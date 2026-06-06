"""
Bite detectors for different fishing methods
"""
import cv2
import numpy as np


class BiteDetector:
    """Base class for bite detection"""
    
    def __init__(self, sensitivity=65):
        self.sensitivity = sensitivity / 100.0
        self.threshold = 100 + (self.sensitivity * 100)
    
    def detect(self, frame):
        """Detect bite in frame"""
        raise NotImplementedError


class BrightnessBiteDetector(BiteDetector):
    """Detects bite based on brightness changes"""
    
    def __init__(self, sensitivity=65):
        super().__init__(sensitivity)
        self.previous_brightness = None
    
    def detect(self, frame):
        """Detect bite using brightness change"""
        if frame is None or frame.size == 0:
            return False
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = gray.mean()
        
        if self.previous_brightness is None:
            self.previous_brightness = mean_brightness
            return False
        
        brightness_change = abs(mean_brightness - self.previous_brightness)
        self.previous_brightness = mean_brightness
        
        return brightness_change > self.threshold * 0.5


class MotionBiteDetector(BiteDetector):
    """Detects bite based on motion"""
    
    def __init__(self, sensitivity=65):
        super().__init__(sensitivity)
        self.previous_frame = None
    
    def detect(self, frame):
        """Detect bite using motion detection"""
        if frame is None or frame.size == 0:
            return False
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if self.previous_frame is None:
            self.previous_frame = gray
            return False
        
        diff = cv2.absdiff(self.previous_frame, gray)
        self.previous_frame = gray
        
        threshold = int(255 * (1 - self.sensitivity))
        _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
        
        motion_pixels = cv2.countNonZero(thresh)
        total_pixels = thresh.shape[0] * thresh.shape[1]
        motion_percentage = (motion_pixels / total_pixels) * 100
        
        return motion_percentage > (10 * self.sensitivity)


class HybridBiteDetector(BiteDetector):
    """Combines multiple detection methods"""
    
    def __init__(self, sensitivity=65):
        super().__init__(sensitivity)
        self.brightness_detector = BrightnessBiteDetector(sensitivity)
        self.motion_detector = MotionBiteDetector(sensitivity)
    
    def detect(self, frame):
        """Detect bite using multiple methods"""
        brightness_detected = self.brightness_detector.detect(frame)
        motion_detected = self.motion_detector.detect(frame)
        
        return brightness_detected and motion_detected
