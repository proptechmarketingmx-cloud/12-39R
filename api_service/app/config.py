"""Configuracion del API."""
from __future__ import annotations

import os
from dataclasses import dataclass

from pathlib import Path
from dotenv import load_dotenv

# Cargar .env desde la carpeta api_service (independiente del cwd)
_env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_env_path, override=True)


def _get_env(name: str, default: str) -> str:
	val = os.getenv(name)
	return default if val is None else val


@dataclass(frozen=True)
class Settings:
	api_use_db: bool = _get_env("API_USE_DB", "false").lower() in ("1", "true", "yes")
	DB_HOST: str = _get_env("DB_HOST", "127.0.0.1")
	DB_PORT: int = int(_get_env("DB_PORT", "5432"))
	DB_USER: str = _get_env("DB_USER", "postgres")
	DB_PASSWORD: str = _get_env("DB_PASSWORD", "")
	DB_NAME: str = _get_env("DB_NAME", "CRM")


settings = Settings()
