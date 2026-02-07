"""Conexion a PostgreSQL para el API."""
from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

from app.config import settings


def get_connection():
	return psycopg.connect(
		host=settings.DB_HOST,
		port=settings.DB_PORT,
		user=settings.DB_USER,
		password=settings.DB_PASSWORD,
		dbname=settings.DB_NAME,
		row_factory=dict_row,
	)
