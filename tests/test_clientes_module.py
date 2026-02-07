"""Tests para modules.clientes (PostgreSQL)."""
from __future__ import annotations

import os
import uuid

import pytest

from modules import clientes


def _should_run_db_tests() -> bool:
    return os.getenv("RUN_DB_TESTS", "").lower() in ("1", "true", "yes")


@pytest.mark.skipif(not _should_run_db_tests(), reason="RUN_DB_TESTS no habilitado")
def test_save_and_find_by_curp():
    curp = f"TEST{uuid.uuid4().hex[:14].upper()}X"
    cliente = {"primer_nombre": "Juan", "apellido_paterno": "Perez", "curp": curp}
    saved = clientes.save(cliente)
    assert "id" in saved

    found = clientes.find_by_curp(curp)
    assert found is not None
    assert found.get("primer_nombre") == "Juan"

    saved["primer_nombre"] = "Juanito"
    updated = clientes.save(saved)
    assert updated.get("primer_nombre") == "Juanito"

    # Cleanup
    assert clientes.eliminar_cliente(saved["id"]) is True
