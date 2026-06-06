"""
Утилита для анализа и захвата образцов поплавков
Помогает обучить бота распознавать сложные расцветки
"""
import cv2
import numpy as np
import os
from datetime import datetime


class FloatAnalyzer:
    """Анализирует образцы поплавков и выводит рекомендации"""
    
    def __init__(self, output_dir="float_samples"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def capture_float_sample(self, frame, region, name=None):
        """
        Захватить и сохранить образец поплавка
        
        Args:
            frame: исходный кадр
            region: dict {'x', 'y', 'width', 'height'}
            name: название образца (опционально)
        """
        x, y, w, h = region['x'], region['y'], region['width'], region['height']
        float_roi = frame[y:y+h, x:x+w]
        
        if name is None:
            name = f"float_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        filename = os.path.join(self.output_dir, f"{name}.png")
        cv2.imwrite(filename, float_roi)
        print(f"✓ Образец сохранён: {filename}")
        
        # Анализируем образец
        self.analyze_sample(float_roi, name)
        return filename
    
    def analyze_sample(self, float_roi, name="float"):
        """Анализирует образец и выводит статистику"""
        print(f"\n{'='*50}")
        print(f"Анализ образца: {name}")
        print(f"{'='*50}")
        
        # Размеры
        h, w = float_roi.shape[:2]
        print(f"Размер: {w}x{h} пикселей")
        
        # Преобразуем в HSV
        hsv = cv2.cvtColor(float_roi, cv2.COLOR_BGR2HSV)
        
        # Анализ по каналам HSV
        h_vals = hsv[:, :, 0].flatten()
        s_vals = hsv[:, :, 1].flatten()
        v_vals = hsv[:, :, 2].flatten()
        
        # Фильтруем пиксели с достаточной насыщенностью
        mask = s_vals > 30
        h_filtered = h_vals[mask]
        
        if len(h_filtered) > 0:
            print(f"\n🎨 Анализ цвета (HSV):")
            print(f"  Hue (оттенок):")
            print(f"    Минимум: {h_filtered.min()}")
            print(f"    Максимум: {h_filtered.max()}")
            print(f"    Среднее: {h_filtered.mean():.1f}")
            print(f"    Мода: {np.bincount(h_filtered).argmax()}")
            
            print(f"  Saturation (насыщенность):")
            print(f"    Минимум: {s_vals.min()}")
            print(f"    Максимум: {s_vals.max()}")
            print(f"    Среднее: {s_vals.mean():.1f}")
            
            print(f"  Value (яркость):")
            print(f"    Минимум: {v_vals.min()}")
            print(f"    Максимум: {v_vals.max()}")
            print(f"    Среднее: {v_vals.mean():.1f}")
        
        # Рекомендации
        self._print_recommendations(h_filtered, s_vals, v_vals)
    
    def _print_recommendations(self, h_filtered, s_vals, v_vals):
        """Выводит рекомендации для config.json"""
        if len(h_filtered) == 0:
            print("\n⚠️  Не найдено цветных пикселей (низкая насыщенность)")
            return
        
        print(f"\n💡 Рекомендации для config.json:")
        
        # Определяем цвет
        hue_mode = np.bincount(h_filtered).argmax()
        
        if hue_mode < 10 or hue_mode > 170:
            color = "red"
            h_range = f"H: 0-10 или 170-180"
        elif 10 <= hue_mode < 25:
            color = "orange"
            h_range = f"H: 5-25"
        elif 25 <= hue_mode < 40:
            color = "yellow"
            h_range = f"H: 20-40"
        elif 40 <= hue_mode < 85:
            color = "green"
            h_range = f"H: 35-85"
        elif 85 <= hue_mode < 100:
            color = "cyan"
            h_range = f"H: 80-100"
        elif 100 <= hue_mode < 130:
            color = "blue"
            h_range = f"H: 95-130"
        elif 130 <= hue_mode < 170:
            color = "magenta"
            h_range = f"H: 125-170"
        else:
            color = "unknown"
            h_range = f"H: {h_filtered.min()}-{h_filtered.max()}"
        
        print(f'  "float_color": "{color}"')
        print(f'  "hue_range": "{h_range}"')
        
        # Рекомендуем использовать Advanced детектор если неоднородная расцветка
        unique_hues = len(np.unique(h_filtered))
        hue_std = np.std(h_filtered)
        
        if hue_std > 15 or unique_hues > 20:
            print(f"\n⚠️  Поплавок имеет неоднородную расцветку!")
            print(f'   Рекомендуем: "float_detection_method": "template_matching"')
        else:
            print(f"\n✓ Однородная расцветка, подходит для обычного детектора")
            print(f'   Можно использовать: "float_detection_method": "color"')
    
    def create_template_from_samples(self):
        """
        Создаёт усреднённый шаблон из всех сохранённых образцов
        Полезно для Template Matching
        """
        samples = []
        
        for filename in os.listdir(self.output_dir):
            if filename.endswith('.png'):
                path = os.path.join(self.output_dir, filename)
                img = cv2.imread(path)
                if img is not None:
                    samples.append(img)
        
        if not samples:
            print("❌ Нет образцов для анализа")
            return None
        
        print(f"✓ Найдено {len(samples)} образцов")
        
        # Приводим все к одному размеру
        h, w = samples[0].shape[:2]
        resized = []
        for sample in samples:
            resized.append(cv2.resize(sample, (w, h)))
        
        # Создаём среднее изображение
        template = np.mean(np.array(resized), axis=0).astype(np.uint8)
        
        template_path = os.path.join(self.output_dir, "_template.png")
        cv2.imwrite(template_path, template)
        print(f"✓ Шаблон сохранён: {template_path}")
        
        return template


def main():
    """Демо анализа образцов поплавков"""
    import mss
    
    analyzer = FloatAnalyzer()
    
    print("Утилита анализа поплавков")
    print("=" * 50)
    print("Используется для обучения бота распознавать сложные расцветки")
    print()
    
    # Захватываем образец с экрана
    sct = mss.mss()
    monitor = sct.monitors[1]
    
    screenshot = sct.grab(monitor)
    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    
    # Выбираем область вручную
    print("Инструкции:")
    print("1. Нарисуй прямоугольник вокруг поплавка")
    print("2. Левая кнопка - начало, отпусти - конец")
    print("3. Правая кнопка - отмена")
    print()
    
    roi_coords = select_region(frame)
    if roi_coords:
        x1, y1, x2, y2 = roi_coords
        region = {
            'x': min(x1, x2),
            'y': min(y1, y2),
            'width': abs(x2 - x1),
            'height': abs(y2 - y1)
        }
        analyzer.capture_float_sample(frame, region, "my_float")
        
        # Если есть несколько образцов, создаём шаблон
        if len(os.listdir(analyzer.output_dir)) > 2:  # > 2 потому что есть _template.png
            analyzer.create_template_from_samples()


def select_region(image):
    """Выбор региона мышью на изображении"""
    drawing = False
    x_start, y_start = 0, 0
    
    def mouse_callback(event, x, y, flags, param):
        nonlocal drawing, x_start, y_start
        
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            x_start, y_start = x, y
        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                img_copy = image.copy()
                cv2.rectangle(img_copy, (x_start, y_start), (x, y), (0, 255, 0), 2)
                cv2.imshow("Select Float Region", img_copy)
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            return (x_start, y_start, x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            return None
    
    cv2.imshow("Select Float Region", image)
    cv2.setMouseCallback("Select Float Region", mouse_callback)
    
    result = None
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        # Проверяем результат через mouse_callback
    
    cv2.destroyAllWindows()
    return result


if __name__ == "__main__":
    main()
