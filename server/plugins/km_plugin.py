"""
Server-Side K-M (Knowledge-Media) Plugin
========================================
Implements Section 1, 2.5, and 3.2 of Master Plan:
  - Adaptive Query Pipeline
  - When an unverified defect is detected, fires MediaSyncRequest back to explicit vehicle ID
  - Avoids continuous high-definition video streaming to the cloud
"""

import logging
from typing import Optional, Callable
from domain.models import DefectMarker

logger = logging.getLogger("KMPlugin")

MEDIA_REQUEST_CONFIDENCE_THRESHOLD = 0.70


class KnowledgeMediaPlugin:
    def __init__(self, command_sender: Optional[Callable] = None):
        self._command_sender = command_sender
        logger.info("[K-M] Knowledge-Media Adaptive Query plugin initialized")

    def set_command_sender(self, sender: Callable):
        self._command_sender = sender

    def request_media_sync(self, bus_id: str, defect_id: str, timestamp_ms: int, clip_duration: int = 2):
        """Dispatches an outbound command to vehicle requesting a localized 2s video clip."""
        logger.info(
            f"[K-M] 🎯 Adaptive trigger: Requesting {clip_duration}s video clip "
            f"from {bus_id} for defect {defect_id[:8]}.. at ts={timestamp_ms}"
        )
        if self._command_sender:
            try:
                self._command_sender(
                    bus_id=bus_id,
                    defect_id=defect_id,
                    timestamp_ms=timestamp_ms,
                    clip_duration=clip_duration,
                )
            except Exception as e:
                logger.error(f"[K-M] Failed to send media sync request: {e}")
        else:
            logger.warning("[K-M] Command sender not wired.")

    def evaluate_and_request_clip(self, marker: DefectMarker, bus_id: str):
        if marker.confidence >= MEDIA_REQUEST_CONFIDENCE_THRESHOLD:
            self.request_media_sync(
                bus_id=bus_id,
                defect_id=marker.defect_id,
                timestamp_ms=marker.last_seen_ms,
            )
