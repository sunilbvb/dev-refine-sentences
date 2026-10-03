"""Manager and coordinator for sentence refinement engines."""

from typing import Optional, Dict, Any
from .base import BaseRefiner
from .rules import RuleBasedRefiner
from .ollama import OllamaRefiner
from .languagetool import LanguageToolRefiner
from .gemini import GeminiRefiner
from .openai import OpenAIRefiner
from .claude import ClaudeRefiner


class RefinerManager:
    """Selects and manages available sentence refiner backends."""

    def __init__(
        self,
        preferred_engine: str = "auto",
        model: Optional[str] = None,
        config_manager: Optional[Any] = None,
    ):
        self.preferred_engine = preferred_engine.lower().strip()
        self.config_manager = config_manager

        # Initialize engines
        gemini_model = model if model and preferred_engine == "gemini" else "gemini-1.5-flash"
        openai_model = model if model and preferred_engine in ["openai", "chatgpt"] else "gpt-4o-mini"
        claude_model = model if model and preferred_engine in ["claude", "anthropic"] else "claude-3-5-haiku-20241022"
        ollama_model = model if model and preferred_engine == "ollama" else "qwen2.5:0.5b"

        self.engines: Dict[str, BaseRefiner] = {
            "rules": RuleBasedRefiner(config_manager=config_manager),
            "gemini": GeminiRefiner(model=gemini_model, config_manager=config_manager),
            "openai": OpenAIRefiner(model=openai_model, config_manager=config_manager),
            "chatgpt": OpenAIRefiner(model=openai_model, config_manager=config_manager),
            "claude": ClaudeRefiner(model=claude_model, config_manager=config_manager),
            "anthropic": ClaudeRefiner(model=claude_model, config_manager=config_manager),
            "ollama": OllamaRefiner(model=ollama_model),
            "languagetool": LanguageToolRefiner(),
        }

    def get_active_engine(self) -> BaseRefiner:
        """Resolve active refiner engine based on preference and availability."""
        if self.preferred_engine in self.engines:
            target = self.engines[self.preferred_engine]
            if target.is_available():
                return target

        # Auto detection priority: Gemini -> OpenAI -> Claude -> Ollama -> LanguageTool -> Rules
        for key in ["gemini", "openai", "claude", "ollama", "languagetool"]:
            engine = self.engines[key]
            if engine.is_available():
                return engine

        # Fallback (Always available, 100% offline)
        return self.engines["rules"]

    def refine(self, text: str, tone: str = "standard") -> str:
        """Refine text using the best available engine."""
        engine = self.get_active_engine()
        return engine.refine(text, tone=tone)

    def get_last_explanations(self) -> list:
        """Retrieve explanations from the most recently used engine if supported."""
        engine = self.get_active_engine()
        if hasattr(engine, "get_last_explanations"):
            return engine.get_last_explanations()
        return []
