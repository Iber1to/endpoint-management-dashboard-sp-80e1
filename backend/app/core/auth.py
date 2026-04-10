from __future__ import annotations

import secrets
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status

from app.core.config import settings

_ROLE_RANK = {"read": 1, "operator": 2, "admin": 3}


@dataclass(frozen=True)
class AuthContext:
    role: str


def _configured_keys() -> dict[str, str]:
    return {
        role: key
        for role, key in {
            "admin": settings.ADMIN_API_KEY,
            "operator": settings.OPERATOR_API_KEY,
            "read": settings.READONLY_API_KEY,
        }.items()
        if key
    }


def _extract_api_key(authorization: str | None, x_api_key: str | None) -> str | None:
    if x_api_key:
        return x_api_key.strip()

    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            return token.strip()

    return None


def get_auth_context(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> AuthContext:
    configured_keys = _configured_keys()
    if not configured_keys:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured",
        )

    provided_key = _extract_api_key(authorization, x_api_key)
    if not provided_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    for role, key in configured_keys.items():
        if secrets.compare_digest(provided_key, key):
            return AuthContext(role=role)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def _enforce_role(ctx: AuthContext, required_role: str) -> AuthContext:
    if _ROLE_RANK[ctx.role] < _ROLE_RANK[required_role]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return ctx


def require_read(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
    return _enforce_role(ctx, "read")


def require_operator(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
    return _enforce_role(ctx, "operator")


def require_admin(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
    return _enforce_role(ctx, "admin")
