import os
import json
import logging
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger(__name__)

class GeminiProvider:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("AI_API_KEY")
        # List of models to try in order. If one fails (e.g., 503), try the next.
        # Based on testing, gemma-4-26b-a4b-it was available, but we'll try gemini first.
        self.fallback_models = [
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro-latest",
            "gemma-4-26b-a4b-it"
        ]
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def generate_summary(self, context: Dict[str, Any], instruction: str, output_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calls the Gemini API with structured JSON output enforcement.
        Returns the parsed JSON response or raises an exception.
        """
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")

        prompt_text = f"{instruction}\n\nCONTEXT:\n{json.dumps(context, indent=2)}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt_text}]
            }],
            "generationConfig": {
                "temperature": 0.2, # Strict low temperature for factual grounding
                "response_mime_type": "application/json",
            }
        }

        # Try models in fallback order
        last_exception = None
        for model in self.fallback_models:
            url = f"{self.base_url}/{model}:generateContent?key={self.api_key}"
            try:
                with httpx.Client(timeout=15.0) as client:
                    response = client.post(url, json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            if parts and "text" in parts[0]:
                                raw_json = parts[0]["text"]
                                return json.loads(raw_json)
                    
                    logger.warning(f"Model {model} failed with status {response.status_code}: {response.text}")
                    last_exception = Exception(f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                logger.warning(f"Model {model} encountered an error: {str(e)}")
                last_exception = e

        # If all models fail, raise the last exception to trigger the rule-based fallback
        raise Exception(f"All Gemini models failed. Last error: {str(last_exception)}")
