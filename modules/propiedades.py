"""Lógica de propiedades - almacenamiento simple para desarrollo.

Provee `save` para persistencia en `database/seeds/propiedades_store.json`.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional

LOG = logging.getLogger(__name__)

STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "seeds", "propiedades_store.json")


def _load_store() -> List[Dict]:
	path = os.path.abspath(STORE_PATH)
	if not os.path.exists(path):
		return []
	try:
		with open(path, "r", encoding="utf-8") as f:
			return json.load(f)
	except Exception:
		LOG.exception("No se pudo leer el store de propiedades")
		return []


def _save_store(data: List[Dict]) -> None:
	path = os.path.abspath(STORE_PATH)
	os.makedirs(os.path.dirname(path), exist_ok=True)
	try:
		with open(path, "w", encoding="utf-8") as f:
			json.dump(data, f, indent=2, ensure_ascii=False)
	except Exception:
		LOG.exception("No se pudo guardar el store de propiedades")


def save(propiedad: Dict) -> Dict:
	"""Guarda o actualiza una propiedad en el store local.

	- Si `propiedad` contiene `id` intenta actualizar.
	- Si no, asigna un `id` secuencial.
	"""
	if not isinstance(propiedad, dict):
		raise ValueError("Propiedad debe ser un diccionario")
	titulo = propiedad.get("titulo", "").strip()
	precio = propiedad.get("precio", "").strip()
	if not titulo:
		raise ValueError("El título es obligatorio")
	if not precio:
		raise ValueError("El precio es obligatorio")

	data = _load_store()

	# Update
	if propiedad.get("id"):
		for i, p in enumerate(data):
			if p.get("id") == propiedad.get("id"):
				data[i].update(propiedad)
				_save_store(data)
				return data[i]

	# Insert
	next_id = max((p.get("id", 0) for p in data), default=0) + 1
	propiedad["id"] = next_id
	data.append(propiedad)
	_save_store(data)
	return propiedad

