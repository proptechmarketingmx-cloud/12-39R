"""Tests para modules.clientes (save / find_by_curp)."""
from __future__ import annotations

import os
import tempfile

from modules import clientes


def test_save_and_find_by_curp():
    # Crear un store temporal
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        clientes.STORE_PATH = path
        # Inicializar store vacío
        with open(path, "w", encoding="utf-8") as f:
            f.write("[]")

        cliente = {"nombre": "Juan", "curp": "ABCDEFGH123456789X"}
        saved = clientes.save(cliente)
        assert "id" in saved

        found = clientes.find_by_curp("ABCDEFGH123456789X")
        assert found is not None
        assert found.get("nombre") == "Juan"

        # actualizar
        saved["nombre"] = "Juan Perez"
        updated = clientes.save(saved)
        assert updated.get("nombre") == "Juan Perez"
    finally:
        try:
            os.remove(path)
        except Exception:
            pass
