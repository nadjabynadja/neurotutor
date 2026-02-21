"""
NeuroTutor - MiniMax LLM Integration
"""
import os
import json
import requests
from typing import Optional, List, Dict
from dataclasses import dataclass


MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = "https://api.minimax.io/v1"


@dataclass
class Message:
    role: str
    content: str


class MiniMaxClient:
    """Client for MiniMax Chat API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or MINIMAX_API_KEY
        self.base_url = MINIMAX_BASE_URL
    
    def chat(
        self,
        messages: List[Message],
        model: str = "MiniMax-M2.5",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None
    ) -> str:
        """Send a chat request to MiniMax."""
        
        # Build the messages payload
        payload_messages = []
        
        if system_prompt:
            payload_messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        for msg in messages:
            payload_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": payload_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(
            f"{self.base_url}/text/chatcompletion_v2",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"MiniMax API error: {response.status_code} - {response.text}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)


class NeuroTutorLLM:
    """NeuroTutor's LLM wrapper with cognitive state adaptation."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = MiniMaxClient(api_key)
    
    def generate_response(
        self,
        user_message: str,
        cognitive_state: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Generate an adaptive response based on cognitive state.
        """
        # Build system prompt based on cognitive state
        system_prompt = self._build_system_prompt(cognitive_state)
        
        # Add context if provided
        if context:
            context_str = f"\n\nContext: {json.dumps(context)}"
            user_message = user_message + context_str
        
        messages = [
            Message(role="user", content=user_message)
        ]
        
        # Check if MiniMax is configured
        if not self.client.is_configured():
            return {
                "response": "MiniMax API key not configured. Set MINIMAX_API_KEY environment variable.",
                "error": "no_api_key",
                "directives": []
            }
        
        try:
            response = self.client.chat(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2048
            )
            
            return {
                "response": response,
                "directives": self._get_directives(cognitive_state),
                "cognitive_state": cognitive_state
            }
        except Exception as e:
            return {
                "response": f"Error generating response: {str(e)}",
                "error": str(e),
                "directives": [],
                "cognitive_state": cognitive_state
            }
    
    def _build_system_prompt(self, state: Optional[Dict]) -> str:
        """Build the system prompt based on cognitive state."""
        
        base_prompt = """You are NeuroTutor, an AI teaching assistant that adapts to students' cognitive states in real-time.

Your teaching style should:
- Match the student's current understanding level
- Adjust difficulty based on their cognitive load
- Keep them engaged and motivated
- Recognize when they need a break
- Always be encouraging and patient"""
        
        if not state:
            return base_prompt
        
        # Add adaptations based on cognitive state
        cognitive_load = state.get("cognitive_load", 0.5)
        attention = state.get("attention_level", 0.5)
        confusion = state.get("confusion_indicator", 0.0)
        fatigue = state.get("fatigue_indicator", 0.0)
        
        adaptations = []
        
        if cognitive_load > 0.7:
            adaptations.append("- The student has HIGH cognitive load - simplify explanations significantly, use shorter sentences")
        elif cognitive_load < 0.3:
            adaptations.append("- The student has LOW cognitive load - you can introduce more advanced concepts")
        
        if attention < 0.4:
            adaptations.append("- The student has LOW attention - add engaging elements, ask questions")
        
        if confusion > 0.6:
            adaptations.append("- The student is CONFUSED - re-explain from basics, use concrete examples")
        
        if fatigue > 0.6:
            adaptations.append("- The student shows signs of FATIGUE - suggest breaks, keep content lighter")
        
        if attention > 0.8 and cognitive_load < 0.5:
            adaptations.append("- The student is in FLOW state - you can accelerate and challenge them")
        
        if adaptations:
            return base_prompt + "\n\n" + "\n".join(adaptations)
        
        return base_prompt
    
    def _get_directives(self, state: Optional[Dict]) -> List[str]:
        """Extract directives from cognitive state."""
        if not state:
            return []
        
        directives = []
        
        if state.get("confusion_indicator", 0) > 0.6:
            directives.extend(["simplify", "elaborate"])
        
        if state.get("attention_level", 0.5) < 0.4:
            directives.append("encourage")
        
        if state.get("cognitive_load", 0.5) > 0.7:
            directives.extend(["slow_down", "simplify"])
        
        if state.get("fatigue_indicator", 0) > 0.6:
            directives.extend(["break", "summarize"])
        
        if state.get("attention_level", 0) > 0.8 and state.get("cognitive_load", 0.5) < 0.5:
            directives.append("speed_up")
        
        return list(set(directives))


# Test function
if __name__ == "__main__":
    import sys
    
    llm = NeuroTutorLLM()
    
    if not llm.client.is_configured():
        print("❌ MINIMAX_API_KEY not set")
        print("Usage: MINIMAX_API_KEY=your_key python minimax_client.py")
        sys.exit(1)
    
    print("✅ MiniMax configured, testing...")
    
    # Test normal state
    result = llm.generate_response(
        "Explain what a neural network is",
        cognitive_state={
            "cognitive_load": 0.3,
            "attention_level": 0.8,
            "engagement": 0.7,
            "confusion_indicator": 0.1,
            "fatigue_indicator": 0.1
        }
    )
    print("\n📝 Normal state response:")
    print(result["response"][:500] if len(result["response"]) > 500 else result["response"])
    
    # Test confused state
    result = llm.generate_response(
        "I don't understand recursion",
        cognitive_state={
            "cognitive_load": 0.8,
            "attention_level": 0.3,
            "engagement": 0.4,
            "confusion_indicator": 0.8,
            "fatigue_indicator": 0.2
        }
    )
    print("\n📝 Confused state response:")
    print(result["response"][:500] if len(result["response"]) > 500 else result["response"])
    print(f"Directives: {result['directives']}")
