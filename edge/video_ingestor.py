"""
RouteSense Urban AI Fleet Intelligence — Video Stream Ingestor
==============================================================
Unified stream ingestor encapsulating OpenCV VideoCapture.
Handles device initialization, frame reading, metadata reporting,
adaptive aspect ratio cropping, format control, and clean teardown.
"""

from pathlib import Path
from typing import Union, Optional, Tuple, Generator
import logging
import cv2
import numpy as np

logger = logging.getLogger("VideoIngestor")


def parse_aspect_ratio(ratio: Optional[Union[float, int, str]]) -> Optional[float]:
    """
    Parse an aspect ratio value which can be a float, int, or string like '16:9', '4:3', '1:1', '9:16'.
    Returns None if 'none', 'original', 'native', or invalid.
    """
    if ratio is None:
        return None
    if isinstance(ratio, (int, float)):
        return float(ratio) if ratio > 0 else None

    s = str(ratio).strip().lower()
    if s in ("none", "original", "native", "auto", "keep", "default", "raw", ""):
        return None

    # Handle formats like "16:9", "16/9", "16x9", "16-9"
    for sep in (":", "/", "x", "-"):
        if sep in s:
            parts = s.split(sep)
            if len(parts) == 2:
                try:
                    w, h = float(parts[0]), float(parts[1])
                    if h > 0:
                        return w / h
                except ValueError:
                    pass

    try:
        val = float(s)
        return val if val > 0 else None
    except ValueError:
        logger.warning("Unrecognized aspect ratio format: '%s'. Keeping original aspect ratio.", ratio)
        return None


