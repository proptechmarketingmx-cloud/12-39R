"""Tests para modules.propiedades (PostgreSQL)."""
from __future__ import annotations

import os
import uuid

import pytest

from modules import propiedades


def _should_run_db_tests() -> bool:
    return os.getenv("RUN_DB_TESTS", "").lower() in ("1", "true", "yes")


@pytest.mark.skipif(not _should_run_db_tests(), reason="RUN_DB_TESTS no habilitado")
def test_save_propiedad():
    titulo = f"Casa prueba {uuid.uuid4().hex[:6]}"
    prop = {"titulo": titulo, "precio": "1000000", "ciudad": "CDMX"}
    saved = propiedades.save(prop)
    assert "id" in saved
    assert saved.get("titulo") == titulo

    saved["precio"] = "1100000"
    updated = propiedades.save(saved)
    assert float(updated.get("precio")) == 1100000.0

    assert propiedades.eliminar_propiedad(saved["id"]) is True
