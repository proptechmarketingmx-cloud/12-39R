"""Tests para modules.propiedades (save)."""
from __future__ import annotations

import os
import tempfile

from modules import propiedades


def test_save_propiedad():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        propiedades.STORE_PATH = path

        prop = {"titulo": "Casa prueba", "precio": "1000000"}
        saved = propiedades.save(prop)
        assert "id" in saved
        assert saved.get("titulo") == "Casa prueba"

        # actualizar
        saved["precio"] = "1100000"
        updated = propiedades.save(saved)
        assert updated.get("precio") == "1100000"
    finally:
        try:
            os.remove(path)
        except Exception:
            pass