class VideoIngestor:
    """
    Unified stream ingestor encapsulating OpenCV VideoCapture.
    Handles device initialization, frame reading, metadata reporting, and clean teardown.
    """

    def __init__(
        self,
        source: Union[int, str, Path],
        loop_video: bool = False,
        target_aspect_ratio: Optional[Union[float, str]] = 16.0 / 9.0,
        crop_anchor: str = "center",
    ) -> None:
        """
        Initialize the video ingestor.

        :param source: Hardware camera index (int or numeric str) or path to video file / stream URL.
        :param loop_video: If True and the source is a file, automatically rewinds to frame 0 upon EOF.
        :param target_aspect_ratio: Target width/height ratio (e.g. 16/9 = ~1.778, '16:9', '4:3', '1:1') for automatic cropping.
        :param crop_anchor: Anchor when cropping video ('center'/'middle' to focus on the middle, 'bottom', 'top', 'left', 'right').
        """
        self.raw_source = source
        self.loop_video = loop_video
        self.target_aspect_ratio = parse_aspect_ratio(target_aspect_ratio)
        self.crop_anchor = str(crop_anchor).strip().lower() if crop_anchor else "center"
        self.is_live = False
        self.source = self._normalize_source(source)

        self._cap: Optional[cv2.VideoCapture] = None
        self._frame_count = 0
        self._fps = 30.0
        self._width = 0
        self._height = 0
        self._orig_width = 0
        self._orig_height = 0

    def _normalize_source(self, source: Union[int, str, Path]) -> Union[int, str]:
        """
        Detect whether the source is a hardware camera index or a file path/stream URL.
        """
        if isinstance(source, int):
            self.is_live = True
            return source

        str_source = str(source).strip()
        # Check if the string represents an integer (e.g., "0", "1")
        if str_source.isdigit():
            self.is_live = True
            return int(str_source)

        # Check for streaming URLs
        if str_source.startswith(("rtsp://", "http://", "https://")):
            self.is_live = True
            return str_source

        # Otherwise it's a file path or URL
        self.is_live = False
        return str_source

    def open(self) -> bool:
        """
        Open the video capture device or file and compute cropped dimensions if aspect ratio adjustment is active.

        :return: True if successfully opened, False otherwise.
        """
        logger.info("Opening video source: %s (is_live=%s)", self.source, self.is_live)
        self._cap = cv2.VideoCapture(self.source)

        if not self._cap.isOpened():
            logger.error("Failed to open video source: %s", self.source)
            return False

        # Query stream properties
        orig_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        reported_fps = self._cap.get(cv2.CAP_PROP_FPS)
        self._fps = reported_fps if reported_fps > 0 else 30.0
        self._frame_count = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))

        self._orig_width = orig_w
        self._orig_height = orig_h

        # Compute output dimensions matching the target aspect ratio
        if self.target_aspect_ratio and orig_h > 0 and orig_w > 0:
            current_aspect = orig_w / orig_h
            if abs(current_aspect - self.target_aspect_ratio) > 0.01:
                if current_aspect < self.target_aspect_ratio:
                    # Video is taller than target (e.g., 4:3, 1:1, or portrait vs 16:9).
                    # Crop height to preserve the specified target aspect ratio.
                    self._height = int(round(orig_w / self.target_aspect_ratio))
                    self._width = orig_w
                else:
                    # Video is wider than target (e.g. 21:9 vs 16:9).
                    self._width = int(round(orig_h * self.target_aspect_ratio))
                    self._height = orig_h
                logger.info(
                    "Adaptive aspect ratio enabled (target=%.2f, anchor=%s): %dx%d -> %dx%d",
                    self.target_aspect_ratio,
                    self.crop_anchor,
                    orig_w,
                    orig_h,
                    self._width,
                    self._height,
                )
            else:
                self._width = orig_w
                self._height = orig_h
        else:
            self._width = orig_w
            self._height = orig_h

        logger.info(
            "Video source opened: Resolution=(%dx%d), FPS=%.2f, TotalFrames=%d",
            self._width,
            self._height,
            self._fps,
            self._frame_count,
        )
        return True

    def _crop_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Crop input frame to match the target aspect ratio.
        If the frame is taller than target, anchors to the specified crop_anchor
        (e.g., 'bottom' so the roadway, potholes, and vehicles are preserved instead of cutting off at the bottom).
        """
        if frame is None or not self.target_aspect_ratio:
            return frame

        h, w = frame.shape[:2]
        if h <= 0 or w <= 0:
            return frame

        current_aspect = w / h
        if abs(current_aspect - self.target_aspect_ratio) <= 0.01:
            return frame

        anchor = self.crop_anchor.strip().lower() if self.crop_anchor else "center"

        if current_aspect < self.target_aspect_ratio:
            # Taller than target aspect ratio (e.g., portrait 9:16, 3:4, or square 1:1 vs 16:9)
            target_h = int(round(w / self.target_aspect_ratio))
            if target_h >= h:
                return frame

            # Middle/center anchor: focus on the middle of the frame (especially in portrait video)
            if anchor in ("center", "middle"):
                start_y = (h - target_h) // 2
                return frame[start_y : start_y + target_h, 0:w]
            elif anchor == "bottom":
                start_y = h - target_h
                return frame[start_y:h, 0:w]
            elif anchor == "top":
                return frame[0:target_h, 0:w]
            else:
                # Default to middle
                start_y = (h - target_h) // 2
                return frame[start_y : start_y + target_h, 0:w]
        else:
            # Wider than target aspect ratio (e.g., ultrawide 21:9 vs 16:9)
            target_w = int(round(h * self.target_aspect_ratio))
            if target_w >= w:
                return frame
            if anchor in ("left", "start"):
                return frame[0:h, 0:target_w]
            elif anchor in ("right", "end"):
                start_x = w - target_w
                return frame[0:h, start_x:w]
            else:
                # Default to center / middle
                start_x = (w - target_w) // 2
                return frame[0:h, start_x : start_x + target_w]

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read the next video frame, automatically cropped to the target aspect ratio.

        :return: Tuple (success, frame). If EOF and loop_video is False, returns (False, None).
        """
        if self._cap is None or not self._cap.isOpened():
            return False, None

        ret, frame = self._cap.read()

        # Handle End-of-File for video files
        if not ret and not self.is_live and self.loop_video:
            logger.info("Video reached EOF. Rewinding to frame 0 (loop enabled).")
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self._cap.read()

        if ret and frame is not None:
            frame = self._crop_frame(frame)

        return ret, frame

    def stream(self) -> Generator[np.ndarray, None, None]:
        """
        Generator that yields frames continuously until EOF or capture termination.
        """
        if self._cap is None and not self.open():
            return

        while True:
            ret, frame = self.read()
            if not ret or frame is None:
                logger.info("Stream ended or frame read failed.")
                break
            yield frame

    @property
    def fps(self) -> float:
        """Return FPS of the stream."""
        return self._fps

    @property
    def dimensions(self) -> Tuple[int, int]:
        """Return (width, height) in pixels after aspect ratio cropping."""
        return self._width, self._height

    @property
    def orig_dimensions(self) -> Tuple[int, int]:
        """Return original uncropped (width, height) in pixels."""
        return self._orig_width, self._orig_height

    @property
    def frame_count(self) -> int:
        """Return total frame count of the stream."""
        return self._frame_count

    @property
    def cap(self) -> Optional[cv2.VideoCapture]:
        """Return underlying OpenCV VideoCapture instance."""
        return self._cap

    @property
    def is_opened(self) -> bool:
        """Return True if video capture is open and active."""
        return self._cap is not None and self._cap.isOpened()

    def release(self) -> None:
        """
        Release hardware camera or video file resources.
        """
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.info("Video capture source released.")

    def __enter__(self) -> "VideoIngestor":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()
