"""
State Machine for fishing bot
Manages state transitions and actions
"""
from enum import Enum
import time


class FishingState(Enum):
    """Possible bot states"""
    IDLE = "idle"
    CASTING = "casting"
    WAITING = "waiting"
    HOOKED = "hooked"
    FIGHTING = "fighting"
    COLLECTING = "collecting"
    ERROR = "error"


class StateMachine:
    """Manages bot state transitions"""
    
    def __init__(self, initial_state=FishingState.IDLE):
        self.current_state = initial_state
        self.previous_state = None
        self.state_start_time = time.time()
        self.transitions = {}
        self.on_state_change = None
    
    def add_transition(self, from_state, to_state, condition=None, action=None):
        """Add a state transition"""
        if from_state not in self.transitions:
            self.transitions[from_state] = []
        
        self.transitions[from_state].append({
            'to': to_state,
            'condition': condition,
            'action': action
        })
    
    def set_state(self, new_state, action=None):
        """Set state directly"""
        if new_state != self.current_state:
            self.previous_state = self.current_state
            self.current_state = new_state
            self.state_start_time = time.time()
            
            if action:
                action()
            
            if self.on_state_change:
                self.on_state_change(self.previous_state, new_state)
    
    def try_transition(self):
        """Try to transition based on conditions"""
        if self.current_state not in self.transitions:
            return False
        
        for transition in self.transitions[self.current_state]:
            condition = transition['condition']
            
            if condition is None or condition():
                self.set_state(transition['to'], transition['action'])
                return True
        
        return False
    
    def get_current_state(self):
        """Get current state"""
        return self.current_state
    
    def get_state_duration(self):
        """Get how long in current state"""
        return time.time() - self.state_start_time
    
    def reset(self):
        """Reset to idle state"""
        self.set_state(FishingState.IDLE)
