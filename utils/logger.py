"""Configuración de logging (placeholder)."""
from __future__ import annotations

import logging


def setup_logging(path: str = "logs/crm.log"):
    logging.basicConfig(level=logging.INFO)
