"""
Nighttime and low-light road dashcam enhancement module.
Uses CLAHE (Contrast Limited Adaptive Histogram Equalization) on the L-channel of LAB space.
Extremely fast (<2ms on CPU) - ideal for edge devices without GPU overhead.
"""

import cv2
import numpy as np


class NightEnhancer:
    def __init__(self, clip_limit: float = 3.0, tile_grid_size: tuple = (8, 8), dark_threshold: float = 85.0):
        """
        :param clip_limit: Threshold for contrast limiting in CLAHE
        :param tile_grid_size: Size of grid for histogram equalization (default 8x8)
        :param dark_threshold: Mean luminance threshold below which night mode auto-activates
        """
        self.clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        self.dark_threshold = dark_threshold

    def is_low_light(self, frame: np.ndarray) -> tuple[bool, float]:
        """Calculates frame mean luminance to detect night/dark conditions."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = float(np.mean(gray))
        return (mean_brightness < self.dark_threshold), mean_brightness

    def enhance(self, frame: np.ndarray, force: bool = False) -> tuple[np.ndarray, bool, float]:
        """
        Enhances low-light / nighttime road frame.
        :param frame: Standard BGR OpenCV image
        :param force: If True, always apply enhancement regardless of brightness
        :return: (enhanced_frame, was_enhanced, mean_brightness)
        """
        is_dark, brightness = self.is_low_light(frame)

        if not (is_dark or force):
            return frame, False, brightness

        # Convert to LAB color space to isolate luminance from color
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        # Apply CLAHE to the L channel
        cl = self.clahe.apply(l_channel)

        # Merge channels back
        merged = cv2.merge((cl, a_channel, b_channel))
        enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

        return enhanced, True, brightness
