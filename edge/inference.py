"""
Edge Multi-Model Inference Pipeline
===================================
Manages 3 concurrent YOLO models running in parallel on Edge Transit Nodes:
  1. Traffic / Vehicle Sensing (cars, buses, trucks, motorcycles, bicycles) via traffic.pt
  2. Road Infrastructure Defects (potholes) via pothole.pt
  3. Road / Waterlogging / Hazard Segmentation via yolov8n-seg.pt
  4. Local Edge MAPE-K Dynamic Night Mode Adaptation via CLAHE
  5. Real-time Video HUD Overlay & Annotation
"""

import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional, Tuple
import cv2
import numpy as np

logger = logging.getLogger("EdgeInference")


class EdgeMultiModelEngine:
    def __init__(
        self,
        models_dir: str = "edge/models",
        conf_threshold: float = 0.35,
        device: str = "cpu",
    ):
        self.models_dir = models_dir
        self.conf_threshold = conf_threshold
        self.device = device

        self.traffic_model = None
        self.pothole_model = None
        self.seg_model = None
        self.night_model = None

        from edge.night_enhancer import NightEnhancer
        self.night_enhancer = NightEnhancer()

        # Thread pool for 3-model parallel inference
        self.executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="EdgeYOLO")

        self._load_models()
        self._warmup()

    def _load_models(self):
        try:
            from ultralytics import YOLO
        except ImportError:
            logger.error("[Inference] ultralytics package not found. Please run pip install ultralytics")
            return

        # 1. Traffic / Vehicle Model
        traffic_path = os.path.join(self.models_dir, "traffic.pt")
        if os.path.exists(traffic_path):
            logger.info(f"[Inference] [1/3] Loading Traffic model: {traffic_path}")
            self.traffic_model = YOLO(traffic_path)
        else:
            logger.info("[Inference] [1/3] traffic.pt not found, loading standard yolov8n.pt")
            self.traffic_model = YOLO("yolov8n.pt")

        # 2. Pothole Model
        pothole_path = os.path.join(self.models_dir, "pothole.pt")
        if os.path.exists(pothole_path):
            logger.info(f"[Inference] [2/3] Loading Pothole model: {pothole_path}")
            self.pothole_model = YOLO(pothole_path)
        else:
            logger.warning(f"[Inference] [2/3] pothole.pt not found in {self.models_dir}")

        # 3. Segmentation / Hazard Model
        seg_path = os.path.join(self.models_dir, "yolov8n-seg.pt")
        if not os.path.exists(seg_path):
            seg_path = os.path.join(self.models_dir, "waterlogging.pt")
        if os.path.exists(seg_path):
            logger.info(f"[Inference] [3/3] Loading Segmentation / Hazard model: {seg_path}")
            self.seg_model = YOLO(seg_path)
        else:
            logger.warning(f"[Inference] [3/3] yolov8n-seg.pt not found in {self.models_dir}")

        # 4. Optional dedicated night model
        night_path = os.path.join(self.models_dir, "night_model.pt")
        if os.path.exists(night_path):
            logger.info(f"[Inference] Loading dedicated Night model: {night_path}")
            self.night_model = YOLO(night_path)
        else:
            logger.info("[Inference] Dedicated night model not present — using OpenCV CLAHE dynamic enhancement")

    def _warmup(self):
        """Warm up models with a dummy black image to eliminate cold-start latency."""
        dummy = np.zeros((320, 320, 3), dtype=np.uint8)
        try:
            if self.traffic_model:
                self.traffic_model(dummy, verbose=False)
            if self.pothole_model:
                self.pothole_model(dummy, verbose=False)
            if self.seg_model:
                self.seg_model(dummy, verbose=False)
            logger.info("[Inference] All 3 YOLO models warmed up successfully.")
        except Exception as e:
            logger.warning(f"[Inference] Model warmup notice: {e}")

    def detect_parallel(self, frame: np.ndarray, is_night_mode: bool = False) -> Dict[str, Any]:
        """
        Executes parallel inference across all three models concurrently using ThreadPoolExecutor.
        Returns:
            {
                "vehicles_count": int,
                "vehicle_breakdown": {"cars": X, "bikes": Y, "buses": Z, "trucks": W},
                "vehicle_boxes": [{"class": str, "conf": float, "bbox": [x1, y1, x2, y2]}, ...],
                "defects": [{"type": "pothole", "confidence": float, "bbox": [...]}, ...],
                "defect_names": ["Pothole", ...],
                "seg_boxes": [{"class": str, "conf": float, "bbox": [...]}, ...],
                "was_enhanced": bool,
                "latency_s": float
            }
        """
        start_t = time.time()
        processed_frame = frame
        was_enhanced = False

        if is_night_mode:
            if self.night_model is None:
                processed_frame, was_enhanced, _ = self.night_enhancer.enhance(frame, force=True)

        active_pothole_model = self.night_model if (is_night_mode and self.night_model) else self.pothole_model

        # Submit tasks in parallel
        futures = {}
        if self.traffic_model:
            futures["traffic"] = self.executor.submit(
                self.traffic_model, processed_frame, conf=self.conf_threshold, verbose=False
            )
        if active_pothole_model:
            futures["pothole"] = self.executor.submit(
                active_pothole_model, processed_frame, conf=self.conf_threshold, verbose=False
            )
        if self.seg_model:
            futures["seg"] = self.executor.submit(
                self.seg_model, processed_frame, conf=self.conf_threshold, verbose=False
            )

        # Collect results
        traffic_res = futures["traffic"].result() if "traffic" in futures else []
        pothole_res = futures["pothole"].result() if "pothole" in futures else []
        seg_res = futures["seg"].result() if "seg" in futures else []

        # ── 1. Parse Traffic Results ───────────────────────────────────
        vehicle_boxes = []
        breakdown = {"cars": 0, "bikes": 0, "buses": 0, "trucks": 0}
        vehicle_class_map = {
            "car": "cars",
            "motorcycle": "bikes",
            "bicycle": "bikes",
            "bus": "buses",
            "truck": "trucks",
        }

        for r in traffic_res:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                cls_name = self.traffic_model.names.get(cls_id, "").lower()
                conf = float(box.conf[0])
                if cls_name in vehicle_class_map:
                    category = vehicle_class_map[cls_name]
                    breakdown[category] += 1
                    vehicle_boxes.append({
                        "class": cls_name,
                        "confidence": conf,
                        "bbox": box.xyxy[0].tolist(),
                    })

        total_vehicles = sum(breakdown.values())

        # ── 2. Parse Pothole Results ───────────────────────────────────
        defects = []
        defect_names = []
        for r in pothole_res:
            for box in r.boxes:
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                name = active_pothole_model.names.get(cls_id, "Pothole").capitalize()
                defect_names.append(name)
                defects.append({
                    "type": name.lower(),
                    "confidence": conf,
                    "bbox": box.xyxy[0].tolist(),
                })

        # ── 3. Parse Segmentation Results ──────────────────────────────
        seg_boxes = []
        for r in seg_res:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                cls_name = self.seg_model.names.get(cls_id, "").lower()
                conf = float(box.conf[0])
                # Check for road hazard / waterlogging relevant classes or high confidence objects
                if cls_name in {"puddle", "water", "crack", "hazard", "stop sign", "traffic light", "fire hydrant"}:
                    seg_boxes.append({
                        "class": cls_name,
                        "confidence": conf,
                        "bbox": box.xyxy[0].tolist(),
                    })
                    if cls_name in {"puddle", "water", "hazard"}:
                        defect_names.append(cls_name.capitalize())
                        defects.append({
                            "type": cls_name,
                            "confidence": conf,
                            "bbox": box.xyxy[0].tolist(),
                        })

        latency = time.time() - start_t

        return {
            "vehicles_count": total_vehicles,
            "vehicle_breakdown": breakdown,
            "vehicle_boxes": vehicle_boxes,
            "defects": defects,
            "defect_names": defect_names,
            "seg_boxes": seg_boxes,
            "was_enhanced": was_enhanced,
            "latency_s": latency,
            "processed_frame": processed_frame,
        }

    # Backward compatibility alias
    def detect(self, frame: np.ndarray, is_night_mode: bool = False) -> Dict[str, Any]:
        res = self.detect_parallel(frame, is_night_mode=is_night_mode)
        return {
            "vehicles": res["vehicles_count"],
            "defects": res["defects"],
            "was_enhanced": res["was_enhanced"],
            "details": res,
        }

    def render_hud(
        self,
        frame: np.ndarray,
        results: Dict[str, Any],
        bus_id: str,
        gps: Dict[str, float],
        heading: str,
        fps: float,
        lux: float,
        net_status: str,
        cached_count: int = 0,
    ) -> np.ndarray:
        """
        Overlays multi-model bounding boxes, labels, and top/bottom HUD banners.
        """
        annotated = frame.copy()
        h, w = annotated.shape[:2]

        # 1. Draw Vehicle Bounding Boxes (Cyan / Electric Blue)
        for v in results.get("vehicle_boxes", []):
            x1, y1, x2, y2 = map(int, v["bbox"])
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 200, 0), 2)
            label = f"{v['class']} {v['confidence']:.2f}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(annotated, (x1, max(0, y1 - th - 6)), (x1 + tw + 6, y1), (255, 200, 0), -1)
            cv2.putText(annotated, label, (x1 + 3, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)

        # 2. Draw Pothole / Defect Bounding Boxes (Vivid Red / Orange)
        for d in results.get("defects", []):
            x1, y1, x2, y2 = map(int, d["bbox"])
            # Draw outer glow & main rectangle
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)
            label = f"Pothole {d['confidence']:.2f}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(annotated, (x1, max(0, y1 - th - 8)), (x1 + tw + 8, y1), (0, 0, 255), -1)
            cv2.putText(annotated, label, (x1 + 4, max(14, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # 3. Draw Segmentation / Hazard Boxes (Magenta)
        for s in results.get("seg_boxes", []):
            x1, y1, x2, y2 = map(int, s["bbox"])
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 0, 255), 2)
            label = f"{s['class']} {s['confidence']:.2f}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(annotated, (x1, max(0, y1 - th - 6)), (x1 + tw + 6, y1), (255, 0, 255), -1)
            cv2.putText(annotated, label, (x1 + 3, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

        # 4. Top Acrylic HUD Banner
        overlay = annotated.copy()
        cv2.rectangle(overlay, (0, 0), (w, 36), (10, 15, 26), -1)
        cv2.addWeighted(overlay, 0.82, annotated, 0.18, 0, annotated)

        # Top Banner Text
        top_left = f"SURADAK EDGE: {bus_id.upper()} | FPS: {fps:.1f} | LUX: {lux:.0f} {'(NIGHT)' if results.get('was_enhanced') else '(DAY)'}"
        top_right = f"GPS: ({gps['latitude']:.6f}, {gps['longitude']:.6f}) {heading} | {net_status}"
        cv2.putText(annotated, top_left, (12, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 230, 255), 1)
        
        # Draw top right text right-aligned
        (rw, _), _ = cv2.getTextSize(top_right, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
        net_color = (0, 255, 128) if "ONLINE" in net_status else (0, 100, 255)
        cv2.putText(annotated, top_right, (max(12, w - rw - 14), 23), cv2.FONT_HERSHEY_SIMPLEX, 0.48, net_color, 1)

        # 5. Bottom Acrylic HUD Banner
        overlay_bot = annotated.copy()
        cv2.rectangle(overlay_bot, (0, h - 32), (w, h), (10, 15, 26), -1)
        cv2.addWeighted(overlay_bot, 0.82, annotated, 0.18, 0, annotated)

        # Format Defect Summary Text
        defect_names = results.get("defect_names", [])
        if defect_names:
            defect_summary = f"DEFECTS: {len(defect_names)} found: {defect_names}"
            defect_color = (0, 80, 255)  # Orange/Red
        else:
            defect_summary = "DEFECTS: None"
            defect_color = (180, 180, 180)

        # Format Traffic Summary Text
        total_veh = results.get("vehicles_count", 0)
        bk = results.get("vehicle_breakdown", {})
        active_bk = [f"{v} {k}" for k, v in bk.items() if v > 0]
        bk_str = f" ({', '.join(active_bk)})" if active_bk else ""
        traffic_summary = f"TRAFFIC: {total_veh} vehicles{bk_str}"

        cv2.putText(annotated, defect_summary, (12, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.46, defect_color, 1)
        (tw_traff, _), _ = cv2.getTextSize(traffic_summary, cv2.FONT_HERSHEY_SIMPLEX, 0.46, 1)
        cv2.putText(annotated, traffic_summary, (max(12, w - tw_traff - 14), h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 200, 0), 1)

        return annotated
