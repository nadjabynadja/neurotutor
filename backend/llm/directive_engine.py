"""
NeuroTutor - LLM Directive Engine

Maps cognitive state to LLM prompt directives.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class Directive(Enum):
    """Available adaptation directives."""
    SIMPLIFY = "simplify"
    ELABORATE = "elaborate"
    SLOW_DOWN = "slow_down"
    SPEED_UP = "speed_up"
    ENCOURAGE = "encourage"
    BREAK = "break"
    SUMMARIZE = "summarize"
    INTERACTIVE = "interactive"
    EXAMPLE = "example"
    ANALOGY = "analogy"


# Directive descriptions for LLM prompts
DIRECTIVE_DESCRIPTIONS = {
    Directive.SIMPLIFY: "Use simpler language, shorter sentences. Avoid jargon.",
    Directive.ELABORATE: "Add detailed examples and analogies to explain concepts.",
    Directive.SLOW_DOWN: "Break into smaller, more manageable steps.",
    Directive.SPEED_UP: "Move faster through basics. The user is grasping this quickly.",
    Directive.ENCOURAGE: "Add positive framing and motivational language.",
    Directive.BREAK: "Suggest a 5-minute break. The user shows signs of fatigue.",
    Directive.SUMMARIZE: "Provide a brief summary before continuing.",
    Directive.INTERACTIVE: "Add interactive elements like questions or exercises.",
    Directive.EXAMPLE: "Include concrete examples to illustrate the concept.",
    Directive.ANALOGY: "Use relatable analogies to explain the concept.",
}


@dataclass
class CognitiveState:
    """Simplified cognitive state for directive mapping."""
    cognitive_load: float  # 0-1
    attention_level: float  # 0-1
    engagement: float  # 0-1
    confusion_indicator: float  # 0-1
    fatigue_indicator: float  # 0-1


class DirectiveEngine:
    """
    Maps cognitive states to LLM directives.
    
    Decision logic:
    - High confusion (>0.6) → simplify, elaborate
    - Low attention (<0.4) → encourage, break
    - High cognitive load (>0.7) → slow_down, simplify
    - High fatigue (>0.6) → break, summarize
    - Flow state (high attention, moderate load) → speed_up
    """
    
    # Thresholds
    HIGH_CONFUSION = 0.6
    LOW_ATTENTION = 0.4
    HIGH_LOAD = 0.7
    HIGH_FATIGUE = 0.6
    FLOW_ATTENTION = 0.8
    FLOW_LOAD_MAX = 0.5
    
    def __init__(self):
        self.current_directives: List[Directive] = []
        self.directive_history: List[Dict] = []
    
    def get_directives(self, state: CognitiveState) -> List[Directive]:
        """Get directives based on current cognitive state."""
        directives = []
        
        # Confusion detection
        if state.confusion_indicator > self.HIGH_CONFUSION:
            directives.append(Directive.SIMPLIFY)
            directives.append(Directive.ELABORATE)
        
        # Attention issues
        if state.attention_level < self.LOW_ATTENTION:
            directives.append(Directive.ENCOURAGE)
            # Only suggest break if also fatigued
            if state.fatigue_indicator > self.HIGH_FATIGUE:
                directives.append(Directive.BREAK)
        
        # Cognitive overload
        if state.cognitive_load > self.HIGH_LOAD:
            directives.append(Directive.SLOW_DOWN)
            directives.append(Directive.SIMPLIFY)
        
        # Fatigue
        if state.fatigue_indicator > self.HIGH_FATIGUE:
            directives.append(Directive.BREAK)
            directives.append(Directive.SUMMARIZE)
        
        # Flow state - user is doing well
        if (state.attention_level > self.FLOW_ATTENTION and 
            state.cognitive_load < self.FLOW_LOAD_MAX):
            directives.append(Directive.SPEED_UP)
        
        # Default: add examples for engagement
        if state.engagement < 0.5 and len(directives) == 0:
            directives.append(Directive.EXAMPLE)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_directives = []
        for d in directives:
            if d not in seen:
                seen.add(d)
                unique_directives.append(d)
        
        self.current_directives = unique_directives
        return unique_directives
    
    def build_prompt_prefix(self, directives: List[Directive]) -> str:
        """Build a prompt prefix from directives."""
        if not directives:
            return ""
        
        instructions = [
            DIRECTIVE_DESCRIPTIONS.get(d, str(d.value)) 
            for d in directives
        ]
        
        return "[ADAPTATION: " + " ".join(instructions) + "] "
    
    def build_system_prompt(self, state: CognitiveState) -> str:
        """Build a complete system prompt with current directives."""
        directives = self.get_directives(state)
        
        base_prompt = """You are NeuroTutor, an AI teaching assistant that adapts to students' cognitive states in real-time.

