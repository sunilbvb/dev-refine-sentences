"""Google Gemini API refiner using Python Standard Library HTTP client."""

import json
import urllib.request
import urllib.error
from typing import Any, Optional
from .base import BaseRefiner
from config.settings import ConfigManager


class GeminiRefiner(BaseRefiner):
    """Google Gemini API refiner using standard library urllib."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-flash",
        config_manager: Optional[ConfigManager] = None,
    ):
        self.config_manager = config_manager or ConfigManager()
        self._explicit_key = api_key
        self.model = model

    @property
    def api_key(self) -> Optional[str]:
        return self._explicit_key or self.config_manager.get_api_key("gemini")

    @property
    def name(self) -> str:
        return f"Google Gemini ({self.model})"

    def is_available(self) -> bool:
        """Check if Gemini API key is configured."""
        return bool(self.api_key)

    def refine(self, text: str, tone: str = "standard", **kwargs: Any) -> str:
        if not text or not text.strip():
            return ""

        key = self.api_key
        if not key:
            return text

        tone_instructions = {
            "standard": "Fix all grammar, spelling, punctuation, and phrasing. Keep meaning identical.",
            "concise": "Make the sentence concise, direct, and clear. Eliminate fluff and filler words.",
            "professional": "Rewrite in a polished, courteous, and formal workplace tone.",
            "friendly": "Rewrite in an approachable, warm, and friendly conversational tone.",
            "bullet_points": "Format the main points into clean markdown bullet points (- ...).",
            "email_formal": "Format as a formal email with polite greeting and professional sign-off.",
        }

        instruction = tone_instructions.get(tone.lower(), tone_instructions["standard"])
        prompt = (
            f"You are an expert sentence refinement assistant.\n"
            f"Instruction: {instruction}\n"
            f"Rule: Return ONLY the final refined text. Do not add quotes, commentary, markdown code blocks, or explanations.\n\n"
            f"Text to refine: {text}"
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={key}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
            }
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=12.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        output = parts[0].get("text", "").strip()
                        if (output.startswith('"') and output.endswith('"')) or (output.startswith("'") and output.endswith("'")):
                            output = output[1:-1].strip()
                        return output if output else text
        except Exception as e:
            # Fallback to original text if API call fails
            return text

        return text
