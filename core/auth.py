import os
import secrets

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer_scheme = HTTPBearer(auto_error=True)

# TOKEN_SECONDARY belongs to AI consume
SECONDARY_TOKEN_ALLOWED_ENDPOINTS = frozenset(
    {
        ("GET", "/shopping/flows/hotspot-access"),
        ("GET", "/shopping/flows/parking-access"),
        ("GET", "/shopping/flows/parking-places"),
        ("GET", "/shopping/flows/people-access"),
        ("GET", "/shopping/finance/sales"),
    }
)


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


def _matches(provided_token: str, configured_token: str | None) -> bool:
    return bool(
        configured_token
        and secrets.compare_digest(provided_token, configured_token)
    )


def verify(
    request: Request,
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    primary_token = os.getenv("TOKEN")
    secondary_token = os.getenv("TOKEN_SECONDARY")
    if not primary_token and not secondary_token:
        raise HTTPException(status_code=500, detail="API token not configured")

    if _matches(creds.credentials, primary_token):
        return True

    if _matches(creds.credentials, secondary_token):
        endpoint = (request.method.upper(), request.url.path)
        if endpoint not in SECONDARY_TOKEN_ALLOWED_ENDPOINTS:
            raise HTTPException(
                status_code=403,
                detail="Token does not have access to this endpoint",
            )
        return True

    raise HTTPException(status_code=403, detail="Invalid token")
