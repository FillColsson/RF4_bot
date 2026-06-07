import customtkinter as ctk
import json
import os
import keyboard
import threading
from gui import RF4BotGUI
from core.bot import RF4Bot
from utils.overlay import BotOverlay

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class RF4BotApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("RF4 AutoFisher — Поплавочная ловля")
        self.root.geometry("1100x750")
        self.root.resizable(True, True)
        
        self.config = self.load_config()
        self.gui = RF4BotGUI(self.root, self.config, self.save_config)
        
        self.bot = RF4Bot(self.config, self.gui)
        self.gui.set_control_callbacks(self.start_bot, self.stop_bot)
        self.overlay = None
        self.hotkeys_registered = False
        
        # Регистрируем горячие клавиши
        self._setup_hotkeys()
        
        # Обработчики закрытия
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_hotkeys(self):
        """Setup hotkeys with error handling"""
        try:
            hotkey_start = self.config.get("hotkey_start", "f6").lower()
            hotkey_stop = self.config.get("hotkey_stop", "f7").lower()
            
            print(f"🔑 Регистрируем горячие клавиши:")
            print(f"  Start: {hotkey_start}")
            print(f"  Stop: {hotkey_stop}")
            
            # Очищаем старые горячие клавиши если есть
            try:
                keyboard.clear_all_hotkeys()
            except:
                pass
            
            # Добавляем новые
            keyboard.add_hotkey(hotkey_start, self.start_bot, suppress=False)
            keyboard.add_hotkey(hotkey_stop, self.stop_bot, suppress=False)
            
            self.hotkeys_registered = True
            print(f"✓ Горячие клавиши зарегистрированы успешно!")
            
        except Exception as e:
            print(f"❌ Ошибка при регистрации горячих клавиш: {e}")
            print(f"   Попробуй перезагрузить программу или изменить клавиши в config.json")
            self.gui.update_status("❌ Горячие клавиши не работают!", "#FF0000")

    def load_config(self):
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки config: {e}")
        return self.default_config()

    def save_config(self, config):
        self.config = config
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        try:
            self.bot.update_config(config)
        except:
            pass

    def default_config(self):
        return {
            "resolution": "1920x1080",
            "fishing_mode": "float",
            "float_color": "red",
            "cast_power": 75,
            "cast_hold_min": 0.15,
            "cast_hold_max": 2.5,
            "cast_delay": 1.2,
            "bite_detection_sensitivity": 65,
            "detection_region": {"x": 850, "y": 350, "width": 450, "height": 380},
            "auto_hook": True,
            "auto_collect": True,
            "auto_repair": True,
            "float_detection_method": "hybrid",
            "hotkey_start": "f6",
            "hotkey_stop": "f7",
            "vision": {
                "float_stable_frames": 5,
                "float_missing_frames_for_fight": 4,
                "bite_cooldown_sec": 2.0,
                "catch_screen_threshold": 0.55,
                "catch_edge_ratio": 0.82,
                "catch_samples_dir": "catch_samples",
                "max_cast_wait_sec": 20,
                "max_wait_sec": 300,
                "max_fight_sec": 120
            },
            "advanced_settings": {
                "enable_template_matching": False,
                "template_path": "float_samples/_template.png"
            }
        }

    def start_bot(self):
        """Start bot with error handling and overlay"""
        print("\n" + "="*60)
        print("🎣 ЗАПУСК БОТА")
        print("="*60)
        
        if self.bot.running:
            print("⚠️  Бот уже запущен!")
            return
        
        try:
            # Проверяем конфиг
            region = self.config.get("detection_region", {})
            if not region.get("width") or not region.get("height"):
                print("❌ Ошибка: область обнаружения не выбрана!")
                print("   Нажми кнопку '🎯 Выбрать область' в интерфейсе")
                self.gui.update_status("❌ Выбери область поплавка!", "#FF0000")
                return
            
            print(f"✓ Регион: {region}")
            print(f"✓ Режим: {self.config.get('fishing_mode', 'float')}")
            print(f"✓ Цвет поплавка: {self.config.get('float_color', 'red')}")
            
            # Запускаем бота
            self.bot.start()
            
            # Запускаем оверлей
            self._start_overlay()
            
            print("✓ Бот успешно запущен!")
            self.gui.update_status("🎣 Бот работает...", "#00FF00")
            
        except Exception as e:
            print(f"❌ Ошибка при запуске: {e}")
            import traceback
            traceback.print_exc()
            self.gui.update_status(f"❌ Ошибка: {str(e)[:50]}", "#FF0000")

    def stop_bot(self):
        """Stop bot and overlay"""
        print("\n" + "="*60)
        print("⏹  ОСТАНОВКА БОТА")
        print("="*60)
        
        try:
            self.bot.stop()
            
            if self.overlay:
                self.overlay.stop()
                self.overlay = None
            
            print("✓ Бот остановлен")
            self.gui.update_status("⏹  Бот остановлен", "#FF5555")
            
        except Exception as e:
            print(f"❌ Ошибка при остановке: {e}")

    def _start_overlay(self):
        """Start status overlay in separate thread"""
        if self.overlay:
            self.overlay.stop()
        
        try:
            self.overlay = BotOverlay(self.bot)
            overlay_thread = threading.Thread(target=self.overlay.run, daemon=True)
            overlay_thread.start()
            print("✓ Оверлей запущен")
        except Exception as e:
            print(f"⚠️  Не удалось запустить оверлей: {e}")

    def on_close(self):
        """Handle window close"""
        print("\n🔴 Закрытие приложения...")
        try:
            if self.bot.running:
                self.stop_bot()
            if self.overlay:
                self.overlay.stop()
            keyboard.clear_all_hotkeys()
        except:
            pass
        self.root.destroy()

    def run(self):
        self.gui.update_status("✓ Готов. Нажми F6 для запуска", "#00FFAA")
        print("\n" + "="*60)
        print("RF4 AutoFisher запущен!")
        print("="*60)
        print("F6 - Запустить бота")
        print("F7 - Остановить бота")
        print("="*60 + "\n")
        self.root.mainloop()


if __name__ == "__main__":
    app = RF4BotApp()
    app.run()

