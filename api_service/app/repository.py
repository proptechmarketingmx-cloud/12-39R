"""Repositorio de propiedades (JSON o PostgreSQL)."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from app.config import settings
from app.db import get_connection

STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "database", "seeds", "propiedades_store.json")


def _load_json() -> List[Dict[str, Any]]:
	path = os.path.abspath(STORE_PATH)
	if not os.path.exists(path):
		return []
	with open(path, "r", encoding="utf-8") as f:
		return json.load(f)


def _filter_items(items: List[Dict[str, Any]], zone: Optional[str], price_min: Optional[float], price_max: Optional[float],
				tipo: Optional[str], bedrooms: Optional[int], amenities: Optional[List[str]]) -> List[Dict[str, Any]]:
	def _match(item: Dict[str, Any]) -> bool:
		if zone and str(item.get("zona", item.get("ubicacion", {}).get("zona", ""))).lower() != zone.lower():
			return False
		if tipo and str(item.get("tipo", item.get("tipo_propiedad", ""))).lower() != tipo.lower():
			return False
		if price_min is not None:
			try:
				if float(item.get("precio", 0)) < price_min:
					return False
			except Exception:
				return False
		if price_max is not None:
			try:
				if float(item.get("precio", 0)) > price_max:
					return False
			except Exception:
				return False
		if bedrooms is not None:
			try:
				if int(item.get("habitaciones", 0)) != bedrooms:
					return False
			except Exception:
				return False
		if amenities:
			carac = item.get("caracteristicas", {})
			if isinstance(carac, dict):
				vals = [k for k, v in carac.items() if v]
			else:
				vals = []
			for a in amenities:
				if a not in vals:
					return False
		return True
	return [i for i in items if _match(i)]


def list_properties(zone: Optional[str] = None, price_min: Optional[float] = None, price_max: Optional[float] = None,
				tipo: Optional[str] = None, bedrooms: Optional[int] = None, amenities: Optional[List[str]] = None) -> List[Dict[str, Any]]:
	if not settings.api_use_db:
		items = _load_json()
		return _filter_items(items, zone, price_min, price_max, tipo, bedrooms, amenities)

	conn = get_connection()
	try:
		cur = conn.cursor()
		query = "SELECT * FROM propiedades WHERE 1=1"
		params: List[Any] = []
		if zone:
			query += " AND zona=%s"
			params.append(zone)
		if tipo:
			query += " AND tipo=%s"
			params.append(tipo)
		if price_min is not None:
			query += " AND precio >= %s"
			params.append(price_min)
		if price_max is not None:
			query += " AND precio <= %s"
			params.append(price_max)
		if bedrooms is not None:
			query += " AND habitaciones=%s"
			params.append(bedrooms)
		cur.execute(query, params)
		rows = cur.fetchall() or []
		return rows
	finally:
		conn.close()


def get_property(prop_id: int) -> Optional[Dict[str, Any]]:
	if not settings.api_use_db:
		for item in _load_json():
			try:
				if int(item.get("id", 0)) == int(prop_id):
					return item
			except Exception:
				continue
		return None

	conn = get_connection()
	try:
		cur = conn.cursor()
		cur.execute("SELECT * FROM propiedades WHERE id=%s", (prop_id,))
		return cur.fetchone()
	finally:
		conn.close()
