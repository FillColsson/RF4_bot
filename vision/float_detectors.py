"""
Advanced float detectors for RF4 fishing
Specialized detection methods for bobber/float fishing
"""
import cv2
import numpy as np
from collections import deque


class FloatDetector:
    """Base class for float detection"""
    
    def __init__(self, roi_size=(100, 100)):
        self.roi_size = roi_size
        self.prev_frames = deque(maxlen=10)
        self.float_position_history = deque(maxlen=30)
    
    def detect_float(self, frame):
        """Detect float in frame"""
        raise NotImplementedError
    
    def detect_bite(self, frame):
        """Detect bite based on float movement"""
        raise NotImplementedError


class ColorBasedFloatDetector(FloatDetector):
    """Detects float based on specific color range"""
    
    def __init__(self, target_color="red"):
        super().__init__()
        self.target_color = target_color
        self.color_ranges = {
            "red": {
                "lower": np.array([0, 100, 100]),
                "upper": np.array([10, 255, 255])
            },
            "orange": {
                "lower": np.array([5, 100, 100]),
                "upper": np.array([25, 255, 255])
            },
            "yellow": {
                "lower": np.array([20, 100, 100]),
                "upper": np.array([40, 255, 255])
            },
            "green": {
                "lower": np.array([35, 100, 100]),
                "upper": np.array([85, 255, 255])
            }
        }
    
    def detect_float(self, frame):
        """
        Detect float using color detection
        
        Returns:
            dict: {'position': (x, y), 'area': float_area, 'confidence': 0-1}
        """
        if frame is None or frame.size == 0:
            return None
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        if self.target_color not in self.color_ranges:
            return None
        
        color_range = self.color_ranges[self.target_color]
        mask = cv2.inRange(hsv, color_range["lower"], color_range["upper"])
        
        # Морфологические операции
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Найти контуры
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Найти наибольший контур (вероятно поплавок)
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        
        if area < 50:  # Слишком маленький
            return None
        
        # Найти центр и окружность
        (x, y), radius = cv2.minEnclosingCircle(largest_contour)
        
        return {
            'position': (int(x), int(y)),
            'area': float(area),
            'radius': float(radius),
            'contour': largest_contour,
            'confidence': min(1.0, area / 1000.0)
        }
    
    def detect_bite(self, frame):
        """
        Detect bite based on float position changes
        
        Returns:
            bool: True if bite detected
        """
        float_info = self.detect_float(frame)
        
        if float_info is None:
            return False
        
        pos = float_info['position']
        self.float_position_history.append(pos)
        
        if len(self.float_position_history) < 5:
            return False
        
        # Анализируем последние позиции
        positions = list(self.float_position_history)
        
        # Вычисляем среднее смещение
        distances = []
        for i in range(1, len(positions)):
            dist = np.sqrt((positions[i][0] - positions[i-1][0])**2 + 
                          (positions[i][1] - positions[i-1][1])**2)
            distances.append(dist)
        
        if not distances:
            return False
        
        avg_distance = np.mean(distances)
        
        # Если есть резкое движение - это поклёвка
        recent_distances = distances[-3:]
        max_recent = max(recent_distances) if recent_distances else 0
        
        # Порог обнаружения: большое смещение (>5 пиксей)
        return max_recent > 5.0 and avg_distance > 2.0


class MotionBasedFloatDetector(FloatDetector):
    """Detects float using optical flow / motion"""
    
    def __init__(self):
        super().__init__()
        self.prev_gray = None
    
    def detect_bite(self, frame):
        """
        Detect bite using optical flow
        
        Returns:
            bool: True if significant motion detected
        """
        if frame is None:
            return False
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if self.prev_gray is None:
            self.prev_gray = gray
            return False
        
        # Вычисляем оптический поток
        flow = cv2.calcOpticalFlowFarneback(
            self.prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
        )
        
        self.prev_gray = gray
        
        # Вычисляем магнитуду движения
        magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        motion_intensity = magnitude.mean()
        
        # Поклёвка - это значительное движение
        return motion_intensity > 0.5


class AreaBasedFloatDetector(FloatDetector):
    """Detects bite based on float area changes"""
    
    def __init__(self, threshold=0.15):
        super().__init__()
        self.prev_area = None
        self.threshold = threshold  # 15% изменения площади
    
    def detect_float(self, frame, color_detector=None):
        """Detect float (uses ColorBasedFloatDetector)"""
        if color_detector:
            return color_detector.detect_float(frame)
        return None
    
    def detect_bite(self, frame, color_detector):
        """
        Detect bite based on float area changes
        
        Returns:
            bool: True if float area changed significantly
        """
        float_info = color_detector.detect_float(frame)
        
        if float_info is None or 'area' not in float_info:
            return False
        
        current_area = float_info['area']
        
        if self.prev_area is None:
            self.prev_area = current_area
            return False
        
        # Вычисляем процент изменения
        area_change = abs(current_area - self.prev_area) / (self.prev_area + 1e-6)
        
        self.prev_area = current_area
        
        # Поклёвка - это значительное изменение площади
        return area_change > self.threshold


class HybridFloatDetector(FloatDetector):
    """Combines multiple float detection methods"""
    
    def __init__(self, target_color="red"):
        super().__init__()
        self.color_detector = ColorBasedFloatDetector(target_color)
        self.motion_detector = MotionBasedFloatDetector()
        self.area_detector = AreaBasedFloatDetector()
    
    def detect_float(self, frame):
        """Detect float using color detection"""
        return self.color_detector.detect_float(frame)
    
    def detect_bite(self, frame, sensitivity=0.5):
        """
        Detect bite using multiple methods
        
        Args:
            frame: numpy array (BGR)
            sensitivity: 0-1, how sensitive detection should be
        
        Returns:
            dict: {'detected': bool, 'methods': [list of positive detections]}
        """
        methods_triggered = []
        
        # Color + Position
        if self.color_detector.detect_bite(frame):
            methods_triggered.append('color_position')
        
        # Motion
        if self.motion_detector.detect_bite(frame):
            methods_triggered.append('motion')
        
        # Area change
        if self.area_detector.detect_bite(frame, self.color_detector):
            methods_triggered.append('area_change')
        
        # Требуем N методов в зависимости от чувствительности
        required_methods = max(1, int(3 * (1 - sensitivity)))
        detected = len(methods_triggered) >= required_methods
        
        return {
            'detected': detected,
            'methods': methods_triggered,
            'confidence': len(methods_triggered) / 3.0
        }
    
    def draw_debug_info(self, frame, float_info):
        """
        Draw debug information on frame
        
        Args:
            frame: numpy array
            float_info: output from detect_float()
        
        Returns:
            numpy array: frame with debug info
        """
        if float_info is None:
            return frame
        
        result = frame.copy()
        pos = float_info.get('position')
        radius = float_info.get('radius', 10)
        
        if pos:
            # Рисуем окружность поплавка
            cv2.circle(result, pos, int(radius), (0, 255, 0), 2)
            # Рисуем центр
            cv2.circle(result, pos, 3, (0, 0, 255), -1)
            # Текст с информацией
            cv2.putText(result, f"Float: {pos}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return result
