"""Conexion a PostgreSQL.

Provee `get_connection()` que retorna un objeto connection listo para usar.
Lee configuracion desde `config.config` o variables de entorno.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import psycopg

LOG = logging.getLogger(__name__)

try:
    import config.config as _config
except Exception:
    _config = None


def _get_cfg(name: str, default: Any = None) -> Any:
    env = os.getenv(name.upper())
    if env is not None:
        return env
    if _config and hasattr(_config, name):
        return getattr(_config, name)
    return default


def get_connection():
    """Retorna una conexion a PostgreSQL.

    Lanza RuntimeError si la conexion falla.
    """
    host = _get_cfg("DB_HOST", "127.0.0.1")
    port = int(_get_cfg("DB_PORT", 5432))
    user = _get_cfg("DB_USER", "postgres")
    password = _get_cfg("DB_PASSWORD", "")
    database = _get_cfg("DB_NAME", "CRM")

    try:
        conn = psycopg.connect(host=host, port=port, user=user, password=password, dbname=database)
        return conn
    except Exception:
        LOG.exception("psycopg no pudo conectar")
        raise RuntimeError("No se pudo establecer conexion con la base de datos PostgreSQL. Verifica drivers y credenciales.")
