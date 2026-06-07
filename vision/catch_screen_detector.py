"""
Catch screen detector for RF4 — modal with fish after successful catch.
"""
import os
import json
import cv2
import numpy as np


class CatchScreenDetector:
    """Detects the post-catch UI (fish reward screen)."""

    def __init__(self, config=None, profile=None):
        config = config or {}
        profile = profile or {}
        vision = config.get("vision", {})

        self.region = vision.get("catch_screen_region") or profile.get("catch_screen_region")
        self.threshold = vision.get(
            "catch_screen_threshold",
            profile.get("catch_screen_threshold", 0.55),
        )
        self.edge_ratio_threshold = vision.get(
            "catch_edge_ratio",
            profile.get("catch_edge_ratio", 0.82),
        )

        samples_dir = vision.get("catch_samples_dir", "catch_samples")
        self.templates = self._load_templates(samples_dir)
        self.profile_stats = profile.get("catch_screen_stats")

    def _load_templates(self, samples_dir):
        templates = []
        if not os.path.isdir(samples_dir):
            return templates

        for name in sorted(os.listdir(samples_dir)):
            if not name.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            path = os.path.join(samples_dir, name)
            img = cv2.imread(path)
            if img is not None:
                templates.append((name, img))

        return templates

    def _crop(self, frame):
        if self.region:
            x = self.region.get("x", 0)
            y = self.region.get("y", 0)
            w = self.region.get("width", frame.shape[1])
            h = self.region.get("height", frame.shape[0])
            return frame[y:y + h, x:x + w]
        return frame

    def _score_vignette(self, gray):
        """Catch overlay darkens screen edges relative to center."""
        h, w = gray.shape
        margin_x = max(1, w // 8)
        margin_y = max(1, h // 8)

        center = gray[h // 4:3 * h // 4, w // 4:3 * w // 4]
        if center.size == 0:
            return 0.0

        center_mean = float(center.mean())
        corners = [
            gray[:margin_y, :margin_x],
            gray[:margin_y, -margin_x:],
            gray[-margin_y:, :margin_x],
            gray[-margin_y:, -margin_x:],
        ]
        edge_mean = float(np.mean([c.mean() for c in corners if c.size]))

        if center_mean < 20:
            return 0.0

        ratio = edge_mean / center_mean
        if ratio < self.edge_ratio_threshold:
            strength = min(1.0, (self.edge_ratio_threshold - ratio) / 0.25)
            return strength
        return 0.0

    def _score_panel(self, frame):
        """Central UI panel is high-contrast and saturated."""
        h, w = frame.shape[:2]
        panel = frame[int(h * 0.15):int(h * 0.85), int(w * 0.2):int(w * 0.8)]
        if panel.size == 0:
            return 0.0

        gray = cv2.cvtColor(panel, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = edges.mean() / 255.0

        hsv = cv2.cvtColor(panel, cv2.COLOR_BGR2HSV)
        sat_mean = hsv[:, :, 1].mean() / 255.0

        score = edge_density * 0.6 + sat_mean * 0.4
        return min(1.0, score)

    def _score_templates(self, frame):
        if not self.templates:
            return 0.0

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        best = 0.0

        for _, template in self.templates:
            tpl_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            if gray.shape[0] < tpl_gray.shape[0] or gray.shape[1] < tpl_gray.shape[1]:
                scale = min(gray.shape[0] / tpl_gray.shape[0], gray.shape[1] / tpl_gray.shape[1])
                scale = min(1.0, scale * 0.95)
                tpl_gray = cv2.resize(
                    tpl_gray,
                    (max(1, int(tpl_gray.shape[1] * scale)), max(1, int(tpl_gray.shape[0] * scale))),
                )

            if gray.shape[0] < tpl_gray.shape[0] or gray.shape[1] < tpl_gray.shape[1]:
                continue

            result = cv2.matchTemplate(gray, tpl_gray, cv2.TM_CCOEFF_NORMED)
            best = max(best, float(result.max()))

        return best

    def _score_profile(self, frame):
        if not self.profile_stats:
            return 0.0

        roi = self._crop(frame)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        features = np.array([
            hsv[:, :, 0].mean(),
            hsv[:, :, 1].mean(),
            hsv[:, :, 2].mean(),
            cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY).mean(),
        ])

        ref = np.array(self.profile_stats.get("mean", features))
        std = np.array(self.profile_stats.get("std", [10, 10, 10, 10]))
        std = np.maximum(std, 1.0)

        z = np.abs(features - ref) / std
        distance = z.mean()
        return max(0.0, min(1.0, 1.0 - distance / 4.0))

    def detect(self, frame):
        if frame is None or frame.size == 0:
            return {"detected": False, "confidence": 0.0, "methods": []}

        roi = self._crop(frame)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        methods = {}
        methods["vignette"] = self._score_vignette(gray)
        methods["panel"] = self._score_panel(roi)
        methods["template"] = self._score_templates(roi)
        methods["profile"] = self._score_profile(frame)

        weights = {"vignette": 0.35, "panel": 0.25, "template": 0.25, "profile": 0.15}
        active = {k: v for k, v in methods.items() if v > 0.05}
        if not active:
            confidence = 0.0
        else:
            total_w = sum(weights[k] for k in active)
            confidence = sum(methods[k] * weights[k] for k in active) / total_w

        triggered = [k for k, v in methods.items() if v >= 0.4]
        detected = confidence >= self.threshold or len(triggered) >= 2

        return {
            "detected": detected,
            "confidence": confidence,
            "methods": triggered,
            "scores": methods,
        }
