"""
Input manager - unified interface for mouse and keyboard input
"""
import pydirectinput
import time
import random


class InputManager:
    """Manages mouse and keyboard input with randomization"""
    
    def __init__(self, use_pydirectinput=False):
        self.use_pydirectinput = use_pydirectinput
    
    def click(self, x=None, y=None, button="left", delay_min=0.05, delay_max=0.15):
        """
        Perform mouse click with randomized delay
        
        Args:
            x, y: coordinates (if None, clicks at current position)
            button: "left", "right", "middle"
            delay_min, delay_max: random delay range in seconds
        """
        if x is not None and y is not None:
            pydirectinput.moveTo(x, y)
            self._random_delay(delay_min, delay_max)
        
        pydirectinput.click(button=button)
        self._random_delay(delay_min, delay_max)
    
    def press(self, key, duration=0.1, delay_min=0.05, delay_max=0.15):
        """
        Press a key for specified duration
        
        Args:
            key: key name (e.g., 'space', 'w', 'shift')
            duration: how long to hold the key
            delay_min, delay_max: random delay before press
        """
        self._random_delay(delay_min, delay_max)
        pydirectinput.press(key)
        time.sleep(duration)
    
    def type_text(self, text, interval=0.05):
        """Type text with interval between characters"""
        pydirectinput.typewrite(text, interval=interval)
    
    def move_mouse(self, x, y, duration=0.5):
        """Move mouse to coordinates"""
        pydirectinput.moveTo(x, y, duration=duration)
    
    def get_mouse_position(self):
        """Get current mouse position"""
        return pydirectinput.position()
    
    @staticmethod
    def _random_delay(delay_min, delay_max):
        """Add random delay"""
        delay = random.uniform(delay_min, delay_max)
        time.sleep(delay)
    
    @staticmethod
    def sleep(duration):
        """Sleep with slight randomization"""
        random_duration = duration + random.uniform(-0.05, 0.05)
        time.sleep(max(0.01, random_duration))
