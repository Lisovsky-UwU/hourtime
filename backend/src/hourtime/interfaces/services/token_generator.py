from abc import ABC, abstractmethod


class TokenGenerator(ABC):
    """Issues opaque session tokens and the digests stored alongside them."""

    @abstractmethod
    def generate(self) -> str:
        """A fresh, unguessable token to hand to the client."""

    @abstractmethod
    def hash(self, token: str) -> str:
        """Deterministic digest of a token, safe to keep in the database."""
