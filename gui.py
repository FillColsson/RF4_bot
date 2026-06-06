import customtkinter as ctk
from tkinter import messagebox, scrolledtext


class RF4BotGUI:
    def __init__(self, root, config, save_callback, start_callback=None, stop_callback=None):
        self.root = root
        self.config = config
        self.save_callback = save_callback
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.status_label = None
        self.log_text = None
        self.build_ui()

    def build_ui(self):
        # Заголовок
        title = ctk.CTkLabel(self.root, text="RF4 AutoFisher", 
                            font=ctk.CTkFont(size=32, weight="bold"),
                            text_color="#A0B0C0")
        title.pack(pady=(20, 5))

        subtitle = ctk.CTkLabel(self.root, text="Поплавочная ловля • 1920×1080", 
                               font=ctk.CTkFont(size=16), text_color="#708090")
        subtitle.pack(pady=(0, 20))

        # Статус
        self.status_label = ctk.CTkLabel(self.root, text="Готов к запуску", 
                                        font=ctk.CTkFont(size=14),
                                        text_color="#CCCCCC")
        self.status_label.pack(pady=5)

        # Вкладки
        self.tabview = ctk.CTkTabview(self.root, fg_color="#1E1E1E")
        self.tabview.pack(fill="both", expand=True, padx=25, pady=10)

        self.tab_general = self.tabview.add("Основные")
        self.tab_float = self.tabview.add("Поплавок")
        self.tab_advanced = self.tabview.add("Лог")

        self.build_general_tab()
        self.build_float_tab()
        self.build_log_tab()

        # Нижняя панель управления
        control_frame = ctk.CTkFrame(self.root, fg_color="#252526")
        control_frame.pack(fill="x", padx=25, pady=15)

        self.start_btn = ctk.CTkButton(control_frame, text="▶ ЗАПУСТИТЬ (F6)", 
                                      font=ctk.CTkFont(size=16, weight="bold"), height=50,
                                      fg_color="#2E8B57", hover_color="#3CB371",
                                      command=self.start_bot)
        self.start_btn.pack(side="left", padx=10, expand=True, fill="x")

        self.stop_btn = ctk.CTkButton(control_frame, text="⏹ ОСТАНОВИТЬ (F7)", 
                                     font=ctk.CTkFont(size=16, weight="bold"), height=50,
                                     fg_color="#B22222", hover_color="#DC143C",
                                     command=self.stop_bot)
        self.stop_btn.pack(side="left", padx=10, expand=True, fill="x")
        
        self.select_region_btn = ctk.CTkButton(control_frame, text="🎯 Выбрать область", 
                                              font=ctk.CTkFont(size=16), height=50,
                                              fg_color="#1E90FF", hover_color="#4169E1",
                                              command=self.select_region)
        self.select_region_btn.pack(side="right", padx=10, expand=True, fill="x")

    def build_general_tab(self):
        frame = ctk.CTkFrame(self.tab_general)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Мощность заброса (%)", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(10,0))
        self.cast_slider = ctk.CTkSlider(frame, from_=50, to=100, number_of_steps=50)
        self.cast_slider.set(self.config.get("cast_power", 75))
        self.cast_slider.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(frame, text="Задержка заброса (сек)", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(15,0))
        self.delay_slider = ctk.CTkSlider(frame, from_=0.5, to=3.0, number_of_steps=50)
        self.delay_slider.set(self.config.get("cast_delay", 1.2))
        self.delay_slider.pack(fill="x", padx=20, pady=5)

    def build_float_tab(self):
        frame = ctk.CTkFrame(self.tab_float)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Область распознавания поплавка", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=10)
        
        region_info = self.config.get("detection_region", {})
        region_text = f"X: {region_info.get('x', 850)}, Y: {region_info.get('y', 350)}, W: {region_info.get('width', 450)}, H: {region_info.get('height', 380)}"
        ctk.CTkLabel(frame, text=region_text, font=ctk.CTkFont(size=12, slant="italic")).pack(anchor="w", padx=40, pady=5)

        ctk.CTkLabel(frame, text="Чувствительность поклёвки (%)", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(15,0))
        self.sens_slider = ctk.CTkSlider(frame, from_=30, to=100, number_of_steps=70)
        self.sens_slider.set(self.config.get("bite_detection_sensitivity", 65))
        self.sens_slider.pack(fill="x", padx=20, pady=5)

        self.auto_hook_check = ctk.CTkCheckBox(frame, text="Автоподсечка")
        self.auto_hook_check.pack(anchor="w", padx=40, pady=10)
        if self.config.get("auto_hook", True):
            self.auto_hook_check.select()

    def build_log_tab(self):
        frame = ctk.CTkFrame(self.tab_advanced)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Логи работы бота", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=10)
        
        self.log_text = scrolledtext.ScrolledText(frame, height=12, width=60, bg="#2b2b2b", fg="#CCCCCC")
        self.log_text.pack(fill="both", expand=True, pady=5)

    def update_status(self, message, color="#CCCCCC"):
        """Update status label"""
        if self.status_label:
            self.status_label.configure(text=message, text_color=color)
            self.root.update()
    
    def log(self, message):
        """Add message to log"""
        if self.log_text:
            self.log_text.insert("end", f"{message}\n")
            self.log_text.see("end")
            self.root.update()

    def set_control_callbacks(self, start_callback, stop_callback):
        """Wire GUI buttons to bot start/stop handlers"""
        self.start_callback = start_callback
        self.stop_callback = stop_callback
    
    def select_region(self):
        """Open screen selector with choice of method"""
        try:
            # Скрываем главное окно
            self.root.withdraw()
            
            # Спрашиваем у пользователя какой метод использовать
            from tkinter import simpledialog
            
            choice = messagebox.askyesno(
                "Выбор области - метод",
                "Выбери метод:\n\n" +
                "ДА - OpenCV (более надёжный)\n" +
                "НЕТ - Tkinter (более красивый)\n\n" +
                "Если первый не работает, используй второй"
            )
            
            if choice:
                # OpenCV - более надёжный
                print("→ Используем OpenCV селектор...")
                from utils.simple_screen_selector import SimpleScreenSelector
                selector = SimpleScreenSelector()
                region = selector.select_region()
                if region:
                    self.on_region_selected(region)
            else:
                # Tkinter - красивый
                print("→ Используем Tkinter селектор...")
                from utils.screen_selector import ScreenSelector
                selector = ScreenSelector(self.on_region_selected)
                selector.select_region()
            
            # Восстанавливаем главное окно
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            
        except Exception as e:
            print(f"❌ Ошибка при выборе области: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Ошибка", f"Ошибка при выборе области:\n{e}")
            self.root.deiconify()
    
    def on_region_selected(self, region):
        """Handle region selection"""
        if region is None:
            messagebox.showwarning("Отменено", "Выбор области отменён")
            return
        
        try:
            self.config["detection_region"] = region
            self.save_callback(self.config)
            
            # Обновляем информацию о регионе в интерфейсе
            region_text = (f"X: {region.get('x', 0)}, Y: {region.get('y', 0)}, " +
                          f"W: {region.get('width', 0)}, H: {region.get('height', 0)}")
            
            messagebox.showinfo(
                "Успешно! ✓", 
                f"Область сохранена:\n\n{region_text}"
            )
            
            print(f"✓ Регион сохранён: {region}")
            
        except Exception as e:
            print(f"❌ Ошибка при сохранении области: {e}")
            messagebox.showerror("Ошибка", f"Ошибка при сохранении:\n{e}")

    def start_bot(self):
        if self.start_callback:
            self.start_callback()
        else:
            messagebox.showinfo("Запуск", "Нажми F6 для старта бота")

    def stop_bot(self):
        if self.stop_callback:
            self.stop_callback()
        else:
            messagebox.showinfo("Стоп", "Нажми F7 для остановки бота")
