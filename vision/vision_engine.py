"""
Enhanced Computer Vision Engine with float detection
"""
import cv2
import numpy as np
import mss
from vision.detectors import HybridBiteDetector


class VisionEngine:
    """Main vision processing engine"""
    
    def __init__(self, config):
        self.config = config
        self.sct = mss.mss()
        self.bite_detector = None
        self.setup_detector(config.get("detector_type", "hybrid"))
    
    def setup_detector(self, detector_type="hybrid"):
        """Setup bite detector"""
        sensitivity = self.config.get("bite_detection_sensitivity", 65)
        self.bite_detector = HybridBiteDetector(sensitivity)
    
    def capture_screen(self, monitor=1):
        """Capture screenshot of specified monitor"""
        try:
            monitors = self.sct.monitors
            if monitor > len(monitors) - 1:
                monitor = 1
            
            screenshot_data = self.sct.grab(monitors[monitor])
            frame = np.array(screenshot_data)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            return frame
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None
    
    def crop_region(self, frame, region):
        """Crop region from frame"""
        if frame is None:
            return None
        
        x = region.get("x", 0)
        y = region.get("y", 0)
        w = region.get("width", frame.shape[1])
        h = region.get("height", frame.shape[0])
        
        # Validate bounds
        h_max = frame.shape[0]
        w_max = frame.shape[1]
        
        y = max(0, min(y, h_max))
        x = max(0, min(x, w_max))
        
        y_end = min(y + h, h_max)
        x_end = min(x + w, w_max)
        
        return frame[y:y_end, x:x_end]
    
    def detect_bite(self, frame):
        """Detect bite in frame"""
        if self.bite_detector is None:
            return False
        
        return self.bite_detector.detect(frame)
    
    def detect_features(self, frame, method="sift"):
        """Detect features in frame"""
        if frame is None:
            return None, None
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if method == "sift":
            detector = cv2.SIFT_create()
        elif method == "orb":
            detector = cv2.ORB_create()
        elif method == "akaze":
            detector = cv2.AKAZE_create()
        else:
            return None, None
        
        keypoints, descriptors = detector.detectAndCompute(gray, None)
        return keypoints, descriptors
    
    def match_template(self, frame, template, threshold=0.7):
        """Find template in frame"""
        if frame is None or template is None:
            return []
        
        if frame.shape[0] < template.shape[0] or frame.shape[1] < template.shape[1]:
            return []
        
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        result = cv2.matchTemplate(gray_frame, gray_template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        
        matches = []
        for loc in zip(*locations[::-1]):
            matches.append(loc)
        
        return matches

