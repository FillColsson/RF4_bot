"""
Продвинутые детекторы поплавков для сложных случаев
Поддерживают Template Matching, Multi-HSV, и гибридные подходы
"""
import cv2
import numpy as np
from collections import deque


class TemplateMatchingFloatDetector:
    """Детектор поплавка через Template Matching (шаблонное совпадение)"""
    
    def __init__(self, template_path, threshold=0.7):
        """
        Args:
            template_path: путь к изображению-шаблону поплавка
            threshold: порог совпадения (0-1)
        """
        self.template = cv2.imread(template_path)
        if self.template is None:
            raise ValueError(f"Не удалось загрузить шаблон: {template_path}")
        
        self.template_h, self.template_w = self.template.shape[:2]
        self.threshold = threshold
        self.prev_position = None
        self.position_history = deque(maxlen=30)
        self.area_history = deque(maxlen=30)
    
    def detect_float(self, frame):
        """
        Поиск поплавка через Template Matching
        
        Returns:
            dict с информацией о поплавке или None
        """
        if frame is None:
            return None
        
        # Используем multi-scale для поиска на разных масштабах
        best_match = None
        best_val = 0
        best_scale = 1.0
        
        # Тестируем разные масштабы (0.5 - 2.0x)
        for scale in [0.5, 0.7, 0.85, 1.0, 1.15, 1.3, 1.5]:
            h, w = int(self.template_h * scale), int(self.template_w * scale)
            
            if h > frame.shape[0] or w > frame.shape[1]:
                continue
            
            template_scaled = cv2.resize(self.template, (w, h))
            
            # Template matching
            result = cv2.matchTemplate(frame, template_scaled, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val > best_val:
                best_val = max_val
                best_match = (max_loc, (w, h))
                best_scale = scale
        
        if best_val < self.threshold:
            return None
        
        match_pos, match_size = best_match
        x, y = match_pos
        w, h = match_size
        
        # Определяем центр и радиус
        center = (x + w // 2, y + h // 2)
        radius = max(w, h) // 2
        
        # Обновляем историю
        self.prev_position = center
        self.position_history.append(center)
        self.area_history.append(w * h)
        
        return {
            'position': center,
            'radius': radius,
            'area': w * h,
            'confidence': best_val,
            'scale': best_scale,
            'bbox': (x, y, w, h)
        }
    
    def detect_bite(self, frame, sensitivity=0.65):
        """
        Обнаружение поклёвки через анализ движения
        
        Args:
            frame: текущий кадр
            sensitivity: чувствительность (0-1)
        
        Returns:
            dict {'detected': bool, 'methods': list}
        """
        float_info = self.detect_float(frame)
        if not float_info:
            return {'detected': False, 'methods': []}
        
        methods = []
        
        # Метод 1: Анализ движения по истории позиций
        if len(self.position_history) > 3:
            distances = []
            for i in range(1, len(self.position_history)):
                p1 = self.position_history[i-1]
                p2 = self.position_history[i]
                dist = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                distances.append(dist)
            
            # Анализируем последние 3 расстояния
            recent_distances = distances[-3:]
            max_dist = max(recent_distances) if recent_distances else 0
            avg_dist = np.mean(recent_distances) if recent_distances else 0
            
            # Порог движения зависит от размера поплавка
            movement_threshold = float_info['radius'] * 0.15 * (2.0 - sensitivity)
            
            if max_dist > movement_threshold and avg_dist > movement_threshold * 0.5:
                methods.append('template_motion')
        
        # Метод 2: Анализ изменения размера
        if len(self.area_history) > 3:
            current_area = self.area_history[-1]
            prev_area = self.area_history[-3]
            
            area_change = abs(current_area - prev_area) / prev_area if prev_area > 0 else 0
            area_threshold = 0.15 * (2.0 - sensitivity)
            
            if area_change > area_threshold:
                methods.append('template_area')
        
        # Требуется 1+ метод (для Template Matching менее требовательны)
        detected = len(methods) >= 1
        
        return {
            'detected': detected,
            'methods': methods,
            'confidence': float_info.get('confidence', 0) if detected else 0
        }


class MultiHSVFloatDetector:
    """
    Детектор поплавка с поддержкой нескольких HSV диапазонов
    Подходит для неоднородных расцветок
    """
    
    def __init__(self, hsv_ranges=None):
        """
        Args:
            hsv_ranges: list of (h_min, h_max, s_min, s_max, v_min, v_max)
        
        Пример:
            [
                (0, 10, 50, 255, 50, 255),      # Красный
                (170, 180, 50, 255, 50, 255),   # Красный (другой диапазон)
                (5, 25, 50, 255, 50, 255),      # Оранжевый
            ]
        """
        self.hsv_ranges = hsv_ranges or [
            (0, 10, 50, 255, 50, 255),    # Красный
            (170, 180, 50, 255, 50, 255), # Красный (второй диапазон)
        ]
        
        self.position_history = deque(maxlen=30)
        self.area_history = deque(maxlen=30)
        self.prev_position = None
    
    def detect_float(self, frame):
        """
        Поиск поплавка через несколько HSV диапазонов
        
        Returns:
            dict с информацией о поплавке или None
        """
        if frame is None:
            return None
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Создаём объединённую маску из всех диапазонов
        combined_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        
        for h_min, h_max, s_min, s_max, v_min, v_max in self.hsv_ranges:
            if h_min <= h_max:
                # Обычный диапазон
                mask = cv2.inRange(hsv, (h_min, s_min, v_min), (h_max, s_max, v_max))
            else:
                # Обёрнутый диапазон (для красного через 0)
                mask1 = cv2.inRange(hsv, (h_min, s_min, v_min), (180, s_max, v_max))
                mask2 = cv2.inRange(hsv, (0, s_min, v_min), (h_max, s_max, v_max))
                mask = cv2.bitwise_or(mask1, mask2)
            
            combined_mask = cv2.bitwise_or(combined_mask, mask)
        
        # Морфологические операции для очистки
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        
        # Поиск контуров
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Находим наибольший контур
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        
        if area < 10:
            return None
        
        # Минимальная окружность
        (x, y), radius = cv2.minEnclosingCircle(largest_contour)
        
        center = (int(x), int(y))
        radius = int(radius)
        
        # Обновляем историю
        self.prev_position = center
        self.position_history.append(center)
        self.area_history.append(area)
        
        return {
            'position': center,
            'radius': radius,
            'area': area,
            'confidence': min(area / 5000.0, 1.0),
            'contour': largest_contour
        }
    
    def detect_bite(self, frame, sensitivity=0.65):
        """Обнаружение поклёвки через анализ движения и размера"""
        float_info = self.detect_float(frame)
        if not float_info:
            return {'detected': False, 'methods': []}
        
        methods = []
        
        # Метод 1: Движение
        if len(self.position_history) > 3:
            distances = []
            for i in range(1, len(self.position_history)):
                p1 = self.position_history[i-1]
                p2 = self.position_history[i]
                dist = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                distances.append(dist)
            
            recent = distances[-3:]
            if max(recent) > float_info['radius'] * 0.1 * (2.0 - sensitivity):
                methods.append('multi_hsv_motion')
        
        # Метод 2: Размер
        if len(self.area_history) > 3:
            curr_area = self.area_history[-1]
            prev_area = self.area_history[-3]
            
            change = abs(curr_area - prev_area) / prev_area if prev_area > 0 else 0
            if change > 0.1 * (2.0 - sensitivity):
                methods.append('multi_hsv_area')
        
        detected = len(methods) >= 1
        
        return {
            'detected': detected,
            'methods': methods,
            'confidence': float_info['confidence'] if detected else 0
        }


class AdaptiveFloatDetector:
    """
    Адаптивный детектор - автоматически выбирает лучший метод
    """
    
    def __init__(self, target_color="red"):
        self.target_color = target_color
        self.methods = [
            ('color', self._init_color_detector()),
        ]
        
        # Пытаемся инициализировать дополнительные методы
        try:
            self.methods.append(('template', None))  # Будет инициализирован с шаблоном
        except:
            pass
        
        self.method_scores = {}
        self.best_method = None
    
    def _init_color_detector(self):
        """Инициализирует простой цветовой детектор"""
        from vision.float_detectors import ColorBasedFloatDetector
        return ColorBasedFloatDetector(self.target_color)
    
    def add_template(self, template_path):
        """Добавляет Template Matching метод"""
        try:
            template_detector = TemplateMatchingFloatDetector(template_path, threshold=0.6)
            self.methods = [m for m in self.methods if m[0] != 'template']
            self.methods.append(('template', template_detector))
            print(f"✓ Template Matching метод добавлен")
        except Exception as e:
            print(f"✗ Ошибка при добавлении шаблона: {e}")
    
    def detect_float(self, frame):
        """Пробует все методы и возвращает лучший результат"""
        results = {}
        
        for method_name, detector in self.methods:
            if detector is None:
                continue
            
            try:
                result = detector.detect_float(frame)
                if result:
                    results[method_name] = result
            except:
                pass
        
        if not results:
            return None
        
        # Выбираем результат с наибольшей уверенностью
        best = max(results.items(), key=lambda x: x[1].get('confidence', 0))
        self.best_method = best[0]
        
        return best[1]
    
    def detect_bite(self, frame, sensitivity=0.65):
        """Обнаруживает поклёвку используя лучший метод"""
        if self.best_method:
            for method_name, detector in self.methods:
                if method_name == self.best_method and detector:
                    return detector.detect_bite(frame, sensitivity)
        
        # Если лучшего метода нет, используем первый
        for method_name, detector in self.methods:
            if detector:
                return detector.detect_bite(frame, sensitivity)
        
        return {'detected': False, 'methods': []}
