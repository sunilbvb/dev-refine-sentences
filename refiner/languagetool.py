"""Local LanguageTool server connector using Python Standard Library."""

import json
import urllib.request
import urllib.parse
from typing import Any
from .base import BaseRefiner


class LanguageToolRefiner(BaseRefiner):
    """Local offline LanguageTool HTTP connector."""

    def __init__(self, host: str = "http://127.0.0.1:8081"):
        self.host = host.rstrip("/")

    @property
    def name(self) -> str:
        return "Local LanguageTool Server"

    def is_available(self) -> bool:
        """Check if local LanguageTool server is reachable."""
        try:
            req = urllib.request.Request(f"{self.host}/v2/languages", method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def refine(self, text: str, tone: str = "standard", **kwargs: Any) -> str:
        if not text or not text.strip():
            return ""

        url = f"{self.host}/v2/check"
        params = {
            "text": text,
            "language": "en-US",
        }
        data = urllib.parse.urlencode(params).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                matches = result.get("matches", [])
                
                # Apply replacements in reverse offset order to maintain index positions
                matches.sort(key=lambda m: m["offset"], reverse=True)
                refined = text
                for m in matches:
                    replacements = m.get("replacements", [])
                    if replacements:
                        offset = m["offset"]
                        length = m["length"]
                        best_fix = replacements[0]["value"]
                        refined = refined[:offset] + best_fix + refined[offset + length:]
                return refined.strip()
        except Exception:
            return text
