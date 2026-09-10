from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str: ...

    @abstractmethod
    def verify(self, password: str, password_hash: str) -> bool:
        """Constant-time check; returns False on a malformed hash instead of raising."""

    @abstractmethod
    def needs_rehash(self, password_hash: str) -> bool:
        """True when the stored hash uses outdated parameters."""
