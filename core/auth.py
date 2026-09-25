import os
import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer_scheme = HTTPBearer(auto_error=True)


def configured_tokens() -> tuple[str, ...]:
    """Return the configured primary and optional secondary bearer tokens."""
    return tuple(
        token
        for token in (os.getenv("TOKEN"), os.getenv("TOKEN_SECONDARY"))
        if token
    )


def token_is_valid(token: str, valid_tokens: tuple[str, ...] | None = None) -> bool:
    """Compare bearer tokens without leaking which configured token matched."""
    tokens = valid_tokens if valid_tokens is not None else configured_tokens()
    return any(secrets.compare_digest(token, valid_token) for valid_token in tokens)


def verify(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    tokens = configured_tokens()
    if not tokens:
        raise HTTPException(status_code=500, detail="API token not configured")

    if not token_is_valid(creds.credentials, tokens):
        raise HTTPException(status_code=403, detail="Invalid token")

    return True
