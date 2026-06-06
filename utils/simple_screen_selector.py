"""
Альтернативный селектор области - простой и надёжный
Использует OpenCV вместо Tkinter для лучшей совместимости
"""
import cv2
import mss
import numpy as np


class SimpleScreenSelector:
    """Простой селектор с OpenCV - более надёжный"""
    
    def __init__(self, window_name="Select Float Region"):
        self.window_name = window_name
        self.drawing = False
        self.start_x = 0
        self.start_y = 0
        self.current_x = 0
        self.current_y = 0
        self.frame = None
        self.original_frame = None
        self.selection = None
    
    def select_region(self):
        """Interactive region selection using OpenCV"""
        print("📸 Захватываю скриншот...")
        
        # Захватываем экран
        sct = mss.mss()
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        
        # Конвертируем в OpenCV формат (без масштабирования!)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        
        self.frame = frame.copy()
        self.original_frame = frame.copy()
        
        print(f"✓ Размер: {frame.shape[1]}x{frame.shape[0]}")
        print("\n" + "="*60)
        print("ИНСТРУКЦИЯ:")
        print("="*60)
        print("1. Левая кнопка мыши - начало выделения")
        print("2. Перетащи мышку - нарисуй прямоугольник")
        print("3. Отпусти кнопку - заверши выделение")
        print("4. Нажми SPACE - сохранить выбор")
        print("5. Нажми ESC - отменить")
        print("="*60 + "\n")
        
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        while True:
            cv2.imshow(self.window_name, self.frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC - отмена
                print("⚠️  Выбор отменён (ESC)")
                self.selection = None
                break
            
            elif key == 32:  # SPACE - сохранить
                if self.selection:
                    print(f"✓ Выбор сохранён: {self.selection}")
                    break
                else:
                    print("⚠️  Сначала выбери область!")
        
        cv2.destroyAllWindows()
        return self.selection
    
    def mouse_callback(self, event, x, y, flags, param):
        """Mouse event handler"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Начало выделения
            self.drawing = True
            self.start_x = x
            self.start_y = y
            self.current_x = x
            self.current_y = y
            self.frame = self.original_frame.copy()
        
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                # Обновляем текущую позицию и рисуем превью
                self.current_x = x
                self.current_y = y
                
                # Копируем оригинальное изображение
                self.frame = self.original_frame.copy()
                
                # Рисуем прямоугольник
                x1 = min(self.start_x, x)
                y1 = min(self.start_y, y)
                x2 = max(self.start_x, x)
                y2 = max(self.start_y, y)
                
                # Заливка полупрозрачная
                overlay = self.frame.copy()
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), -1)
                cv2.addWeighted(overlay, 0.2, self.frame, 0.8, 0, self.frame)
                
                # Контур
                cv2.rectangle(self.frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                
                # Информация
                width = x2 - x1
                height = y2 - y1
                info = f"Size: {width}x{height} px | Press SPACE to save"
                cv2.putText(
                    self.frame, info, (x1 + 10, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
                )
        
        elif event == cv2.EVENT_LBUTTONUP:
            if self.drawing:
                self.drawing = False
                
                # Сохраняем выделение (в оригинальных координатах)
                x1 = min(self.start_x, self.current_x)
                y1 = min(self.start_y, self.current_y)
                x2 = max(self.start_x, self.current_x)
                y2 = max(self.start_y, self.current_y)
                
                width = x2 - x1
                height = y2 - y1
                
                if width >= 20 and height >= 20:
                    self.selection = {
                        "x": x1,
                        "y": y1,
                        "width": width,
                        "height": height
                    }
                    
                    print(f"✓ Область выбрана: {self.selection}")
                    print("  Нажми SPACE для сохранения или ESC для отмены")
                else:
                    print("⚠️  Область слишком маленькая! Минимум 20x20 пикселей")
                    self.selection = None


# Функция-обёртка для совместимости
def select_region_simple():
    """Simple region selector - standalone"""
    selector = SimpleScreenSelector()
    return selector.select_region()


if __name__ == "__main__":
    # Демо
    print("Simple Screen Selector Demo")
    region = select_region_simple()
    if region:
        print(f"\n✓ Выбранная область:")
        print(f"  X: {region['x']}")
        print(f"  Y: {region['y']}")
        print(f"  Width: {region['width']}")
        print(f"  Height: {region['height']}")
    else:
        print("\n❌ Выбор отменён")