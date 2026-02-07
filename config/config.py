"""Configuracion centralizada.

Lee valores desde variables de entorno y opcionalmente desde un archivo
`.env` (si se instala `python-dotenv`).

Para entornos de produccion, exporta las variables de entorno:
`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`.
"""
import os
from typing import Any

try:
    # Intentar cargar .env si python-dotenv esta instalado
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass

# Colores y UI
PRIMARY = os.getenv("PRIMARY", "#2196F3")
SUCCESS = os.getenv("SUCCESS", "#4CAF50")
DANGER = os.getenv("DANGER", "#F44336")


# Database (PostgreSQL; sobrescribir con env vars)
def _get_env(name: str, default: Any):
    v = os.getenv(name)
    if v is None:
        return default
    return v


DB_HOST = _get_env("DB_HOST", "127.0.0.1")
DB_PORT = int(_get_env("DB_PORT", 5432))
DB_USER = _get_env("DB_USER", "postgres")
DB_PASSWORD = _get_env("DB_PASSWORD", "")
DB_NAME = _get_env("DB_NAME", "CRM")

# UI constants
FONT_FAMILY = os.getenv("FONT_FAMILY", "Segoe UI")
FONT_SIZE_BASE = int(_get_env("FONT_SIZE_BASE", 10))
