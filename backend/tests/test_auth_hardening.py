import pytest
from fastapi import HTTPException

from app.core import auth


def _set_keys(monkeypatch, admin: str = "", operator: str = "", readonly: str = "") -> None:
    monkeypatch.setattr(auth.settings, "ADMIN_API_KEY", admin)
    monkeypatch.setattr(auth.settings, "OPERATOR_API_KEY", operator)
    monkeypatch.setattr(auth.settings, "READONLY_API_KEY", readonly)


def test_extract_api_key_prefers_x_api_key() -> None:
    token = auth._extract_api_key("Bearer from-header", "from-x-api-key")
    assert token == "from-x-api-key"


def test_extract_api_key_from_authorization_bearer() -> None:
    token = auth._extract_api_key("Bearer abc123", None)
    assert token == "abc123"


def test_get_auth_context_returns_matching_role(monkeypatch) -> None:
    _set_keys(monkeypatch, admin="admin", operator="operator", readonly="read")
    ctx = auth.get_auth_context(x_api_key="operator")
    assert ctx.role == "operator"


def test_get_auth_context_requires_configured_keys(monkeypatch) -> None:
    _set_keys(monkeypatch)
    with pytest.raises(HTTPException) as exc:
        auth.get_auth_context(x_api_key="anything")
    assert exc.value.status_code == 503


def test_get_auth_context_requires_api_key(monkeypatch) -> None:
    _set_keys(monkeypatch, readonly="read")
    with pytest.raises(HTTPException) as exc:
        auth.get_auth_context(authorization=None, x_api_key=None)
    assert exc.value.status_code == 401


def test_get_auth_context_rejects_invalid_key(monkeypatch) -> None:
    _set_keys(monkeypatch, readonly="read")
    with pytest.raises(HTTPException) as exc:
        auth.get_auth_context(x_api_key="invalid")
    assert exc.value.status_code == 401


def test_enforce_role_blocks_lower_privilege() -> None:
    with pytest.raises(HTTPException) as exc:
        auth._enforce_role(auth.AuthContext(role="read"), "operator")
    assert exc.value.status_code == 403


def test_enforce_role_allows_higher_privilege() -> None:
    ctx = auth._enforce_role(auth.AuthContext(role="admin"), "operator")
    assert ctx.role == "admin"
