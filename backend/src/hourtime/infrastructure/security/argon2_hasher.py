from argon2 import PasswordHasher as Argon2
from argon2.exceptions import Argon2Error, InvalidHashError, VerifyMismatchError

from hourtime.interfaces.services import PasswordHasher


class Argon2PasswordHasher(PasswordHasher):
    """Argon2id with the library defaults, which track current guidance."""

    def __init__(self) -> None:
        self._hasher = Argon2()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return self._hasher.verify(password_hash, password)
        except (VerifyMismatchError, InvalidHashError, Argon2Error):
            return False

    def needs_rehash(self, password_hash: str) -> bool:
        try:
            return self._hasher.check_needs_rehash(password_hash)
        except (InvalidHashError, Argon2Error):
            return False
