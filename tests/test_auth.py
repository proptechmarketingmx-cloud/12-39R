"""Tests de autenticacion (PostgreSQL)."""
from __future__ import annotations

import os

import pytest

from modules.auth import auth_manager


def _should_run_db_tests() -> bool:
    return os.getenv("RUN_DB_TESTS", "").lower() in ("1", "true", "yes")


@pytest.mark.skipif(not _should_run_db_tests(), reason="RUN_DB_TESTS no habilitado")
def test_login_admin():
    exito, usuario, msg = auth_manager.login("admin", "admin123")
    assert exito
