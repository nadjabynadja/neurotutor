"""
NeuroTutor - Core Cognitive State Detection

Simulator mode: Webcam-based attention detection using:
- Gaze tracking (dwell time, fixations)
- Facial expression analysis
- Mouse movement patterns
- Keystroke dynamics
"""
import cv2
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import time


@dataclass
class CognitiveState:
    """Represents the current cognitive state of a student."""
    timestamp: datetime
    cognitive_load: float  # 0-1, higher = more overloaded
    attention_level: float  # 0-1, higher = more focused
    engagement: float  # 0-1, higher = more engaged
    confusion_indicator: float  # 0-1, higher = more confused
    fatigue_indicator: float  # 0-1, higher = more fatigued
    is_calibrated: bool = False
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "cognitive_load": self.cognitive_load,
            "attention_level": self.attention_level,
            "engagement": self.engagement,
            "confusion_indicator": self.confusion_indicator,
            "fatigue_indicator": self.fatigue_indicator,
            "is_calibrated": self.is_calibrated
        }


class AttentionDetector:
    """
    Webcam-based attention detection.
    Uses computer vision to detect:
    - Face presence and orientation
    - Eye tracking (gaze direction)
    - Expression analysis (confusion, frustration)
    """
    
    def __init__(self, camera_index: int = 0, use_gpu: bool = False):
        self.camera_index = camera_index
        self.cap = None
        self.use_gpu = use_gpu
        self.baseline_state: Optional[CognitiveState] = None
        self.history: List[CognitiveState] = []
        self.session_start = time.time()
        
        # Detection parameters
        self.face_cascade = None
        self.eye_cascade = None
        self._load_detectors()
    
    def _load_detectors(self):
        """Load OpenCV cascades for face/eye detection."""
        # Use Haar cascades for face detection
        cascade_path = cv2.data.haarcascades
        self.face_cascade = cv2.CascadeClassifier(
            f"{cascade_path}haarcascade_frontalface_default.xml"
        )
        self.eye_cascade = cv2.CascadeClassifier(
            f"{cascade_path}haarcascade_eye.xml"
        )
    
    def start(self) -> bool:
        """Start the webcam capture."""
        self.cap = cv2.VideoCapture(self.camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        return self.cap.isOpened()
    
    def stop(self):
        """Stop the webcam capture."""
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def detect_face(self, frame: np.ndarray) -> tuple:
        """Detect face and return (x, y, w, h) or None."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
        )
        if len(faces) > 0:
            return faces[0]  # Return first face
        return None
    
    def detect_eyes(self, face_gray: np.ndarray) -> list:
        """Detect eyes within a face region."""
        eyes = self.eye_cascade.detectMultiScale(
            face_gray, scaleFactor=1.1, minNeighbors=3
        )
        return eyes
    
    def estimate_gaze(self, eyes: list, face_bbox: tuple) -> float:
        """
        Estimate gaze direction as attention score.
        Returns 0-1, where 1 = looking at screen.
        """
        if len(eyes) == 0:
            return 0.3  # Low attention if no eyes detected
        
        # Simple heuristic: eyes should be roughly centered in face
        face_x, face_y, face_w, face_h = face_bbox
        
        # Check if eyes are roughly in upper half of face (looking at screen)
        eye_centers_y = [y + h/2 for x, y, w, h in eyes]
        avg_eye_y = sum(eye_centers_y) / len(eye_centers_y)
        
        # Eyes in upper 60% of face = looking at screen
        relative_y = avg_eye_y / face_h
        if relative_y < 0.6:
            return 0.9  # Looking at screen
        elif relative_y < 0.8:
            return 0.6  # Possibly looking down
        else:
            return 0.3  # Looking away
    
    def analyze_frame(self, frame: np.ndarray) -> Dict:
        """Analyze a single frame and return attention metrics."""
        result = {
            "face_detected": False,
            "eye_contact": 0.0,
            "face_position": 0.5,  # 0=left, 0.5=center, 1=right
            "brightness": 0.5,
            "motion_detected": False
        }
        
        face_bbox = self.detect_face(frame)
        if face_bbox is not None:
            result["face_detected"] = True
            x, y, w, h = face_bbox
            
            # Face position (centeredness)
            frame_center = frame.shape[1] / 2
            face_center = x + w / 2
            result["face_position"] = abs(face_center - frame_center) / (frame.shape[1] / 2)
            result["face_position"] = 1 - result["face_position"]  # Invert: higher = more centered
            
            # Eye detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_gray = gray[y:y+h, x:x+w]
            eyes = self.detect_eyes(face_gray)
            result["eye_contact"] = self.estimate_gaze(eyes, face_bbox)
        
        # Brightness (could indicate fatigue - low brightness = tired)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        result["brightness"] = np.mean(gray) / 255.0
        
        return result
    
    def get_cognitive_state(self, frame: Optional[np.ndarray] = None) -> CognitiveState:
        """Get the current cognitive state."""
        if frame is None:
            if self.cap is None or not self.cap.isOpened():
                return self._default_state()
            ret, frame = self.cap.read()
            if not ret:
                return self._default_state()
        
        # Analyze frame
        metrics = self.analyze_frame(frame)
        
        # Calculate cognitive state scores
        attention = self._calculate_attention(metrics)
        cognitive_load = self._estimate_cognitive_load(metrics)
        engagement = self._calculate_engagement(metrics)
        confusion = self._detect_confusion(metrics)
        fatigue = self._detect_fatigue()
        
        state = CognitiveState(
            timestamp=datetime.now(),
            cognitive_load=cognitive_load,
            attention_level=attention,
            engagement=engagement,
            confusion_indicator=confusion,
            fatigue_indicator=fatigue,
            is_calibrated=self.baseline_state is not None
        )
        
        self.history.append(state)
        return state
    
    def _default_state(self) -> CognitiveState:
        """Return default state when no data available."""
        return CognitiveState(
            timestamp=datetime.now(),
            cognitive_load=0.5,
            attention_level=0.5,
            engagement=0.5,
            confusion_indicator=0.0,
            fatigue_indicator=0.0,
            is_calibrated=False
        )
    
    def _calculate_attention(self, metrics: Dict) -> float:
        """Calculate attention score from metrics."""
        if not metrics["face_detected"]:
            return 0.2
        
        attention = (
            metrics["eye_contact"] * 0.5 +
            metrics["face_position"] * 0.3 +
            metrics["brightness"] * 0.2
        )
        return min(1.0, attention)
    
    def _estimate_cognitive_load(self, metrics: Dict) -> float:
        """Estimate cognitive load (higher = more overloaded)."""
        # This is a placeholder - real implementation would use
        # temporal patterns, response times, etc.
        if not metrics["face_detected"]:
            return 0.7
        
        # Default to moderate load
        return 0.5
    
    def _calculate_engagement(self, metrics: Dict) -> float:
        """Calculate engagement score."""
        if not metrics["face_detected"]:
            return 0.2
        
        return metrics["eye_contact"] * metrics["face_position"]
    
    def _detect_confusion(self, metrics: Dict) -> float:
        """Detect confusion indicators."""
        # Placeholder - would use expression analysis
        # in a full implementation
        return 0.0
    
    def _detect_fatigue(self) -> float:
        """Detect fatigue based on session duration and patterns."""
        session_duration = time.time() - self.session_start
        
        # Fatigue increases with session length
        if session_duration < 1800:  # < 30 min
            return 0.1
        elif session_duration < 3600:  # < 1 hour
            return 0.3
        elif session_duration < 5400:  # < 1.5 hours
            return 0.6
        else:
            return 0.8
    
    def calibrate(self, duration_seconds: int = 60) -> CognitiveState:
        """
        Calibrate baseline cognitive state.
        Collect data for specified duration and compute baseline.
        """
        print(f"Calibrating for {duration_seconds} seconds...")
        samples = []
        
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            state = self.get_cognitive_state()
            samples.append(state)
            time.sleep(0.5)  # Sample every 500ms
        
        # Compute baseline as average
        self.baseline_state = CognitiveState(
            timestamp=datetime.now(),
            cognitive_load=np.mean([s.cognitive_load for s in samples]),
            attention_level=np.mean([s.attention_level for s in samples]),
            engagement=np.mean([s.engagement for s in samples]),
            confusion_indicator=np.mean([s.confusion_indicator for s in samples]),
            fatigue_indicator=np.mean([s.fatigue_indicator for s in samples]),
            is_calibrated=True
        )
        
        print(f"Calibration complete. Baseline: {self.baseline_state}")
        return self.baseline_state
    
    def get_adaptive_directive(self) -> Dict:
        """
        Get the current adaptive directive based on cognitive state.
        Returns a dict describing how to adapt the LLM response.
        """
        state = self.get_cognitive_state()
        
        # Determine directive based on state
        directives = []
        
        if state.confusion_indicator > 0.6:
            directives.append("simplify")
            directives.append("elaborate")
        elif state.attention_level < 0.4:
            directives.append("encourage")
            directives.append("break")
        elif state.cognitive_load > 0.7:
            directives.append("slow_down")
            directives.append("simplify")
        elif state.fatigue_indicator > 0.6:
            directives.append("break")
            directives.append("summarize")
        
        # Check for flow state (high attention, moderate load)
        if state.attention_level > 0.8 and state.cognitive_load < 0.5:
            directives.append("speed_up")
        
        return {
            "state": state.to_dict(),
            "directives": directives,
            "suggested_action": self._get_suggested_action(directives)
        }
    
    def _get_suggested_action(self, directives: List[str]) -> str:
        """Get human-readable suggested action."""
        if not directives:
            return "Continue as normal"
        
        if "break" in directives:
            return "Suggest a short break"
        if "simplify" in directives:
            return "Simplify the explanation"
        if "speed_up" in directives:
            return "Accelerate the content"
        if "slow_down" in directives:
            return "Slow down and break into steps"
        if "encourage" in directives:
            return "Add encouragement and positive framing"
        
        return "Adjust content based on cognitive state"


def run_attention_detection(duration_seconds: int = 30):
    """Run attention detection for a specified duration."""
    detector = AttentionDetector()
    
    if not detector.start():
        print("Failed to start camera")
        return
    
    print("Starting attention detection. Press 'q' to quit.")
    
    start_time = time.time()
    while time.time() - start_time < duration_seconds:
        ret, frame = detector.cap.read()
        if not ret:
            break
        
        # Get cognitive state
        state = detector.get_cognitive_state(frame)
        
        # Display metrics
        cv2.putText(frame, f"Attention: {state.attention_level:.2f}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Load: {state.cognitive_load:.2f}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Engagement: {state.engagement:.2f}", 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('NeuroTutor - Attention Detection', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    detector.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_attention_detection(duration_seconds=30)
