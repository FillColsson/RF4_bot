"""
Spinning mode - Спиннинг (заготовка)
"""
from core.fishing_mode import FishingMode
from core.state_machine import FishingState


class SpinningFishing(FishingMode):
    """Spinning fishing implementation (WIP)"""
    
    def setup(self):
        self.logger.info("Spinning fishing setup")
        self.state_machine.set_state(FishingState.IDLE)
    
    def execute_cycle(self):
        self.logger.info("Spinning cycle")
    
    def cleanup(self):
        self.logger.info("Spinning fishing stopped")
