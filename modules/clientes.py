"""Lógica de clientes - almacenamiento simple para desarrollo.

Provee funciones mínimas `find_by_curp` y `save` usadas por la UI.
Persistencia en `database/seeds/clientes_store.json` cuando no hay una
implementación más avanzada.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional

LOG = logging.getLogger(__name__)

STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "seeds", "clientes_store.json")


def _load_store() -> List[Dict]:
	path = os.path.abspath(STORE_PATH)
	if not os.path.exists(path):
		return []
	try:
		with open(path, "r", encoding="utf-8") as f:
			return json.load(f)
	except Exception:
		LOG.exception("No se pudo leer el store de clientes")
		return []


def _save_store(data: List[Dict]) -> None:
	path = os.path.abspath(STORE_PATH)
	os.makedirs(os.path.dirname(path), exist_ok=True)
	try:
		with open(path, "w", encoding="utf-8") as f:
			json.dump(data, f, indent=2, ensure_ascii=False)
	except Exception:
		LOG.exception("No se pudo guardar el store de clientes")


def find_by_curp(curp: str) -> Optional[Dict]:
	"""Busca y retorna un cliente por CURP, o None si no existe.

	Args:
		curp: CURP a buscar (case-sensitive según store).
	Returns:
		Diccionario del cliente o None.
	"""
	if not curp:
		return None
	data = _load_store()
	for c in data:
		if c.get("curp") == curp:
			return c
	return None


def save(cliente: Dict) -> Dict:
	"""Guarda o actualiza un cliente en el store local.

	- Si `cliente` contiene `id` intenta actualizar el registro.
	- Si no tiene `id`, asigna uno nuevo.

	Levanta ValueError en validaciones básicas.
	Retorna el cliente guardado (con `id`).
	"""
	if not isinstance(cliente, dict):
		raise ValueError("Cliente debe ser un diccionario")
	nombre = cliente.get("nombre", "").strip()
	curp = cliente.get("curp", "").strip()
	if not nombre:
		raise ValueError("El nombre es obligatorio")
	if not curp or len(curp) != 18:
		raise ValueError("CURP inválido")

	data = _load_store()

	# Update
	if cliente.get("id"):
		for i, c in enumerate(data):
			if c.get("id") == cliente.get("id"):
				data[i].update(cliente)
				_save_store(data)
				return data[i]

	# Insert
	next_id = max((c.get("id", 0) for c in data), default=0) + 1
	cliente["id"] = next_id
	data.append(cliente)
	_save_store(data)
	return cliente

