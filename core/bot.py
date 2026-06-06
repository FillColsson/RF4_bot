"""
Main RF4 Bot - Coordinates all fishing modes
"""
import threading
import time
from vision.vision_engine import VisionEngine
from input.input_manager import InputManager
from modes.float_fishing import FloatFishing
from modes.spinning import SpinningFishing
from modes.bottom_fishing import BottomFishing
from utils.logger import BotLogger


class RF4Bot:
    """Main bot class"""
    
    MODES = {
        "float": FloatFishing,
        "spinning": SpinningFishing,
        "bottom": BottomFishing,
    }
    
    def __init__(self, config, gui):
        self.config = config
        self.gui = gui
        self.logger = BotLogger(name="RF4Bot")
        
        # Initialize components
        self.vision = VisionEngine(config)
        self.input_manager = InputManager()
        
        # Current mode
        self.current_mode = None
        self.running = False
        self.bot_thread = None
    
    def start(self):
        """Start the bot"""
        if self.running:
            self.logger.warning("Bot already running!")
            return
        
        self.running = True
        self.bot_thread = threading.Thread(target=self._run, daemon=True)
        self.bot_thread.start()
        self.logger.info("Bot started")
        self.gui.update_status("🎣 Бот работает...", "#00FF00")
    
    def stop(self):
        """Stop the bot"""
        if not self.running:
            return
        
        self.running = False
        if self.current_mode:
            self.current_mode.stop()
        
        if self.bot_thread:
            self.bot_thread.join(timeout=5)
        
        self.logger.info("Bot stopped")
    
    def set_mode(self, mode_name):
        """Change fishing mode"""
        if mode_name not in self.MODES:
            self.logger.error(f"Unknown mode: {mode_name}")
            return
        
        if self.current_mode:
            self.current_mode.stop()
        
        mode_class = self.MODES[mode_name]
        self.current_mode = mode_class(self.config, self.vision, self.input_manager)
        self.logger.info(f"Mode changed to: {mode_name}")
    
    def update_config(self, config):
        """Update bot configuration"""
        self.config = config
        self.vision.config = config
        if self.current_mode:
            self.current_mode.config = config
        self.logger.info("Config updated")
    
    def _run(self):
        """Main bot loop"""
        try:
            if not self.current_mode:
                self.set_mode("float")
            
            self.current_mode.start()
            
            while self.running:
                if self.current_mode:
                    self.current_mode.update()
                
                time.sleep(0.05)
        
        except Exception as e:
            self.logger.error(f"Bot error: {e}")
            self.gui.update_status(f"Ошибка: {str(e)}", "#FF5555")
        
        finally:
            self.running = False
            if self.current_mode:
                self.current_mode.stop()
    
    def get_status(self):
        """Get bot status"""
        if self.current_mode:
            return self.current_mode.get_status()
        return {
            'mode': 'None',
            'state': 'idle',
            'running': self.running
        }
