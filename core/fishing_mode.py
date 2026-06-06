"""
Base class for fishing modes
"""
from abc import ABC, abstractmethod
from core.state_machine import StateMachine, FishingState
from utils.logger import BotLogger


class FishingMode(ABC):
    """Abstract base class for all fishing modes"""
    
    def __init__(self, config, vision_engine, input_manager):
        self.config = config
        self.vision = vision_engine
        self.input = input_manager
        self.logger = BotLogger(name=self.__class__.__name__)
        self.state_machine = StateMachine()
        self.running = False
    
    @abstractmethod
    def setup(self):
        """Setup mode specific parameters"""
        pass
    
    @abstractmethod
    def execute_cycle(self):
        """Execute one fishing cycle"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Cleanup when fishing stops"""
        pass
    
    def start(self):
        """Start fishing"""
        self.running = True
        self.logger.info(f"Starting {self.__class__.__name__}")
        self.setup()
    
    def stop(self):
        """Stop fishing"""
        self.running = False
        self.logger.info(f"Stopping {self.__class__.__name__}")
        self.cleanup()
    
    def update(self):
        """Update fishing state"""
        if self.running:
            try:
                self.state_machine.try_transition()
                self.execute_cycle()
            except Exception as e:
                self.logger.error(f"Error in fishing cycle: {e}")
                self.state_machine.set_state(FishingState.ERROR)
    
    def get_status(self):
        """Get current fishing status"""
        return {
            'mode': self.__class__.__name__,
            'state': self.state_machine.get_current_state().value,
            'running': self.running
        }