Your teaching style should:
- Match the student's current understanding level
- Adjust difficulty based on their cognitive load
- Keep them engaged and motivated
- Recognize when they need a break"""

        adaptation = self.build_prompt_prefix(directives)
        
        return base_prompt + "\n\n" + adaptation
    
    def adapt_response(self, base_response: str, state: CognitiveState) -> str:
        """
        Adapt a base LLM response based on cognitive state.
        This is a simple implementation - could be enhanced with
        more sophisticated prompt engineering.
        """
        directives = self.get_directives(state)
        
        if not directives:
            return base_response
        
        # Track directive usage
        self.directive_history.append({
            "state": {
                "cognitive_load": state.cognitive_load,
                "attention_level": state.attention_level,
                "engagement": state.engagement,
                "confusion": state.confusion_indicator,
                "fatigue": state.fatigue_indicator
            },
            "directives": [d.value for d in directives]
        })
        
        # Add prefix to response (the actual adaptation happens via prompt)
        # In a real implementation, this would reconstruct the response
        # based on the directives
        return self.build_prompt_prefix(directives) + base_response
    
    def get_suggested_action(self) -> str:
        """Get human-readable suggested action for the UI."""
        if not self.current_directives:
            return "Continue as normal"
        
        # Priority ordering
        if Directive.BREAK in self.current_directives:
            return "Suggest a short break"
        if Directive.SIMPLIFY in self.current_directives:
            return "Simplify the explanation"
        if Directive.SPEED_UP in self.current_directives:
            return "Accelerate the content"
        if Directive.SLOW_DOWN in self.current_directives:
            return "Break into smaller steps"
        if Directive.ENCOURAGE in self.current_directives:
            return "Add encouragement"
        
        return "Adjust based on cognitive state"


class DirectiveMapper:
    """
    Maps cognitive states to structured directive objects
    for downstream processing.
    """
    
    @staticmethod
    def to_llm_directives(state: CognitiveState) -> Dict:
        """Convert cognitive state to LLM-compatible directive format."""
        engine = DirectiveEngine()
        directives = engine.get_directives(state)
        
        return {
            "directives": [d.value for d in directives],
            "prompt_prefix": engine.build_prompt_prefix(directives),
            "teaching_tone": DirectiveMapper._get_teaching_tone(directives),
            "content_pacing": DirectiveMapper._get_pacing(directives),
            "suggested_break": Directive.BREAK in directives
        }
    
    @staticmethod
    def _get_teaching_tone(directives: List[Directive]) -> str:
        """Determine teaching tone based on directives."""
        if Directive.ENCOURAGE in directives:
            return "supportive"
        if Directive.SIMPLIFY in directives:
            return "clear"
        if Directive.SPEED_UP in directives:
            return "fast-paced"
        return "balanced"
    
    @staticmethod
    def _get_pacing(directives: List[Directive]) -> str:
        """Determine content pacing."""
        if Directive.SPEED_UP in directives:
            return "fast"
        if Directive.SLOW_DOWN in directives:
            return "slow"
        return "normal"


# Example usage
if __name__ == "__main__":
    # Test with various cognitive states
    engine = DirectiveEngine()
    
    test_states = [
        CognitiveState(0.8, 0.3, 0.4, 0.7, 0.2),  # Confused, low attention
        CognitiveState(0.3, 0.9, 0.8, 0.1, 0.1),  # Flow state
        CognitiveState(0.7, 0.5, 0.5, 0.3, 0.8),  # Fatigued
        CognitiveState(0.5, 0.5, 0.5, 0.2, 0.2),  # Normal
    ]
    
    for state in test_states:
        directives = engine.get_directives(state)
        print(f"\nState: load={state.cognitive_load}, "
              f"attention={state.attention_level}, "
              f"fatigue={state.fatigue_indicator}")
        print(f"Directives: {[d.value for d in directives]}")
        print(f"Action: {engine.get_suggested_action()}")
