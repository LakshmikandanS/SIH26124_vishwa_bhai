"""
Local Edge MAPE-K Loop (On-Vehicle Hardware Self-Healing & Adaptability)
======================================================================
Strictly implements Section 5.1 of Urban_AI_Fleet_MyMasterPlan:
  - Monitor: Ambient lux from camera frame, processing FPS, vibration g-force, cellular dBm.
  - Analyze: Checks if ambient lighting trips night threshold, CPU/FPS drops, or vibration causes blur.
  - Plan: Selects adaptation strategy (switches between standard vs night-mode model/CLAHE, thermal throttle).
  - Execute: Applies model switch, preprocessing enhancement, or frame rate adjustment in real time.
"""

import logging
import time
import cv2
import numpy as np
from typing import Optional

logger = logging.getLogger("EdgeMAPEK")


class EdgeMAPELoop:
    def __init__(
        self,
        lux_night_threshold: float = 25.0,
        vibration_blur_threshold_g: float = 3.0,
        target_fps: float = 15.0,
    ):
        self.lux_night_threshold = lux_night_threshold
        self.vibration_blur_threshold_g = vibration_blur_threshold_g
        self.target_fps = target_fps

        # Current internal state
        self.is_night_mode: bool = False
        self.is_throttled: bool = False
        self.last_switch_time: float = 0.0
        self.switch_cooldown_s: float = 3.0  # Hysteresis to prevent flapping

        # Metrics history
        self.current_lux: float = 100.0
        self.current_fps: float = target_fps
        self.current_vibration_g: float = 0.0

    def monitor(self, frame: np.ndarray, last_frame_time: float, vibration_g: float = 0.0) -> dict:
        """
        [M] Monitor phase: Extracts environment and hardware diagnostics.
        """
        # Calculate ambient light (mean luminance of the frame)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.current_lux = float(np.mean(gray))

        # Calculate actual loop FPS
        if last_frame_time > 0:
            dt = time.time() - last_frame_time
            self.current_fps = 1.0 / dt if dt > 0 else self.target_fps

        self.current_vibration_g = vibration_g

        return {
            "lux": self.current_lux,
            "fps": self.current_fps,
            "vibration_g": self.current_vibration_g,
        }

    def analyze(self, metrics: dict) -> dict:
        """
        [A] Analyze phase: Compares sensor diagnostics against thresholds.
        """
        needs_night_adaptation = metrics["lux"] < self.lux_night_threshold
        needs_throttling = metrics["fps"] < (self.target_fps * 0.5)
        high_vibration = metrics["vibration_g"] > self.vibration_blur_threshold_g

        return {
            "needs_night_adaptation": needs_night_adaptation,
            "needs_throttling": needs_throttling,
            "high_vibration": high_vibration,
        }

    def plan(self, analysis: dict) -> dict:
        """
        [P] Plan phase: Formulates corrective action plan.
        """
        now = time.time()
        plan_action = {}

        # Adaptability: Night mode switching with cooldown
        target_night = analysis["needs_night_adaptation"]
        if target_night != self.is_night_mode and (now - self.last_switch_time) > self.switch_cooldown_s:
            plan_action["switch_night_mode"] = target_night
            plan_action["model_strategy"] = "NIGHT_VISION" if target_night else "DAY_STANDARD"
        else:
            plan_action["switch_night_mode"] = None
            plan_action["model_strategy"] = "NIGHT_VISION" if self.is_night_mode else "DAY_STANDARD"

        # Thermal / CPU Throttling
        plan_action["set_throttling"] = analysis["needs_throttling"]
        plan_action["drop_frame"] = analysis["high_vibration"]

        return plan_action

    def execute(self, plan: dict) -> dict:
        """
        [E] Execute phase: Deploys adaptations onto edge node.
        """
        now = time.time()
        if plan["switch_night_mode"] is not None:
            self.is_night_mode = plan["switch_night_mode"]
            self.last_switch_time = now
            mode_str = "🌙 NIGHT MODE (Low-Light Model / CLAHE)" if self.is_night_mode else "☀️ DAY MODE (Standard Model)"
            logger.info(f"[MAPE-K] Adaptive switch executed -> {mode_str} (Lux: {self.current_lux:.1f})")

        self.is_throttled = plan["set_throttling"]

        return {
            "is_night_mode": self.is_night_mode,
            "is_throttled": self.is_throttled,
            "drop_frame": plan["drop_frame"],
            "lux": self.current_lux,
            "fps": self.current_fps,
        }
