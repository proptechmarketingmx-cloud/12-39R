"""Lógica de clientes - almacenamiento simple para desarrollo.

Provee funciones mínimas `find_by_curp` y `save` usadas por la UI.
Persistencia en `database/seeds/clientes_store.json` cuando no hay una
implementación más avanzada.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional
from collections.abc import Mapping

LOG = logging.getLogger(__name__)

STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "seeds", "clientes_store.json")


def _load_store() -> List[Dict[str, Any]]:
	path = os.path.abspath(STORE_PATH)
	if not os.path.exists(path):
		return []
	try:
		with open(path, "r", encoding="utf-8") as f:
			return json.load(f)
	except Exception:
		LOG.exception("No se pudo leer el store de clientes")
		return []


def _save_store(data: List[Dict[str, Any]]) -> None:
	path = os.path.abspath(STORE_PATH)
	os.makedirs(os.path.dirname(path), exist_ok=True)
	try:
		with open(path, "w", encoding="utf-8") as f:
			json.dump(data, f, indent=2, ensure_ascii=False)
	except Exception:
		LOG.exception("No se pudo guardar el store de clientes")


def _to_int(value: Any, default: int = 0) -> int:
	try:
		return int(value)
	except Exception:
		return default


def find_by_curp(curp: str) -> Optional[Dict[str, Any]]:
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


def save(cliente: Dict[str, Any] | Mapping[str, Any]) -> Dict[str, Any]:
	"""Guarda o actualiza un cliente en el store local.

	- Si `cliente` contiene `id` intenta actualizar el registro.
	- Si no tiene `id`, asigna uno nuevo.

	Levanta ValueError en validaciones básicas.
	Retorna el cliente guardado (con `id`).
	"""
	if not isinstance(cliente, dict):
		if isinstance(cliente, Mapping):
			cliente = dict(cliente)
		elif hasattr(cliente, "__dict__"):
			cliente = dict(vars(cliente))
		else:
			raise ValueError("Cliente debe ser un diccionario o Mapping")
	curp = str(cliente.get("curp", "")).strip()
	if curp and len(curp) != 18:
		raise ValueError("CURP inválido")

	data = _load_store()

	# Update
	if cliente.get("id") is not None:
		cid = _to_int(cliente.get("id"))
		for i, c in enumerate(data):
			if _to_int(c.get("id")) == cid:
				data[i].update(cliente)
				_save_store(data)
				return data[i]

	# Insert
	next_id = max((_to_int(c.get("id", 0)) for c in data), default=0) + 1
	cliente["id"] = int(next_id)
	data.append(cliente)
	_save_store(data)
	return cliente


def eliminar_cliente(cliente_id: int) -> bool:
	"""Elimina un cliente del store por id.

	Retorna True si se eliminó, False si no se encontró.
	"""
	try:
		cid = int(cliente_id)
	except Exception:
		raise ValueError("ID de cliente inválido")

	data = _load_store()
	nuevo = [c for c in data if int(c.get("id", 0)) != cid]
	if len(nuevo) == len(data):
		LOG.info("Eliminar cliente: id=%s no encontrado", cid)
		return False
	_save_store(nuevo)
	LOG.info("Cliente eliminado: id=%s", cid)
	return True
