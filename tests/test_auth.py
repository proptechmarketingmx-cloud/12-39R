"""Tests unitarios iniciales (placeholder)."""
from __future__ import annotations

from modules.auth import auth_manager


def test_login_admin():
    exito, usuario, msg = auth_manager.login("admin", "admin123")
    assert exito
