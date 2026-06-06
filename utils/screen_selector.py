"""
Screen selector tool - allows user to select areas on screen
Улучшенная версия с лучшей обработкой событий и оптимизацией
"""
import tkinter as tk
import mss
from PIL import Image, ImageTk
import threading


class ScreenSelector:
    def __init__(self, callback=None):
        self.callback = callback
        self.root = None
        self.canvas = None
        self.photo_image = None
        self.start_x = 0
        self.start_y = 0
        self.rect_id = None
        self.selection = None
        self.dragging = False
    
    def select_region(self):
        """Open screen selector window"""
        try:
            self.root = tk.Tk()
            self.root.title("Выбери область на экране (левая кнопка + перетащи)")
            self.root.attributes('-topmost', True)
            self.root.geometry("1920x1080")
            
            # Захватываем скриншот
            sct = mss.mss()
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            
            # Конвертируем в PIL Image - используем RGB вместо RGBA
            image = Image.frombytes('RGB', (screenshot.width, screenshot.height), screenshot.rgb)
            
            # Масштабируем если нужно (оптимизация)
            display_width = self.root.winfo_screenwidth()
            display_height = self.root.winfo_screenheight()
            
            if image.width > display_width or image.height > display_height:
                scale = min(display_width / image.width, display_height / image.height)
                new_size = (int(image.width * scale), int(image.height * scale))
                image = image.resize(new_size, Image.LANCZOS)
            
            # Создаем canvas
            self.photo_image = ImageTk.PhotoImage(image)
            self.canvas = tk.Canvas(
                self.root, 
                image=self.photo_image, 
                cursor="crosshair",
                highlightthickness=0
            )
            self.canvas.pack(fill="both", expand=True)
            
            # Binding событий мыши
            self.canvas.bind("<Button-1>", self.on_press, add=True)
            self.canvas.bind("<B1-Motion>", self.on_drag, add=True)
            self.canvas.bind("<ButtonRelease-1>", self.on_release, add=True)
            
            # Binding для отмены (ESC)
            self.root.bind("<Escape>", lambda e: self.on_cancel())
            
            # Label с инструкциями
            label = tk.Label(
                self.root, 
                text="ИНСТРУКЦИЯ:\n" +
                     "1. Нарисуй прямоугольник вокруг поплавка (левая кнопка мыши)\n" +
                     "2. Красная линия показывает область\n" +
                     "3. Отпусти кнопку - область сохранится\n" +
                     "4. ESC для отмены",
                bg="#1a1a1a", 
                fg="yellow",
                font=("Arial", 12),
                justify="left",
                padx=10,
                pady=10
            )
            label.pack(side="bottom", fill="x")
            
            # Окно в фокусе
            self.root.focus_force()
            self.root.lift()
            
            self.root.mainloop()
            
        except Exception as e:
            print(f"❌ Ошибка в ScreenSelector: {e}")
            import traceback
            traceback.print_exc()
        
        return self.selection
    
    def on_press(self, event):
        """Mouse button press"""
        self.start_x = event.x
        self.start_y = event.y
        self.dragging = True
        
        # Удаляем старый прямоугольник если есть
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
    
    def on_drag(self, event):
        """Mouse drag"""
        if not self.dragging:
            return
        
        # Удаляем старый прямоугольник
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        # Рисуем новый
        try:
            self.rect_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline="red", width=3, fill="red", stipple="gray50"
            )
            
            # Информация о размере
            width = abs(event.x - self.start_x)
            height = abs(event.y - self.start_y)
            text = f"Размер: {width}x{height}"
            
            # Удаляем старый текст если есть
            for item in self.canvas.find_all():
                if isinstance(self.canvas.itemcget(item, "text"), str):
                    if "Размер" in self.canvas.itemcget(item, "text"):
                        self.canvas.delete(item)
            
            # Рисуем новый текст
            self.canvas.create_text(
                event.x + 10, event.y + 10,
                text=text,
                fill="yellow",
                font=("Arial", 14, "bold"),
                anchor="nw",
                bg="#1a1a1a"
            )
            
            self.canvas.update()
        except Exception as e:
            print(f"Ошибка при рисовании: {e}")
    
    def on_release(self, event):
        """Mouse button release"""
        self.dragging = False
        
        # Получаем координаты
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)
        
        width = x2 - x1
        height = y2 - y1
        
        # Проверяем минимальный размер
        if width < 20 or height < 20:
            print("⚠️  Область слишком маленькая! Минимум 20x20 пикселей")
            return
        
        # Сохраняем выделение
        self.selection = {
            "x": x1,
            "y": y1,
            "width": width,
            "height": height
        }
        
        print(f"✓ Область выбрана: x={x1}, y={y1}, width={width}, height={height}")
        
        if self.callback:
            try:
                self.callback(self.selection)
            except Exception as e:
                print(f"Ошибка при вызове callback: {e}")
        
        self.close()
    
    def on_cancel(self):
        """Cancel selection"""
        print("⚠️  Выбор отменён (нажата ESC)")
        self.selection = None
        self.close()
    
    def close(self):
        """Close selector window"""
        try:
            if self.root:
                self.root.quit()
                self.root.destroy()
        except:
            pass

