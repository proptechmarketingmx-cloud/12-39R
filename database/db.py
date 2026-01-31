"""Conexión a MySQL con soporte para mysql-connector-python y PyMySQL.

Provee `get_connection()` que retorna un objeto connection listo para usar.
Lee configuración desde `config.config` o variables de entorno.
"""
from __future__ import annotations

import logging
import os
from typing import Any

LOG = logging.getLogger(__name__)

try:
    import mysql.connector as mysql_connector  # type: ignore
    MYSQL_CONNECTOR_AVAILABLE = True
except Exception:
    mysql_connector = None  # type: ignore
    MYSQL_CONNECTOR_AVAILABLE = False

try:
    import pymysql  # type: ignore
    PYMysql_AVAILABLE = True
except Exception:
    pymysql = None  # type: ignore
    PYMysql_AVAILABLE = False

try:
    import config.config as _config
except Exception:
    _config = None


def _get_cfg(name: str, default: Any = None) -> Any:
    # Prefer environment variables, then config module, then default
    env = os.getenv(name.upper())
    if env is not None:
        return env
    if _config and hasattr(_config, name):
        return getattr(_config, name)
    return default


def get_connection():
    """Retorna una conexión a MySQL.

    Lanza RuntimeError si no hay un driver disponible o la conexión falla.
    """
    host = _get_cfg("DB_HOST", "127.0.0.1")
    port = int(_get_cfg("DB_PORT", 3306))
    user = _get_cfg("DB_USER", "root")
    password = _get_cfg("DB_PASSWORD", "")
    database = _get_cfg("DB_NAME", "crm_inmobiliario")

    if MYSQL_CONNECTOR_AVAILABLE and mysql_connector is not None:
        try:
            conn = mysql_connector.connect(host=host, port=port, user=user, password=password, database=database)
            return conn
        except Exception:
            LOG.exception("mysql.connector no pudo conectar, intentando pymysql si está disponible")

    if PYMysql_AVAILABLE and pymysql is not None:
        try:
            conn = pymysql.connect(host=host, port=port, user=user, password=password, database=database, cursorclass=pymysql.cursors.Cursor)
            return conn
        except Exception:
            LOG.exception("pymysql no pudo conectar")

    raise RuntimeError("No se pudo establecer conexión con la base de datos MySQL. Verifica drivers y credenciales.")

