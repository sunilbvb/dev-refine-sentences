"""Base interface for sentence refiners."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseRefiner(ABC):
    """Abstract base class for all sentence refinement engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the refiner engine."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if refiner backend is reachable/ready."""
        pass

    @abstractmethod
    def refine(self, text: str, tone: str = "standard", **kwargs: Any) -> str:
        """Refine sentence according to specified tone.

        Args:
            text: Raw input string.
            tone: Desired tone ('standard', 'professional', 'concise', 'friendly').
            kwargs: Extra engine-specific parameters.

        Returns:
            Refined string.
        """
        pass
