"""
LLM Client for KFUPM Course Advisor Agent.
Interfaces with vLLM-served Qwen model via OpenAI-compatible API.
"""

import json
import re
from typing import Optional, Dict, Any, List
import requests

from .config import (
    VLLM_BASE_URL, 
    MODEL_NAME, 
    LLM_TEMPERATURE, 
    LLM_MAX_TOKENS,
    LLM_TOP_P,
    DEBUG_MODE
)


class LLMClient:
    """Client for interacting with vLLM-served LLM."""
    
    def __init__(self, base_url: str = VLLM_BASE_URL, model: str = MODEL_NAME):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.chat_endpoint = f"{self.base_url}/chat/completions"
    
    def _build_messages(self, system_prompt: str, user_message: str, 
                         conversation_history: Optional[List[Dict]] = None) -> List[Dict]:
        """Build messages array for chat completion."""
        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": user_message})
        return messages
    
    def generate(self, system_prompt: str, user_message: str,
                 conversation_history: Optional[List[Dict]] = None,
                 temperature: Optional[float] = None,
                 max_tokens: Optional[int] = None) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            system_prompt: System instructions for the model
            user_message: User's input
            conversation_history: Previous messages for context
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            Generated text response
        """
        messages = self._build_messages(system_prompt, user_message, conversation_history)
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or LLM_TEMPERATURE,
            "max_tokens": max_tokens or LLM_MAX_TOKENS,
            "top_p": LLM_TOP_P,
        }
        
        if DEBUG_MODE:
            print(f"[DEBUG] LLM Request: {json.dumps(payload, indent=2)[:500]}...")
        
        try:
            response = requests.post(
                self.chat_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if DEBUG_MODE:
                print(f"[DEBUG] LLM Response: {content[:500]}...")
            
            return self._clean_response(content)
            
        except requests.exceptions.Timeout:
            raise RuntimeError("LLM request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(f"Cannot connect to LLM server at {self.base_url}. Is vLLM running?")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"LLM request failed: {e}")
    
    def _clean_response(self, text: str) -> str:
        """Clean LLM response of common artifacts."""
        if not text:
            return ""
        
        # Remove thinking blocks if present
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
        
        # Remove trailing whitespace
        text = text.strip()
        
        return text
    
    def health_check(self) -> bool:
        """Check if LLM server is accessible."""
        try:
            response = requests.get(f"{self.base_url}/models", timeout=5)
            return response.status_code == 200
        except:
            return False


# Singleton instance
_llm_client: Optional[LLMClient] = None

def get_llm_client() -> LLMClient:
    """Get the singleton LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
