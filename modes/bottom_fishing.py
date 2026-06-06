"""
Bottom fishing mode - Донная ловля (заготовка)
"""
from core.fishing_mode import FishingMode
from core.state_machine import FishingState


class BottomFishing(FishingMode):
    """Bottom fishing implementation (WIP)"""
    
    def setup(self):
        self.logger.info("Bottom fishing setup")
        self.state_machine.set_state(FishingState.IDLE)
    
    def execute_cycle(self):
        self.logger.info("Bottom fishing cycle")
    
    def on_bite_detected(self):
        self.logger.info("Bite detected in bottom mode")
    
    def cleanup(self):
        self.logger.info("Bottom fishing stopped")
