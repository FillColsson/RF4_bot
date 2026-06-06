"""
Enhanced float fishing with advanced bite detection
"""
import time
import random
import cv2
import numpy as np
from core.fishing_mode import FishingMode
from core.state_machine import FishingState
from vision.float_detectors import HybridFloatDetector


class FloatFishing(FishingMode):
    """Float fishing with advanced float and bite detection"""
    
    def __init__(self, config, vision_engine, input_manager):
        super().__init__(config, vision_engine, input_manager)
        
        self.cast_count = 0
        self.bite_detected = False
        self.float_detector = None
        self.float_info = None
        self.detection_failures = 0
        self.max_detection_failures = 20
        
        self._setup_state_transitions()
    
    def _setup_state_transitions(self):
        """Setup state machine transitions"""
        self.state_machine.add_transition(
            FishingState.IDLE, FishingState.CASTING,
            lambda: self.running,
            self._start_cast
        )
        
        self.state_machine.add_transition(
            FishingState.CASTING, FishingState.WAITING,
            lambda: self.state_machine.get_state_duration() > 1.5,
            self._finish_cast
        )
        
        self.state_machine.add_transition(
            FishingState.WAITING, FishingState.HOOKED,
            lambda: self.bite_detected,
            self._hook_fish
        )
        
        self.state_machine.add_transition(
            FishingState.HOOKED, FishingState.FIGHTING,
            lambda: self.state_machine.get_state_duration() > 0.3,
            self._start_fighting
        )
        
        self.state_machine.add_transition(
            FishingState.FIGHTING, FishingState.COLLECTING,
            lambda: self.state_machine.get_state_duration() > random.uniform(4, 8),
            self._prepare_collection
        )
        
        self.state_machine.add_transition(
            FishingState.COLLECTING, FishingState.CASTING,
            lambda: self.state_machine.get_state_duration() > 2.0,
            self._finish_collection
        )
    
    def setup(self):
        """Setup float fishing"""
        self.logger.info("Float fishing setup")
        
        # Initialize float detector based on configuration
        detection_method = self.config.get("float_detection_method", "hybrid")
        float_color = self.config.get("float_color", "red")
        
        # Initialize detector based on config
        if detection_method == "template_matching":
            try:
                from vision.advanced_detectors import TemplateMatchingFloatDetector
                template_path = self.config.get("advanced_settings", {}).get("template_path")
                if template_path:
                    self.float_detector = TemplateMatchingFloatDetector(template_path)
                    self.logger.info(f"✓ Template Matching detector initialized: {template_path}")
                else:
                    self.logger.warning("Template path not found, using Hybrid")
                    self.float_detector = HybridFloatDetector(target_color=float_color)
            except Exception as e:
                self.logger.error(f"Failed to initialize Template Matching: {e}, using Hybrid")
                self.float_detector = HybridFloatDetector(target_color=float_color)
        
        elif detection_method == "multi_hsv":
            try:
                from vision.advanced_detectors import MultiHSVFloatDetector
                hsv_ranges = self.config.get("advanced_settings", {}).get("multi_hsv_ranges")
                if hsv_ranges:
                    self.float_detector = MultiHSVFloatDetector(hsv_ranges=hsv_ranges)
                    self.logger.info(f"✓ Multi-HSV detector initialized with {len(hsv_ranges)} ranges")
                else:
                    self.float_detector = HybridFloatDetector(target_color=float_color)
            except Exception as e:
                self.logger.error(f"Failed to initialize Multi-HSV: {e}, using Hybrid")
                self.float_detector = HybridFloatDetector(target_color=float_color)
        
        elif detection_method == "adaptive":
            try:
                from vision.advanced_detectors import AdaptiveFloatDetector
                self.float_detector = AdaptiveFloatDetector(target_color=float_color)
                
                # Try to add template if available
                template_path = self.config.get("advanced_settings", {}).get("template_path")
                if template_path:
                    self.float_detector.add_template(template_path)
                
                self.logger.info(f"✓ Adaptive detector initialized (color={float_color})")
            except Exception as e:
                self.logger.error(f"Failed to initialize Adaptive: {e}, using Hybrid")
                self.float_detector = HybridFloatDetector(target_color=float_color)
        
        else:  # Default: hybrid
            self.float_detector = HybridFloatDetector(target_color=float_color)
            self.logger.info(f"✓ Hybrid detector initialized: color={float_color}")
        
        self.logger.info(f"Float fishing mode ready (method={detection_method})")
        
        self.cast_count = 0
        self.detection_failures = 0
        self.state_machine.set_state(FishingState.IDLE)
        
        self.logger.info(f"Float color set to: {float_color}")
    
    def execute_cycle(self):
        """Execute fishing cycle with advanced detection"""
        current_state = self.state_machine.get_current_state()
        
        # Capture frame
        frame = self.vision.capture_screen()
        if frame is None:
            return
        
        # Get detection region
        region = self.config.get("detection_region", {})
        roi = self.vision.crop_region(frame, region)
        
        if roi is None or roi.size == 0:
            self.detection_failures += 1
            if self.detection_failures > self.max_detection_failures:
                self.logger.warning("Detection region invalid or empty!")
            return
        
        # Detect float
        self.float_info = self.float_detector.detect_float(roi)
        
        if self.float_info is None:
            self.detection_failures += 1
            return
        
        self.detection_failures = 0
        
        # Analyze for bite if waiting
        if current_state == FishingState.WAITING:
            bite_result = self.float_detector.detect_bite(
                roi,
                sensitivity=self.config.get("bite_detection_sensitivity", 65) / 100.0
            )
            
            if bite_result['detected']:
                self.logger.info(f"Bite detected! Methods: {bite_result['methods']}")
                self.bite_detected = True
    
    def _start_cast(self):
        """Start casting"""
        self.logger.info(f"Casting #{self.cast_count + 1}")
        cast_power = self.config.get("cast_power", 75)
        
        cast_duration = 0.2 + (cast_power / 100.0) * 0.8
        self.input.press('space', duration=cast_duration)
        
        self.cast_count += 1
    
    def _finish_cast(self):
        """Finish casting"""
        self.logger.info("Cast complete, waiting for bite...")
        cast_delay = self.config.get("cast_delay", 1.2)
        random_delay = cast_delay + random.uniform(-0.3, 0.3)
        self.input.sleep(random_delay)
    
    def _hook_fish(self):
        """Hook the fish"""
        self.logger.info("HOOKING FISH!")
        self.bite_detected = False
        
        self.input.press('space', duration=0.15)
        self.input.sleep(random.uniform(0.2, 0.4))
    
    def _start_fighting(self):
        """Start fighting"""
        self.logger.info("Fighting fish...")
        
        for _ in range(random.randint(2, 4)):
            direction = random.choice(['up', 'down'])
            if direction == 'up':
                self.input.press('w', duration=random.uniform(0.3, 0.6))
            else:
                self.input.press('s', duration=random.uniform(0.3, 0.6))
            self.input.sleep(random.uniform(0.2, 0.5))
    
    def _prepare_collection(self):
        """Prepare for collection"""
        self.logger.info("Fish caught, preparing to collect...")
    
    def _finish_collection(self):
        """Finish collection and repeat"""
        self.logger.info(f"Fish collected! Total catch: {self.cast_count}")
        random_delay = random.uniform(0.8, 1.5)
        self.input.sleep(random_delay)
    
    def cleanup(self):
        """Cleanup"""
        self.logger.info(f"Float fishing stopped. Total casts: {self.cast_count}")

