"""Esquemas del API."""
from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel


class PropertyOut(BaseModel):
	id: int
	titulo: Optional[str] = None
	descripcion: Optional[str] = None
	precio: Optional[float] = None
	metros: Optional[float] = None
	estado: Optional[str] = None
	ciudad: Optional[str] = None
	zona: Optional[str] = None
	tipo: Optional[str] = None
	habitaciones: Optional[int] = None
	amenidades: Optional[List[str]] = None
