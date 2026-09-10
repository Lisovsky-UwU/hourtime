import hashlib
import secrets

from hourtime.interfaces.services import TokenGenerator

# 32 bytes of entropy, url-safe, ~43 characters.
TOKEN_BYTES = 32


class OpaqueTokenGenerator(TokenGenerator):
    """Random opaque tokens; only their SHA-256 digests are ever persisted.

    Plain SHA-256 (no salt, no stretching) is deliberate: the input is already
    high-entropy random, so the digest has to stay a deterministic lookup key.
    """

    def generate(self) -> str:
        return secrets.token_urlsafe(TOKEN_BYTES)

    def hash(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
