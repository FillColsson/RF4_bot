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
                    status = self.bot.current_mode.get_status() if self.bot.current_mode else {}
                    cast_count = status.get("casts", getattr(self.bot.current_mode, "cast_count", 0))
                    catch_count = status.get("catches", 0)
                    vision_phase = status.get("vision_phase", "—")
                    
                    self._draw_status(overlay_frame, bot_state, cast_count, catch_count, vision_phase)
                    
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
    
    def _draw_status(self, frame, state, cast_count, catch_count=0, vision_phase="—"):
        """Draw bot status on frame"""
        
        cv2.putText(
            frame, "RF4 AutoFisher", (10, 28),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2
        )
        
        status_text = f"Bot: {state.name if state else 'IDLE'}"
        status_color = self._get_status_color(state)
        cv2.putText(
            frame, status_text, (10, 58),
            cv2.FONT_HERSHEY_SIMPLEX, 0.65, status_color, 2
        )

        cv2.putText(
            frame, f"Vision: {vision_phase}", (10, 82),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 220, 255), 1
        )
        
        cv2.putText(
            frame, f"Casts: {cast_count}  Catches: {catch_count}", (10, 108),
            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 200, 200), 1
        )
        
        uptime = time.time() - (self.bot.start_time if hasattr(self.bot, 'start_time') else time.time())
        cv2.putText(
            frame, f"Uptime: {int(uptime)}s", (10, 132),
            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 200, 200), 1
        )
        
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
