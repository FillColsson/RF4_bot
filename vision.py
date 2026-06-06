"""
Computer vision module for RF4_Bot
Uses OpenCV and MSS for screen capture and image processing
"""
import cv2
import numpy as np
import mss


class VisionEngine:
    def __init__(self, config):
        self.config = config
        self.sct = mss.mss()
    
    def capture_screen(self, monitor=1):
        """
        Capture screenshot of specified monitor
        
        Args:
            monitor (int): Monitor number (1 for primary)
        
        Returns:
            numpy.ndarray: Screenshot in BGR format
        """
        try:
            # Get monitor info
            monitors = self.sct.monitors
            if monitor > len(monitors) - 1:
                monitor = 1
            
            # Capture screenshot
            screenshot_data = self.sct.grab(monitors[monitor])
            frame = np.array(screenshot_data)
            # Convert BGRA to BGR
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            return frame
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None
    
    def detect_features(self, frame, method="sift"):
        """
        Detect features in frame using specified method
        
        Args:
            frame (numpy.ndarray): Input image
            method (str): Detection method ('sift', 'orb', 'akaze')
        
        Returns:
            tuple: Keypoints and descriptors
        """
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
        """
        Find template in frame
        
        Args:
            frame (numpy.ndarray): Search frame
            template (numpy.ndarray): Template to find
            threshold (float): Matching threshold (0-1)
        
        Returns:
            list: List of matching locations
        """
        if frame is None or template is None:
            return []
        
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        result = cv2.matchTemplate(gray_frame, gray_template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        
        matches = []
        for loc in zip(*locations[::-1]):
            matches.append(loc)
        
        return matches
    
    def draw_boxes(self, frame, locations, size, color=(0, 255, 0), thickness=2):
        """
        Draw bounding boxes on frame
        
        Args:
            frame (numpy.ndarray): Input frame
            locations (list): List of (x, y) locations
            size (tuple): Template size (width, height)
            color (tuple): BGR color
            thickness (int): Line thickness
        
        Returns:
            numpy.ndarray: Frame with boxes drawn
        """
        result = frame.copy()
        w, h = size
        
        for x, y in locations:
            cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
        
        return result
