"""
NeuroTutor - Webcam Simulator

Simulates webcam input for testing attention detection without hardware.
Uses synthetic data with configurable patterns.
"""
import time
import random
import threading
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import numpy as np


@dataclass
class SimulatedCognitiveState:
    """Simulated cognitive state with realistic variations."""
    timestamp: datetime
    cognitive_load: float
    attention_level: float
    engagement: float
    confusion_indicator: float
    fatigue_indicator: float
    face_detected: bool = True
    is_calibrated: bool = False


class WebcamSimulator:
    """
    Simulates webcam-based attention detection.
    
    Useful for:
    - Testing without webcam hardware
    - Demoing the system
    - Generating synthetic data for development
    """
    
    def __init__(self):
        self.is_running = False
        self.session_start = time.time()
        self.baseline: Optional[SimulatedCognitiveState] = None
        
        # Simulation parameters
        self.session_duration = 0
        self.target_attention = 0.7
        self.target_load = 0.5
        self.confusion_events = []
        self.attention_dips = []
        
        # Callback for state updates
        self.on_state_update: Optional[Callable] = None
        
        # Current state
        self._current_state = self._generate_state()
        self._lock = threading.Lock()
    
    def start(self) -> bool:
        """Start the simulator."""
        self.is_running = True
        self.session_start = time.time()
        self._current_state = self._generate_state()
        return True
    
    def stop(self):
        """Stop the simulator."""
        self.is_running = False
    
    def calibrate(self, duration_seconds: int = 60) -> SimulatedCognitiveState:
        """Simulate calibration period."""
        samples = []
        for _ in range(duration_seconds // 2):
            samples.append(self._generate_state())
            time.sleep(0.5)
        
        self.baseline = SimulatedCognitiveState(
            timestamp=datetime.now(),
            cognitive_load=sum(s.cognitive_load for s in samples) / len(samples),
            attention_level=sum(s.attention_level for s in samples) / len(samples),
            engagement=sum(s.engagement for s in samples) / len(samples),
            confusion_indicator=sum(s.confusion_indicator for s in samples) / len(samples),
            fatigue_indicator=sum(s.fatigue_indicator for s in samples) / len(samples),
            is_calibrated=True
        )
        
        self._current_state = self.baseline
        return self.baseline
    
    def _generate_state(self) -> SimulatedCognitiveState:
        """Generate a realistic cognitive state."""
        session_duration = time.time() - self.session_start
        
        # Base values with some randomness
        attention = self.target_attention + random.uniform(-0.15, 0.15)
        load = self.target_load + random.uniform(-0.15, 0.15)
        engagement = (attention + load) / 2 + random.uniform(-0.1, 0.1)
        
        # Add attention dips
        for dip_start, dip_duration in self.attention_dips:
            if session_duration >= dip_start and session_duration < dip_start + dip_duration:
                attention *= 0.5
                engagement *= 0.6
        
        # Add confusion events
        confusion = 0.0
        for event_time, duration in self.confusion_events:
            if session_duration >= event_time and session_duration < event_time + duration:
                confusion = 0.8 + random.uniform(0, 0.2)
                attention *= 0.6
                engagement *= 0.5
        
        # Fatigue increases over time
        if session_duration > 1800:  # 30 minutes
            fatigue = min(0.8, (session_duration - 1800) / 3600)
        elif session_duration > 900:  # 15 minutes
            fatigue = min(0.4, (session_duration - 900) / 1800)
        else:
            fatigue = 0.1 + random.uniform(-0.05, 0.05)
        
        # Clamp values
        attention = max(0, min(1, attention))
        load = max(0, min(1, load))
        engagement = max(0, min(1, engagement))
        confusion = max(0, min(1, confusion))
        fatigue = max(0, min(1, fatigue))
        
        return SimulatedCognitiveState(
            timestamp=datetime.now(),
            cognitive_load=load,
            attention_level=attention,
            engagement=engagement,
            confusion_indicator=confusion,
            fatigue_indicator=fatigue,
            face_detected=True,
            is_calibrated=self.baseline is not None
        )
    
    def get_state(self) -> SimulatedCognitiveState:
        """Get current simulated state."""
        with self._lock:
            self._current_state = self._generate_state()
            return self._current_state
    
    def get_state_dict(self) -> Dict:
        """Get current state as dictionary."""
        state = self.get_state()
        return {
            "timestamp": state.timestamp.isoformat(),
            "cognitive_load": state.cognitive_load,
            "attention_level": state.attention_level,
            "engagement": state.engagement,
            "confusion_indicator": state.confusion_indicator,
            "fatigue_indicator": state.fatigue_indicator,
            "face_detected": state.face_detected,
            "is_calibrated": state.is_calibrated
        }
    
    # ============== Scenario Helpers ==============
    
    def set_attention_level(self, level: float):
        """Set target attention level (0-1)."""
        self.target_attention = max(0, min(1, level))
    
    def set_cognitive_load(self, load: float):
        """Set target cognitive load (0-1)."""
        self.target_load = max(0, min(1, load))
    
    def trigger_attention_dip(self, duration_seconds: int = 30):
        """Trigger an attention dip after a short delay."""
        delay = random.randint(5, 15)
        start_time = time.time() - self.session_start + delay
        self.attention_dips.append((start_time, duration_seconds))
    
    def trigger_confusion_event(self, duration_seconds: int = 60):
        """Trigger a confusion event after a short delay."""
        delay = random.randint(5, 20)
        start_time = time.time() - self.session_start + delay
        self.confusion_events.append((start_time, duration_seconds))
    
    def simulate_struggling_student(self):
        """Configure for a struggling student scenario."""
        self.target_attention = 0.35
        self.target_load = 0.85
        self.trigger_confusion_event(120)
        self.trigger_attention_dip(45)
    
    def simulate_engaged_student(self):
        """Configure for an engaged student scenario."""
        self.target_attention = 0.85
        self.target_load = 0.45
    
    def simulate_fatigued_student(self):
        """Configure for a fatigued student scenario."""
        self.target_attention = 0.5
        self.target_load = 0.6
        # Fatigue will naturally increase over time
    
    def simulate_flow_state(self):
        """Configure for flow state (optimal learning)."""
        self.target_attention = 0.9
        self.target_load = 0.4
    
    def reset(self):
        """Reset simulator to defaults."""
        self.baseline = None
        self.session_start = time.time()
        self.confusion_events = []
        self.attention_dips = []
        self.target_attention = 0.7
        self.target_load = 0.5
        self._current_state = self._generate_state()


class ScenarioGenerator:
    """Generate test scenarios for demos and testing."""
    
    SCENARIOS = {
        "normal": {
            "description": "Normal learning session",
            "attention": 0.7,
            "load": 0.5
        },
        "struggling": {
            "description": "Student struggling with content",
            "attention": 0.35,
            "load": 0.85,
            "confusion": True
        },
        "engaged": {
            "description": "Highly engaged student",
            "attention": 0.85,
            "load": 0.45
        },
        "flow": {
            "description": "Flow state - optimal learning",
            "attention": 0.9,
            "load": 0.4
        },
        "fatigued": {
            "description": "Student getting tired",
            "attention": 0.5,
            "load": 0.6,
            "fatigue_accelerates": True
        },
        "distracted": {
            "description": "Student easily distracted",
            "attention": 0.4,
            "load": 0.5,
            "attention_dips": True
        },
        "confused": {
            "description": "Student clearly confused",
            "attention": 0.3,
            "load": 0.75,
            "confusion": True
        }
    }
    
    @classmethod
    def apply_scenario(cls, simulator: WebcamSimulator, scenario_name: str):
        """Apply a predefined scenario to a simulator."""
        if scenario_name not in cls.SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        scenario = cls.SCENARIOS[scenario_name]
        
        simulator.target_attention = scenario.get("attention", 0.7)
        simulator.target_load = scenario.get("load", 0.5)
        
        if scenario.get("confusion"):
            simulator.trigger_confusion_event(120)
        
        if scenario.get("attention_dips"):
            simulator.trigger_attention_dip(30)
    
    @classmethod
    def list_scenarios(cls) -> Dict:
        """List all available scenarios."""
        return {name: info["description"] for name, info in cls.SCENARIOS.items()}


# Demo function
if __name__ == "__main__":
    print("🎭 Webcam Simulator Demo")
    print("=" * 50)
    
    # Create simulator
    sim = WebcamSimulator()
    sim.start()
    
    print("\n📊 Scenario 1: Normal student")
    print("-" * 30)
    for i in range(5):
        state = sim.get_state()
        print(f"  Attention: {state.attention_level:.2f} | "
              f"Load: {state.cognitive_load:.2f} | "
              f"Engagement: {state.engagement:.2f}")
        time.sleep(1)
    
    print("\n📊 Scenario 2: Struggling student")
    print("-" * 30)
    sim.simulate_struggling_student()
    for i in range(5):
        state = sim.get_state()
        print(f"  Attention: {state.attention_level:.2f} | "
              f"Load: {state.cognitive_load:.2f} | "
              f"Confusion: {state.confusion_indicator:.2f}")
        time.sleep(1)
    
    print("\n📊 Scenario 3: Flow state")
    print("-" * 30)
    sim.simulate_flow_state()
    for i in range(5):
        state = sim.get_state()
        print(f"  Attention: {state.attention_level:.2f} | "
              f"Load: {state.cognitive_load:.2f}")
        time.sleep(1)
    
    print("\n✅ Demo complete!")
