"""Lógica de propiedades - PostgreSQL.

Funciones:
- save(propiedad)
- eliminar_propiedad(prop_id) (soft delete)
- listar_propiedades(page, page_size, filtros)
- buscar_propiedades(texto, page, page_size, filtros)
- contar_propiedades(texto, filtros)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from collections.abc import Mapping

from database import db as _db

LOG = logging.getLogger(__name__)


def _clean_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _to_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except Exception:
        return None


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


def _row_to_dict(cur, row) -> Dict[str, Any]:
    cols = [c.name for c in cur.description]
    return {cols[i]: row[i] for i in range(len(cols))}


def _normalize_propiedad(prop: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(prop)
    ubic = data.get("ubicacion") if isinstance(data.get("ubicacion"), dict) else {}
    if "ciudad" not in data and ubic:
        data["ciudad"] = ubic.get("Ciudad") or ubic.get("ciudad")
    if "estado" not in data and ubic:
        data["estado"] = ubic.get("Estado") or ubic.get("estado")
    if "zona" not in data and ubic:
        data["zona"] = ubic.get("Zona") or ubic.get("zona") or ubic.get("Colonia") or ubic.get("colonia")

    carac = data.get("caracteristicas")
    if carac and "amenidades" not in data:
        if isinstance(carac, dict):
            data["amenidades"] = ", ".join([k for k, v in carac.items() if v])
        elif isinstance(carac, list):
            data["amenidades"] = ", ".join([str(x) for x in carac if x])
    return data


def save(propiedad: Dict[str, Any] | Mapping[str, Any]) -> Dict[str, Any]:
    """Guarda o actualiza una propiedad en PostgreSQL."""
    if not isinstance(propiedad, dict):
        if isinstance(propiedad, Mapping):
            propiedad = dict(propiedad)
        elif hasattr(propiedad, "__dict__"):
            propiedad = dict(vars(propiedad))
        else:
            raise ValueError("Propiedad debe ser un diccionario o Mapping")

    data = _normalize_propiedad(propiedad)

    fields = {
        "activo",
        "titulo",
        "descripcion",
        "precio",
        "metros",
        "estado",
        "ciudad",
        "zona",
        "tipo",
        "habitaciones",
        "amenidades",
    }
    payload: Dict[str, Any] = {}
    for k in fields:
        if k in data:
            payload[k] = data.get(k)

    payload["titulo"] = _clean_str(payload.get("titulo"))
    payload["descripcion"] = _clean_str(payload.get("descripcion"))
    payload["estado"] = _clean_str(payload.get("estado"))
    payload["ciudad"] = _clean_str(payload.get("ciudad"))
    payload["zona"] = _clean_str(payload.get("zona"))
    payload["tipo"] = _clean_str(payload.get("tipo"))
    payload["amenidades"] = _clean_str(payload.get("amenidades"))

    payload["precio"] = _to_float(payload.get("precio")) or 0.0
    payload["metros"] = _to_float(payload.get("metros"))
    payload["habitaciones"] = _to_int(payload.get("habitaciones"))

    if "activo" in payload:
        payload["activo"] = bool(payload.get("activo"))

    conn = _db.get_connection()
    cur = conn.cursor()
    try:
        if data.get("id"):
            prop_id = int(data.get("id"))
            set_clause = ", ".join([f"{k}=%s" for k in payload.keys()])
            values = list(payload.values()) + [prop_id]
            cur.execute(f"UPDATE propiedades SET {set_clause} WHERE id=%s RETURNING id", values)
            row = cur.fetchone()
            conn.commit()
            return {"id": row[0], **payload} if row else {"id": prop_id, **payload}

        cols = ", ".join(payload.keys())
        placeholders = ", ".join(["%s"] * len(payload))
        cur.execute(
            f"INSERT INTO propiedades ({cols}) VALUES ({placeholders}) RETURNING id",
            list(payload.values()),
        )
        row = cur.fetchone()
        conn.commit()
        return {"id": row[0], **payload} if row else payload
    finally:
        cur.close()
        conn.close()


def eliminar_propiedad(prop_id: int) -> bool:
    """Elimina una propiedad (soft delete)."""
    try:
        pid = int(prop_id)
    except Exception:
        raise ValueError("ID de propiedad inválido")
    conn = _db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE propiedades SET activo=%s WHERE id=%s", (False, pid))
        conn.commit()
        return cur.rowcount > 0
    finally:
        cur.close()
        conn.close()


def _build_where(texto: Optional[str], filtros: Optional[Dict[str, Any]]) -> tuple[str, List[Any]]:
    where = "WHERE 1=1"
    params: List[Any] = []

    if filtros:
        estado = filtros.get("estado")
        precio_min = filtros.get("precio_min")
        precio_max = filtros.get("precio_max")
        if estado:
            where += " AND estado=%s"
            params.append(estado)
        if precio_min is not None:
            where += " AND precio >= %s"
            params.append(float(precio_min))
        if precio_max is not None:
            where += " AND precio <= %s"
            params.append(float(precio_max))

    if texto:
        t = f"%{texto.lower()}%"
        where += " AND ("
        where += "LOWER(COALESCE(titulo,'')) ILIKE %s OR "
        where += "LOWER(COALESCE(descripcion,'')) ILIKE %s OR "
        where += "LOWER(COALESCE(estado,'')) ILIKE %s OR "
        where += "LOWER(COALESCE(ciudad,'')) ILIKE %s OR "
        where += "LOWER(COALESCE(zona,'')) ILIKE %s"
        where += ")"
        params.extend([t, t, t, t, t])

    return where, params


def listar_propiedades(page: int = 1, page_size: int = 50, filtros: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    conn = _db.get_connection()
    cur = conn.cursor()
    try:
        where, params = _build_where(None, filtros)
        offset = max(0, (int(page) - 1) * int(page_size))
        cur.execute(
            f"SELECT * FROM propiedades {where} ORDER BY id DESC LIMIT %s OFFSET %s",
            params + [int(page_size), offset],
        )
        rows = cur.fetchall() or []
        return [_row_to_dict(cur, r) for r in rows]
    finally:
        cur.close()
        conn.close()


def buscar_propiedades(texto: str, page: int = 1, page_size: int = 50, filtros: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    conn = _db.get_connection()
    cur = conn.cursor()
    try:
        where, params = _build_where(texto, filtros)
        offset = max(0, (int(page) - 1) * int(page_size))
        cur.execute(
            f"SELECT * FROM propiedades {where} ORDER BY id DESC LIMIT %s OFFSET %s",
            params + [int(page_size), offset],
        )
        rows = cur.fetchall() or []
        return [_row_to_dict(cur, r) for r in rows]
    finally:
        cur.close()
        conn.close()


def contar_propiedades(texto: Optional[str] = None, filtros: Optional[Dict[str, Any]] = None) -> int:
    conn = _db.get_connection()
    cur = conn.cursor()
    try:
        where, params = _build_where(texto, filtros)
        cur.execute(f"SELECT COUNT(*) FROM propiedades {where}", params)
        row = cur.fetchone()
        return int(row[0]) if row else 0
    finally:
        cur.close()
        conn.close()
