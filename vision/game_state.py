"""
Vision-driven game state analysis for RF4 float fishing.
"""
import json
import os
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum

from vision.catch_screen_detector import CatchScreenDetector
from vision.float_detectors import HybridFloatDetector


class GamePhase(Enum):
    UNKNOWN = "unknown"
    NO_FLOAT = "no_float"
    FLOAT_CALM = "float_calm"
    BITE = "bite"
    FIGHTING = "fighting"
    CATCH_SCREEN = "catch_screen"


@dataclass
class FrameAnalysis:
    phase: GamePhase = GamePhase.UNKNOWN
    float_visible: bool = False
    float_info: dict = None
    bite: bool = False
    bite_confidence: float = 0.0
    bite_methods: list = field(default_factory=list)
    catch_screen: bool = False
    catch_confidence: float = 0.0
    float_stable_frames: int = 0
    float_missing_frames: int = 0
    timestamp: float = 0.0


class GameStateAnalyzer:
    """Reads the screen and infers what is happening in the game."""

    PROFILE_FILE = "vision_profile.json"

    def __init__(self, config, float_detector=None):
        self.config = config
        self.profile = self._load_profile()

        float_color = config.get("float_color", "red")
        self.float_detector = float_detector or HybridFloatDetector(target_color=float_color)
        self.catch_detector = CatchScreenDetector(config, self.profile)

        self._float_stable_count = 0
        self._float_missing_count = 0
        self._bite_cooldown_until = 0.0
        self._hooked = False

        vision = config.get("vision", {})
        self.stable_frames_required = vision.get("float_stable_frames", 5)
        self.missing_frames_for_fight = vision.get("float_missing_frames_for_fight", 4)
        self.bite_cooldown = vision.get("bite_cooldown_sec", 2.0)

    def _load_profile(self):
        if os.path.exists(self.PROFILE_FILE):
            try:
                with open(self.PROFILE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def reload_profile(self):
        self.profile = self._load_profile()
        self.catch_detector = CatchScreenDetector(self.config, self.profile)

    def reset_for_new_cast(self):
        self._float_stable_count = 0
        self._float_missing_count = 0
        self._hooked = False
        self._bite_cooldown_until = 0.0
        self.float_detector.color_detector.float_position_history.clear()
        self.float_detector.motion_detector.prev_gray = None
        self.float_detector.area_detector.prev_area = None

    def mark_hooked(self):
        self._hooked = True
        self._float_missing_count = 0

    def mark_unhooked(self):
        self._hooked = False

    def analyze(self, frame, float_roi=None):
        result = FrameAnalysis(timestamp=time.time())

        if frame is None:
            return result

        catch = self.catch_detector.detect(frame)
        result.catch_screen = catch["detected"]
        result.catch_confidence = catch["confidence"]

        if result.catch_screen:
            result.phase = GamePhase.CATCH_SCREEN
            return result

        if float_roi is None or float_roi.size == 0:
            result.phase = GamePhase.NO_FLOAT
            return result

        float_info = self.float_detector.detect_float(float_roi)
        result.float_info = float_info
        result.float_visible = float_info is not None

        if result.float_visible:
            self._float_stable_count += 1
            self._float_missing_count = 0
        else:
            self._float_missing_count += 1
            self._float_stable_count = 0

        result.float_stable_frames = self._float_stable_count
        result.float_missing_frames = self._float_missing_count

        sensitivity = self.config.get("bite_detection_sensitivity", 65) / 100.0
        bite = self.float_detector.detect_bite(float_roi, sensitivity=sensitivity)
        result.bite = bite.get("detected", False)
        result.bite_confidence = bite.get("confidence", 0.0)
        result.bite_methods = bite.get("methods", [])

        now = time.time()
        if result.bite and now < self._bite_cooldown_until:
            result.bite = False

        if result.bite:
            result.phase = GamePhase.BITE
            self._bite_cooldown_until = now + self.bite_cooldown
            return result

        if self._hooked and self._float_missing_count >= self.missing_frames_for_fight:
            result.phase = GamePhase.FIGHTING
            return result

        if self._float_stable_count >= self.stable_frames_required:
            result.phase = GamePhase.FLOAT_CALM
            return result

        if not result.float_visible:
            result.phase = GamePhase.NO_FLOAT
        else:
            result.phase = GamePhase.FLOAT_CALM

        return result
