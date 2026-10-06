"""Local Ollama offline model refiner using Python Standard Library HTTP client."""

import json
import urllib.request
import urllib.error
from typing import Any
from .base import BaseRefiner


class OllamaRefiner(BaseRefiner):
    """Local offline LLM refiner using self-hosted Ollama."""

    def __init__(self, host: str = "http://127.0.0.1:11434", model: str = "qwen2.5:0.5b"):
        self.host = host.rstrip("/")
        self.model = model

    @property
    def name(self) -> str:
        return f"Local Ollama ({self.model})"

    def is_available(self) -> bool:
        """Check if local Ollama daemon is reachable and model is installed."""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status != 200:
                    return False
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                target = self.model.strip()
                return any(
                    target == m or f"{target}:latest" == m or target.split(":")[0] == m.split(":")[0]
                    for m in models
                )
        except Exception:
            return False

    def refine(self, text: str, tone: str = "standard", **kwargs: Any) -> str:
        if not text or not text.strip():
            return ""

        tone_instructions = {
            "standard": "Fix all grammar, spelling, punctuation, and phrasing. Keep meaning identical.",
            "concise": "Make the sentence concise, direct, and clear. Eliminate fluff and filler words.",
            "professional": "Rewrite in a polished, courteous, and formal workplace tone.",
            "friendly": "Rewrite in an approachable, warm, and friendly conversational tone.",
        }

        instruction = tone_instructions.get(tone.lower(), tone_instructions["standard"])
        prompt = (
            f"You are a sentence refinement assistant.\n"
            f"Instruction: {instruction}\n"
            f"Important: Return ONLY the refined sentence. Do not add quotes, markdown, or commentary.\n\n"
            f"Input: {text}\n"
            f"Output:"
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "30m",  # keep the model resident so later calls skip the cold start
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
            }
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.host}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=60.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                output = result.get("response", "").strip()
                # Strip wrapping quotes if added by model
                if (output.startswith('"') and output.endswith('"')) or (output.startswith("'") and output.endswith("'")):
                    output = output[1:-1].strip()
                return output if output else text
        except Exception:
            # Fallback to original text if call fails
            return text
