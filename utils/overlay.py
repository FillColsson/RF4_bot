"""
Оверлей статуса бота
Показывает статус бота поверх игры в реальном времени
"""
import cv2
import mss
import numpy as np
import time
from threading import Event


class BotOverlay:
    """Displays bot status overlay on screen"""
    
    def __init__(self, bot, window_name="RF4 Bot Status"):
        self.bot = bot
        self.window_name = window_name
        self.running = False
        self.stop_event = Event()
        
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1]
    
    def run(self):
        """Main overlay loop"""
        self.running = True
        
        try:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, 400, 200)
            cv2.moveWindow(self.window_name, 10, 10)
            
            print(f"✓ Оверлей запущен на {self.window_name}")
            
            while self.running and not self.stop_event.is_set():
                try:
                    # Создаём фон
                    overlay_frame = np.ones((200, 400, 3), dtype=np.uint8) * 20
                    
                    # Получаем информацию о боте
                    bot_state = self.bot.current_mode.state_machine.get_current_state() if self.bot.current_mode else None
                    cast_count = self.bot.current_mode.cast_count if self.bot.current_mode else 0
                    
                    # Рисуем информацию
                    self._draw_status(overlay_frame, bot_state, cast_count)
                    
                    # Показываем оверлей
                    cv2.imshow(self.window_name, overlay_frame)
                    
                    key = cv2.waitKey(100) & 0xFF
                    if key == 27:  # ESC
                        break
                    
                except Exception as e:
                    print(f"Ошибка в оверлее: {e}")
                    time.sleep(0.1)
            
        except Exception as e:
            print(f"Ошибка при инициализации оверлея: {e}")
        finally:
            self.stop()
    
    def _draw_status(self, frame, state, cast_count):
        """Draw bot status on frame"""
        
        # Заголовок
        cv2.putText(
            frame, "🎣 RF4 AutoFisher", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2
        )
        
        # Статус
        status_text = f"Status: {state.name if state else 'IDLE'}"
        status_color = self._get_status_color(state)
        cv2.putText(
            frame, status_text, (10, 65),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2
        )
        
        # Забросы
        casts_text = f"Casts: {cast_count}"
        cv2.putText(
            frame, casts_text, (10, 100),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1
        )
        
        # Время работы
        uptime = time.time() - (self.bot.start_time if hasattr(self.bot, 'start_time') else time.time())
        uptime_text = f"Uptime: {int(uptime)}s"
        cv2.putText(
            frame, uptime_text, (10, 135),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1
        )
        
        # Подсказка
        cv2.putText(
            frame, "ESC - Close", (10, 170),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1
        )
    
    def _get_status_color(self, state):
        """Get color based on state"""
        if state is None:
            return (100, 100, 100)  # Grey
        
        state_name = state.name.lower()
        
        if "idle" in state_name:
            return (100, 100, 100)  # Grey
        elif "casting" in state_name:
            return (0, 255, 255)  # Cyan
        elif "waiting" in state_name:
            return (0, 165, 255)  # Orange
        elif "hooked" in state_name or "fighting" in state_name:
            return (0, 0, 255)  # Red
        elif "collecting" in state_name:
            return (0, 255, 0)  # Green
        else:
            return (200, 200, 200)  # White
    
    def stop(self):
        """Stop overlay"""
        self.running = False
        self.stop_event.set()
        
        try:
            cv2.destroyAllWindows()
            print("✓ Оверлей остановлен")
        except:
            pass


class AdvancedOverlay(BotOverlay):
    """Advanced overlay with more information"""
    
    def _draw_status(self, frame, state, cast_count):
        """Draw advanced status with graphics"""
        
        # Фон с полупрозрачностью
        cv2.rectangle(frame, (0, 0), (400, 200), (40, 40, 40), -1)
        cv2.rectangle(frame, (0, 0), (400, 200), (0, 255, 0), 2)
        
        # Заголовок
        cv2.putText(
            frame, "RF4 AutoFisher v1.0", (15, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
        )
        
        # Статус с полосой
        status_text = f"Status: {state.name if state else 'IDLE'}"
        status_color = self._get_status_color(state)
        
        # Полоса статуса
        cv2.rectangle(frame, (15, 35), (390, 45), (50, 50, 50), -1)
        cv2.rectangle(frame, (15, 35), (390, 45), status_color, 2)
        cv2.putText(
            frame, status_text, (20, 42),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1
        )
        
        # Информация
        y_offset = 60
        
        info_items = [
            f"Забросов: {cast_count}",
            f"FPS: ~20",
            f"Ловля: Поплавочная",
            f"F7 - Стоп | ESC - Закрыть оверлей"
        ]
        
        for i, text in enumerate(info_items):
            cv2.putText(
                frame, text, (20, y_offset + i * 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1
            )
        
        # Нижняя полоса
        cv2.line(frame, (10, 190), (390, 190), (0, 255, 0), 1)


class MinimalOverlay(BotOverlay):
    """Minimal overlay - just essential info"""
    
    def run(self):
        """Run minimal overlay"""
        self.running = True
        
        try:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, 300, 80)
            cv2.moveWindow(self.window_name, 1620, 1000)  # Bottom right
            
            print(f"✓ Минимальный оверлей запущен")
            
            while self.running and not self.stop_event.is_set():
                try:
                    overlay_frame = np.zeros((80, 300, 3), dtype=np.uint8)
                    
                    state = self.bot.current_mode.state_machine.get_current_state() if self.bot.current_mode else None
                    status_color = self._get_status_color(state)
                    
                    # Минимальная информация
                    cv2.putText(
                        overlay_frame, f"Status: {state.name if state else 'IDLE'}", (5, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2
                    )
                    
                    cv2.putText(
                        overlay_frame, "F7 - Stop | ESC - Close", (5, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1
                    )
                    
                    cv2.imshow(self.window_name, overlay_frame)
                    
                    key = cv2.waitKey(100) & 0xFF
                    if key == 27:
                        break
                    
                except:
                    time.sleep(0.1)
        
        finally:
            self.stop()
