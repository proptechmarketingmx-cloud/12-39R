"""Lógica de clientes - PostgreSQL.

Provee funciones:
- find_by_curp(curp)
- save(cliente)
- eliminar_cliente(cliente_id) (hard delete)
- listar_clientes(page, page_size, asesor_id, filtros)
- buscar_clientes(texto, page, page_size, asesor_id, filtros)
- contar_clientes(texto, asesor_id, filtros)
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
    if s.lower() == "none":
        return None
    return s if s else None


def _to_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    if isinstance(value, str) and value.strip().lower() == "none":
        return None
    try:
        return int(value)
    except Exception:
        return None


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, str) and value.strip().lower() == "none":
        return None
    try:
        return float(value)
    except Exception:
        return None


def _to_bool(value: Any) -> Optional[bool]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ("si", "sí", "true", "1", "y", "yes"):
        return True
    if s in ("no", "false", "0", "n"):
        return False
    return None


def _to_date_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return None
    s = str(value).strip()
    if not s or s.lower() == "none":
        return None
    # formato esperado YYYY-MM-DD
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s
    return None


def _row_to_dict(cur, row) -> Dict[str, Any]:
    cols = [c.name for c in cur.description]
    return {cols[i]: row[i] for i in range(len(cols))}


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and (value.strip() == "" or value.strip().lower() == "none"):
        return True
    return False


def _normalize_cliente(cliente: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(cliente)
    # Mapear campos de propiedad de interes
    if "pi_pais" in data and "interes_pais" not in data:
        data["interes_pais"] = data.get("pi_pais")
    if "pi_estado" in data and "interes_estado" not in data:
        data["interes_estado"] = data.get("pi_estado")
    if "pi_ciudad" in data and "interes_ciudad" not in data:
        data["interes_ciudad"] = data.get("pi_ciudad")
    if "pi_zona" in data and "interes_zona" not in data:
        data["interes_zona"] = data.get("pi_zona")
    if "pi_tipo" in data and "interes_tipo" not in data:
        data["interes_tipo"] = data.get("pi_tipo")
    return data


def find_by_curp(curp: str) -> Optional[Dict[str, Any]]:
    """Busca y retorna un cliente por CURP, o None si no existe."""
    curp = _clean_str(curp)
    if not curp:
        return None
    conn = _db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM clientes WHERE curp=%s LIMIT 1", (curp,))
        row = cur.fetchone()
        if not row:
            return None
        return _row_to_dict(cur, row)
    finally:
        cur.close()
        conn.close()


def save(cliente: Dict[str, Any] | Mapping[str, Any]) -> Dict[str, Any]:
    """Guarda o actualiza un cliente en PostgreSQL.

    - Si `cliente` contiene `id` intenta actualizar el registro.
    - Si no tiene `id`, inserta y devuelve con id.
    """
    if not isinstance(cliente, dict):
        if isinstance(cliente, Mapping):
            cliente = dict(cliente)
        elif hasattr(cliente, "__dict__"):
            cliente = dict(vars(cliente))
        else:
            raise ValueError("Cliente debe ser un diccionario o Mapping")

    data = _normalize_cliente(cliente)

    # Campos permitidos
    fields = {
        "activo",
        "primer_nombre",
        "segundo_nombre",
        "apellido_paterno",
        "apellido_materno",
        "curp",
        "fecha_nacimiento",
        "edad",
        "genero",
        "estado_civil",
        "telefono",
        "correo",
        "pais",
        "estado",
        "ciudad",
        "zona",
        "ocupacion",
        "antiguedad_laboral",
        "ingreso_mensual",
        "tipo_credito",
        "buro_credito",
        "presupuesto_min",
        "presupuesto_max",
        "nivel_educativo",
        "hijos",
        "metodo_captacion",
        "origen_captacion",
        "interes_pais",
        "interes_estado",
        "interes_ciudad",
        "interes_zona",
        "interes_tipo",
        "zona_interes",
        "deudor_alimenticio",
        "propiedades_previas",
        "num_propiedades_previas",
        "edad_adquisicion",
        "estado_cliente",
        "tipo_cliente",
        "etapa_embudo",
        "score",
        "asesor_id",
    }

    payload: Dict[str, Any] = {}
    for k in fields:
        if k in data:
            payload[k] = data.get(k)

    # Normalizaciones
    payload["curp"] = _clean_str(payload.get("curp"))
    payload["primer_nombre"] = _clean_str(payload.get("primer_nombre"))
    payload["segundo_nombre"] = _clean_str(payload.get("segundo_nombre"))
    payload["apellido_paterno"] = _clean_str(payload.get("apellido_paterno"))
    payload["apellido_materno"] = _clean_str(payload.get("apellido_materno"))
    payload["telefono"] = _clean_str(payload.get("telefono"))
    payload["correo"] = _clean_str(payload.get("correo"))
    payload["fecha_nacimiento"] = _to_date_str(payload.get("fecha_nacimiento"))
    payload["pais"] = _clean_str(payload.get("pais"))
    payload["estado"] = _clean_str(payload.get("estado"))
    payload["ciudad"] = _clean_str(payload.get("ciudad"))
    payload["zona"] = _clean_str(payload.get("zona"))
    payload["ocupacion"] = _clean_str(payload.get("ocupacion"))
    payload["antiguedad_laboral"] = _clean_str(payload.get("antiguedad_laboral"))
    payload["tipo_credito"] = _clean_str(payload.get("tipo_credito"))
    payload["buro_credito"] = _clean_str(payload.get("buro_credito"))
    payload["nivel_educativo"] = _clean_str(payload.get("nivel_educativo"))
    payload["metodo_captacion"] = _clean_str(payload.get("metodo_captacion"))
    payload["origen_captacion"] = _clean_str(payload.get("origen_captacion"))
    payload["interes_pais"] = _clean_str(payload.get("interes_pais"))
    payload["interes_estado"] = _clean_str(payload.get("interes_estado"))
    payload["interes_ciudad"] = _clean_str(payload.get("interes_ciudad"))
    payload["interes_zona"] = _clean_str(payload.get("interes_zona"))
    payload["interes_tipo"] = _clean_str(payload.get("interes_tipo"))
    payload["zona_interes"] = _clean_str(payload.get("zona_interes"))
    payload["estado_cliente"] = _clean_str(payload.get("estado_cliente"))
    payload["tipo_cliente"] = _clean_str(payload.get("tipo_cliente"))
    payload["etapa_embudo"] = _clean_str(payload.get("etapa_embudo"))

    payload["edad"] = _to_int(payload.get("edad"))
    payload["hijos"] = _to_int(payload.get("hijos"))
    payload["num_propiedades_previas"] = _to_int(payload.get("num_propiedades_previas"))
    payload["edad_adquisicion"] = _to_int(payload.get("edad_adquisicion"))
    payload["score"] = _to_int(payload.get("score"))
    payload["asesor_id"] = _to_int(payload.get("asesor_id"))

    payload["ingreso_mensual"] = _to_float(payload.get("ingreso_mensual"))
    payload["presupuesto_min"] = _to_float(payload.get("presupuesto_min"))
    payload["presupuesto_max"] = _to_float(payload.get("presupuesto_max"))

    payload["deudor_alimenticio"] = _to_bool(payload.get("deudor_alimenticio"))
    payload["propiedades_previas"] = _to_bool(payload.get("propiedades_previas"))

    if "activo" in payload:
        payload["activo"] = bool(payload.get("activo"))

    conn = _db.get_connection()
    cur = conn.cursor()
    try:
        cliente_id_raw = data.get("id")
        if cliente_id_raw is not None and str(cliente_id_raw).strip() != "":
            cliente_id = int(cliente_id_raw)
            update_payload: Dict[str, Any] = {}
            for k in fields:
                if k in data:
                    val = payload.get(k)
                    update_payload[k] = None if _is_empty(val) else val
            if not update_payload:
                return {"id": cliente_id}
            set_clause = ", ".join([f"{k}=%s" for k in update_payload.keys()])
            values = list(update_payload.values()) + [cliente_id]
            cur.execute(f"UPDATE clientes SET {set_clause} WHERE id=%s RETURNING id", values)
            row = cur.fetchone()
            conn.commit()
            return {"id": row[0], **update_payload} if row else {"id": cliente_id, **update_payload}

        # Insert sin id (si viene id en el payload, se ignora)
        insert_payload = {k: v for k, v in payload.items() if k != "id" and not _is_empty(v)}
        if not insert_payload:
            # Insertar solo defaults si no hay datos
            cur.execute("INSERT INTO clientes DEFAULT VALUES RETURNING id")
            row = cur.fetchone()
            conn.commit()
            return {"id": row[0]} if row else {}
        cols = ", ".join(insert_payload.keys())
        placeholders = ", ".join(["%s"] * len(insert_payload))
        cur.execute(
            f"INSERT INTO clientes ({cols}) VALUES ({placeholders}) RETURNING id",
            list(insert_payload.values()),
        )
        row = cur.fetchone()
        conn.commit()
        return {"id": row[0], **insert_payload} if row else insert_payload
    finally:
        cur.close()
        conn.close()


def eliminar_cliente(cliente_id: int) -> bool:
    """Elimina un cliente (hard delete)."""
    try:
        cid = int(cliente_id)
    except Exception:
        raise ValueError("ID de cliente inválido")

    conn = _db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM clientes WHERE id=%s", (cid,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        cur.close()
        conn.close()


def _build_where(texto: Optional[str], asesor_id: Optional[int], filtros: Optional[Dict[str, Any]]) -> tuple[str, List[Any]]:
    where = "WHERE 1=1"
    params: List[Any] = []

    if asesor_id:
        where += " AND asesor_id=%s"
        params.append(int(asesor_id))

    if filtros:
        estado = filtros.get("estado_cliente")
        tipo = filtros.get("tipo_cliente")
        etapa = filtros.get("etapa_embudo")
        origen = filtros.get("origen_captacion")
        pres_min = filtros.get("presupuesto_min")
        pres_max = filtros.get("presupuesto_max")
        if estado:
            where += " AND estado_cliente=%s"
            params.append(estado)
        if tipo:
            where += " AND tipo_cliente=%s"
            params.append(tipo)
        if etapa:
            where += " AND etapa_embudo=%s"
            params.append(etapa)
        if origen:
            where += " AND origen_captacion=%s"
            params.append(origen)
        if pres_min is not None:
            where += " AND presupuesto_min >= %s"
            params.append(float(pres_min))
        if pres_max is not None:
            where += " AND presupuesto_max <= %s"
            params.append(float(pres_max))

    if texto:
        t = f"%{texto.lower()}%"
        where += " AND ("
        where += "LOWER(COALESCE(primer_nombre,'')) ILIKE %s OR "
        where += "LOWER(COALESCE(segundo_nombre,'')) ILIKE %s OR "
        where += "LOWER(COALESCE(apellido_paterno,'')) ILIKE %s OR "
        where += "LOWER(COALESCE(apellido_materno,'')) ILIKE %s OR "
        where += "LOWER(COALESCE(curp,'')) ILIKE %s OR "
        where += "LOWER(COALESCE(telefono,'')) ILIKE %s OR "
        where += "LOWER(COALESCE(correo,'')) ILIKE %s"
        where += ")"
        params.extend([t, t, t, t, t, t, t])

    return where, params


def listar_clientes(page: int = 1, page_size: int = 50, asesor_id: Optional[int] = None,
                    filtros: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    conn = _db.get_connection()
    cur = conn.cursor()
    try:
        where, params = _build_where(None, asesor_id, filtros)
        offset = max(0, (int(page) - 1) * int(page_size))
        cur.execute(
            f"SELECT * FROM clientes {where} ORDER BY fecha_registro DESC, id DESC LIMIT %s OFFSET %s",
            params + [int(page_size), offset],
        )
        rows = cur.fetchall() or []
        return [_row_to_dict(cur, r) for r in rows]
    finally:
        cur.close()
        conn.close()


def buscar_clientes(texto: str, page: int = 1, page_size: int = 50, asesor_id: Optional[int] = None,
                    filtros: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    conn = _db.get_connection()
    cur = conn.cursor()
    try:
        where, params = _build_where(texto, asesor_id, filtros)
        offset = max(0, (int(page) - 1) * int(page_size))
        cur.execute(
            f"SELECT * FROM clientes {where} ORDER BY fecha_registro DESC, id DESC LIMIT %s OFFSET %s",
            params + [int(page_size), offset],
        )
        rows = cur.fetchall() or []
        return [_row_to_dict(cur, r) for r in rows]
    finally:
        cur.close()
        conn.close()


def contar_clientes(texto: Optional[str] = None, asesor_id: Optional[int] = None,
                    filtros: Optional[Dict[str, Any]] = None) -> int:
    conn = _db.get_connection()
    cur = conn.cursor()
    try:
        where, params = _build_where(texto, asesor_id, filtros)
        cur.execute(f"SELECT COUNT(*) FROM clientes {where}", params)
        row = cur.fetchone()
        return int(row[0]) if row else 0
    finally:
        cur.close()
        conn.close()
