from abc import ABC, abstractmethod
from datetime import datetime


class Clock(ABC):
    """Injected so that use cases are testable without freezing real time."""

    @abstractmethod
    def now(self) -> datetime:
        """Current moment as a timezone-aware UTC datetime."""
