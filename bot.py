"""
Main bot logic for RF4_Bot - Float fishing automation
"""
import threading
import time
import random
import cv2
import pydirectinput
from vision import VisionEngine


class RF4Bot:
    def __init__(self, config, gui):
        self.config = config
        self.gui = gui
        self.vision = VisionEngine(config)
        self.running = False
        self.thread = None
    
    def update_config(self, config):
        """Update bot configuration"""
        self.config = config
    
    def start(self):
        """Start the bot"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self.gui.update_status("🎣 Бот работает...", "#00FF00")
    
    def stop(self):
        """Stop the bot"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _run(self):
        """Main bot loop"""
        try:
            while self.running:
                # Capture screenshot
                frame = self.vision.capture_screen()
                
                if frame is not None:
                    # Process frame for float detection
                    self._process_frame(frame)
                
                # Sleep to avoid high CPU usage
                time.sleep(0.05)
        
        except Exception as e:
            print(f"Error in bot loop: {e}")
            self.gui.update_status(f"❌ Ошибка: {str(e)}", "#FF5555")
        
        finally:
            self.running = False
    
    def _process_frame(self, frame):
        """
        Process captured frame for float detection
        
        Args:
            frame (numpy.ndarray): Frame from vision module
        """
        # Detect features in float region
        region = self.config.get("detection_region", {})
        x = region.get("x", 850)
        y = region.get("y", 350)
        w = region.get("width", 450)
        h = region.get("height", 380)
        
        # Crop detection region
        roi = frame[y:y+h, x:x+w]
        
        # Detect float using brightness/color analysis
        if self._detect_bite(roi):
            self._perform_hook()
    
    def _detect_bite(self, roi):
        """
        Detect bite using image analysis
        
        Args:
            roi (numpy.ndarray): Region of interest
        
        Returns:
            bool: True if bite detected
        """
        if roi is None or roi.size == 0:
            return False
        
        # Simple brightness-based detection
        # Could be improved with ML model
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        mean_brightness = gray.mean()
        
        sensitivity = self.config.get("bite_detection_sensitivity", 65) / 100.0
        threshold = 100 + (sensitivity * 100)
        
        return mean_brightness > threshold
    
    def _perform_hook(self):
        """Perform hooking action"""
        if self.config.get("auto_hook", True):
            # Simulate mouse click for hook
            pydirectinput.press('space')
            time.sleep(0.1)
            pydirectinput.release('space')
