"""
Vision-driven float fishing for RF4.

The bot reacts to what it sees on screen:
  - float landed  -> start waiting for bite
  - bite          -> hook (LMB)
  - catch screen  -> stop reeling, collect (Space/Backspace)
  - screen closed -> next cast
"""
import random
import time

from core.fishing_mode import FishingMode
from core.state_machine import FishingState
from vision.float_detectors import HybridFloatDetector
from vision.game_state import GameStateAnalyzer, GamePhase


class FloatFishing(FishingMode):
    """Float fishing controlled by computer vision."""

    CAST_HOLD_MIN = 0.15
    CAST_HOLD_MAX = 2.5
    HOOK_HOLD = 0.1

    def __init__(self, config, vision_engine, input_manager):
        super().__init__(config, vision_engine, input_manager)

        self.cast_count = 0
        self.catch_count = 0
        self.float_detector = None
        self.game_state = None
        self.last_analysis = None

        self._float_landed = False
        self._bite_detected = False
        self._catch_detected = False
        self._collect_sent = False
        self._catch_gone = False

        self._setup_state_transitions()

    def _vision_cfg(self, key, default):
        return self.config.get("vision", {}).get(key, default)

    def _setup_state_transitions(self):
        self.state_machine.add_transition(
            FishingState.IDLE, FishingState.CASTING,
            lambda: self.running,
            self._start_cast,
        )

        self.state_machine.add_transition(
            FishingState.CASTING, FishingState.WAITING,
            lambda: self._float_landed or self._cast_timed_out(),
            self._on_float_landed,
        )

        self.state_machine.add_transition(
            FishingState.WAITING, FishingState.HOOKED,
            lambda: self._bite_detected and self.config.get("auto_hook", True),
            self._hook_fish,
        )

        self.state_machine.add_transition(
            FishingState.WAITING, FishingState.IDLE,
            lambda: self._wait_timed_out(),
            self._on_wait_timeout,
        )

        self.state_machine.add_transition(
            FishingState.HOOKED, FishingState.FIGHTING,
            lambda: self.state_machine.get_state_duration() > 0.15,
            self._start_fighting,
        )

        self.state_machine.add_transition(
            FishingState.FIGHTING, FishingState.COLLECTING,
            lambda: self._catch_detected or self._fight_timed_out(),
            self._on_catch_screen,
        )

        self.state_machine.add_transition(
            FishingState.COLLECTING, FishingState.IDLE,
            lambda: self._catch_gone or self._collect_timed_out(),
            self._finish_collection,
        )

    def _cast_timed_out(self):
        return self.state_machine.get_state_duration() > self._vision_cfg("max_cast_wait_sec", 20)

    def _wait_timed_out(self):
        return self.state_machine.get_state_duration() > self._vision_cfg("max_wait_sec", 300)

    def _fight_timed_out(self):
        return self.state_machine.get_state_duration() > self._vision_cfg("max_fight_sec", 120)

    def _collect_timed_out(self):
        return self._collect_sent and self.state_machine.get_state_duration() > 8

    def _cast_hold_duration(self):
        cast_power = self.config.get("cast_power", 75)
        hold_min = self.config.get("cast_hold_min", self.CAST_HOLD_MIN)
        hold_max = self.config.get("cast_hold_max", self.CAST_HOLD_MAX)
        ratio = max(0.0, min(100.0, cast_power)) / 100.0
        return hold_min + ratio * (hold_max - hold_min)

    def _create_float_detector(self):
        detection_method = self.config.get("float_detection_method", "hybrid")
        float_color = self.config.get("float_color", "red")

        if detection_method == "template_matching":
            try:
                from vision.advanced_detectors import TemplateMatchingFloatDetector
                template_path = self.config.get("advanced_settings", {}).get("template_path")
                if template_path:
                    return TemplateMatchingFloatDetector(template_path)
            except Exception as e:
                self.logger.error(f"Template Matching failed: {e}")

        return HybridFloatDetector(target_color=float_color)

    def setup(self):
        self.logger.info("Vision-driven float fishing setup")

        self.float_detector = self._create_float_detector()
        self.game_state = GameStateAnalyzer(self.config, self.float_detector)
        self.game_state.reload_profile()

        self.cast_count = 0
        self.catch_count = 0
        self._reset_vision_flags()
        self.state_machine.set_state(FishingState.IDLE)

        self.logger.info("Waiting for visual events (bite / catch screen)")

    def _reset_vision_flags(self):
        self._float_landed = False
        self._bite_detected = False
        self._catch_detected = False
        self._collect_sent = False
        self._catch_gone = False

    def execute_cycle(self):
        if self.game_state is None:
            return

        frame = self.vision.capture_screen()
        if frame is None:
            return

        region = self.config.get("detection_region", {})
        roi = self.vision.crop_region(frame, region)
        self.last_analysis = self.game_state.analyze(frame, roi)

        state = self.state_machine.get_current_state()
        phase = self.last_analysis.phase

        if state == FishingState.CASTING:
            if phase in (GamePhase.FLOAT_CALM, GamePhase.BITE):
                self._float_landed = True
                self.logger.info("Vision: float detected in water")

        elif state == FishingState.WAITING:
            if self.last_analysis.bite:
                self._bite_detected = True
                self.logger.info(
                    f"Vision: BITE ({self.last_analysis.bite_confidence:.0%}) "
                    f"methods={self.last_analysis.bite_methods}"
                )

        elif state == FishingState.FIGHTING:
            if self.last_analysis.catch_screen:
                self._catch_detected = True
                self.logger.info(
                    f"Vision: catch screen ({self.last_analysis.catch_confidence:.0%})"
                )

        elif state == FishingState.COLLECTING:
            if self._collect_sent and not self.last_analysis.catch_screen:
                self._catch_gone = True
                self.logger.info("Vision: catch screen closed")

    def _start_cast(self):
        self.game_state.reset_for_new_cast()
        self._reset_vision_flags()

        hold = self._cast_hold_duration()
        self.logger.info(
            f"Cast #{self.cast_count + 1}: LMB {hold:.2f}s "
            f"({self.config.get('cast_power', 75)}%)"
        )
        self.input.hold_mouse("left", hold)
        self.cast_count += 1
        self.logger.info("Vision: waiting for float to appear...")

    def _on_float_landed(self):
        if self._float_landed:
            self.logger.info("Float ready — watching for bite")
        else:
            self.logger.warning("Float not seen — waiting anyway (cast timeout)")

    def _hook_fish(self):
        self.logger.info("Hooking (LMB) — vision confirmed bite")
        self._bite_detected = False
        self.game_state.mark_hooked()
        self.input.hold_mouse("left", self.HOOK_HOLD)

    def _start_fighting(self):
        self.logger.info("Fighting — reeling until catch screen appears")
        self.input.start_reel()

    def _on_catch_screen(self):
        self.input.stop_reel()

        if self._catch_detected:
            self.catch_count += 1
            self.input.sleep(random.uniform(0.3, 0.6))

            if self.config.get("auto_collect", True):
                self.logger.info("Collecting fish (Space)")
                self.input.tap_key("space")
            else:
                self.logger.info("Releasing fish (Backspace)")
                self.input.tap_key("backspace")

            self._collect_sent = True
            self.game_state.mark_unhooked()
        else:
            self.logger.warning("Fight timeout — no catch screen, resetting")
            self.game_state.mark_unhooked()
            self._catch_gone = True

    def _on_wait_timeout(self):
        self.logger.warning("No bite for too long — recasting")

    def _finish_collection(self):
        self.logger.info(f"Cycle done. Casts: {self.cast_count}, catches: {self.catch_count}")
        self.game_state.reset_for_new_cast()
        self._reset_vision_flags()
        self.input.sleep(random.uniform(0.5, 1.0))

    def cleanup(self):
        self.input.stop_reel()
        self.logger.info(
            f"Stopped. Casts: {self.cast_count}, catches: {self.catch_count}"
        )

    def get_status(self):
        status = super().get_status()
        if self.last_analysis:
            status["vision_phase"] = self.last_analysis.phase.value
            status["catch_confidence"] = round(self.last_analysis.catch_confidence, 2)
        status["catches"] = self.catch_count
        return status
