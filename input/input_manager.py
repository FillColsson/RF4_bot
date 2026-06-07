"""
Input manager - unified interface for mouse and keyboard input
"""
import pydirectinput
import time
import random
import threading

pydirectinput.PAUSE = 0


class InputManager:
    """Manages mouse and keyboard input with randomization"""

    def __init__(self):
        self._reel_stop = threading.Event()
        self._reel_thread = None

    def hold_mouse(self, button="left", duration=0.5, delay_min=0.05, delay_max=0.15):
        """Hold mouse button for a duration (cast, hook)."""
        self._random_delay(delay_min, delay_max)
        pydirectinput.mouseDown(button=button)
        time.sleep(max(0.01, duration))
        pydirectinput.mouseUp(button=button)
        self._random_delay(delay_min, delay_max)

    def start_reel(self, button="left"):
        """Start background LMB pulsing for reeling while vision loop runs."""
        self.stop_reel()
        self._reel_stop.clear()
        self._reel_thread = threading.Thread(
            target=self._reel_loop, args=(button,), daemon=True
        )
        self._reel_thread.start()

    def _reel_loop(self, button):
        while not self._reel_stop.is_set():
            pydirectinput.mouseDown(button=button)
            if self._reel_stop.wait(timeout=0.3):
                break
            pydirectinput.mouseUp(button=button)
            time.sleep(0.04)
        pydirectinput.mouseUp(button=button)

    def stop_reel(self):
        """Stop background reeling."""
        self._reel_stop.set()
        if self._reel_thread and self._reel_thread.is_alive():
            self._reel_thread.join(timeout=1.0)
        self._reel_thread = None
        pydirectinput.mouseUp(button="left")

    def click_mouse(self, button="left", delay_min=0.05, delay_max=0.15):
        """Short mouse click (hook set)."""
        self.hold_mouse(
            button=button,
            duration=random.uniform(0.06, 0.12),
            delay_min=delay_min,
            delay_max=delay_max,
        )

    def tap_key(self, key, delay_min=0.05, delay_max=0.15):
        """Single key press (catch screen: space / backspace)."""
        self._random_delay(delay_min, delay_max)
        pydirectinput.press(key)
        self._random_delay(delay_min, delay_max)

    def click(self, x=None, y=None, button="left", delay_min=0.05, delay_max=0.15):
        """Click at optional coordinates."""
        if x is not None and y is not None:
            pydirectinput.moveTo(x, y)
            self._random_delay(delay_min, delay_max)

        pydirectinput.click(button=button)
        self._random_delay(delay_min, delay_max)

    def press(self, key, duration=0.1, delay_min=0.05, delay_max=0.15):
        """Hold keyboard key for a duration."""
        self._random_delay(delay_min, delay_max)
        pydirectinput.keyDown(key)
        time.sleep(max(0.01, duration))
        pydirectinput.keyUp(key)
        self._random_delay(delay_min, delay_max)

    def type_text(self, text, interval=0.05):
        """Type text with interval between characters."""
        pydirectinput.typewrite(text, interval=interval)

    def move_mouse(self, x, y, duration=0.5):
        """Move mouse to coordinates."""
        pydirectinput.moveTo(x, y, duration=duration)

    def get_mouse_position(self):
        """Get current mouse position."""
        return pydirectinput.position()

    @staticmethod
    def _random_delay(delay_min, delay_max):
        """Add random delay."""
        delay = random.uniform(delay_min, delay_max)
        time.sleep(delay)

    @staticmethod
    def sleep(duration):
        """Sleep with slight randomization."""
        random_duration = duration + random.uniform(-0.05, 0.05)
        time.sleep(max(0.01, random_duration))
