"""Modulo CRUD de asesores (tabla `asesores`).

Expone una clase `AsesoresManager` con operaciones basicas y validaciones
para permisos y unicidad de username.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import bcrypt

from database import db as _db

try:
    from modules.auth import auth_manager
except Exception:
    auth_manager = None  # type: ignore

LOG = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


class AsesoresManager:
    """Gestiona asesores en BD.

    Todas las operaciones usan PostgreSQL via `database.db.get_connection()`.
    """

    def _get_conn(self):
        return _db.get_connection()

    def _es_admin_por_id(self, asesor_id: int) -> bool:
        conn = None
        cur = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT rol FROM asesores WHERE id=%s", (asesor_id,))
            row = cur.fetchone()
            if not row:
                return False
            return str(row[0]).lower() == "admin"
        except Exception:
            LOG.exception("Error validando rol de asesor")
            return False
        finally:
            try:
                if cur is not None:
                    cur.close()
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def _get_current_user(self) -> Optional[Dict[str, Any]]:
        if auth_manager is None:
            return None
        return auth_manager.get_current_user()

    def _validar_permiso_admin(self) -> None:
        usuario = self._get_current_user()
        if not usuario:
            raise PermissionError("Sesion no iniciada")
        if not auth_manager.is_admin():
            raise PermissionError("Permisos insuficientes")

    def _validar_permiso_admin_o_mismo(self, asesor_id: int) -> None:
        usuario = self._get_current_user()
        if not usuario:
            raise PermissionError("Sesion no iniciada")
        if auth_manager.is_admin():
            return
        if int(usuario.get("id", 0)) != int(asesor_id):
            raise PermissionError("Permisos insuficientes")

    def validar_username_unico(self, username: str, excluir_id: Optional[int] = None) -> bool:
        """Valida que el username no exista en BD.

        Retorna True si es unico.
        """
        if not username:
            return False
        conn = None
        cur = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            if excluir_id is None:
                cur.execute("SELECT id FROM asesores WHERE username=%s", (username,))
            else:
                cur.execute("SELECT id FROM asesores WHERE username=%s AND id<>%s", (username, excluir_id))
            return cur.fetchone() is None
        except Exception:
            LOG.exception("Error validando username unico")
            return False
        finally:
            try:
                if cur is not None:
                    cur.close()
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def crear_asesor(self, datos: Dict[str, Any], creador_id: int) -> int:
        """Crea un asesor.

        Requiere que el creador sea admin. Retorna el id creado.
        """
        if not self._es_admin_por_id(int(creador_id)):
            raise PermissionError("El creador no tiene permisos de admin")

        username = str(datos.get("username", "")).strip()
        password = str(datos.get("password", "")).strip()
        if not username or not password:
            raise ValueError("username y password son obligatorios")
        if not self.validar_username_unico(username):
            raise ValueError("Username ya existe")

        datos_db = {
            "username": username,
            "password_hash": _hash_password(password),
            "rol": datos.get("rol", "asesor"),
            "nombres": datos.get("nombres", ""),
            "apellidos": datos.get("apellidos", ""),
            "activo": bool(datos.get("activo", True)),
            "requiere_cambio_password": bool(datos.get("requiere_cambio_password", False)),
            "ultimo_acceso": None,
            "primer_nombre": datos.get("primer_nombre"),
            "segundo_nombre": datos.get("segundo_nombre"),
            "apellido_paterno": datos.get("apellido_paterno"),
            "apellido_materno": datos.get("apellido_materno"),
            "curp": datos.get("curp"),
            "fecha_nacimiento": datos.get("fecha_nacimiento"),
            "edad": datos.get("edad"),
            "genero": datos.get("genero"),
            "estado_civil": datos.get("estado_civil"),
            "telefono": datos.get("telefono"),
            "correo": datos.get("correo"),
            "pais": datos.get("pais"),
            "estado": datos.get("estado"),
            "ciudad": datos.get("ciudad"),
            "zona": datos.get("zona"),
            "inmobiliaria": datos.get("inmobiliaria"),
            "area": datos.get("area"),
            "anos_experiencia": datos.get("anos_experiencia"),
            "comision_asignada": datos.get("comision_asignada"),
            "fecha_ingreso": datos.get("fecha_ingreso"),
        }

        conn = None
        cur = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO asesores (username, password_hash, rol, nombres, apellidos, activo, requiere_cambio_password, ultimo_acceso, primer_nombre, segundo_nombre, apellido_paterno, apellido_materno, curp, fecha_nacimiento, edad, genero, estado_civil, telefono, correo, pais, estado, ciudad, zona, inmobiliaria, area, anos_experiencia, comision_asignada, fecha_ingreso) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                (
                    datos_db["username"],
                    datos_db["password_hash"],
                    datos_db["rol"],
                    datos_db["nombres"],
                    datos_db["apellidos"],
                    datos_db["activo"],
                    datos_db["requiere_cambio_password"],
                    datos_db["ultimo_acceso"],
                    datos_db["primer_nombre"],
                    datos_db["segundo_nombre"],
                    datos_db["apellido_paterno"],
                    datos_db["apellido_materno"],
                    datos_db["curp"],
                    datos_db["fecha_nacimiento"],
                    datos_db["edad"],
                    datos_db["genero"],
                    datos_db["estado_civil"],
                    datos_db["telefono"],
                    datos_db["correo"],
                    datos_db["pais"],
                    datos_db["estado"],
                    datos_db["ciudad"],
                    datos_db["zona"],
                    datos_db["inmobiliaria"],
                    datos_db["area"],
                    datos_db["anos_experiencia"],
                    datos_db["comision_asignada"],
                    datos_db["fecha_ingreso"],
                ),
            )
            new_id = cur.fetchone()
            conn.commit()
            return int(new_id[0]) if new_id else 0
        except Exception:
            LOG.exception("No se pudo crear asesor")
            raise
        finally:
            try:
                if cur is not None:
                    cur.close()
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def editar_asesor(self, asesor_id: int, datos: Dict[str, Any]) -> None:
        """Edita un asesor.

        Permite admin o el mismo asesor.
        """
        self._validar_permiso_admin_o_mismo(int(asesor_id))

        permitidos = {
            "username",
            "rol",
            "nombres",
            "apellidos",
            "activo",
            "requiere_cambio_password",
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
            "inmobiliaria",
            "area",
            "anos_experiencia",
            "comision_asignada",
            "fecha_ingreso",
        }
        updates = {k: v for k, v in datos.items() if k in permitidos}
        if not updates:
            raise ValueError("No hay campos para actualizar")

        if "username" in updates:
            username = str(updates.get("username", "")).strip()
            if not username:
                raise ValueError("username no puede estar vacio")
            if not self.validar_username_unico(username, excluir_id=int(asesor_id)):
                raise ValueError("Username ya existe")
            updates["username"] = username

        if "activo" in updates:
            updates["activo"] = bool(updates["activo"])
        if "requiere_cambio_password" in updates:
            updates["requiere_cambio_password"] = bool(updates["requiere_cambio_password"])

        set_clause = ", ".join([f"{k}=%s" for k in updates.keys()])
        valores = list(updates.values()) + [int(asesor_id)]

        conn = None
        cur = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(f"UPDATE asesores SET {set_clause} WHERE id=%s", tuple(valores))
            conn.commit()
        except Exception:
            LOG.exception("No se pudo editar asesor")
            raise
        finally:
            try:
                if cur is not None:
                    cur.close()
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def eliminar_asesor(self, asesor_id: int) -> None:
        """Elimina un asesor (soft delete)."""
        self._validar_permiso_admin_o_mismo(int(asesor_id))

        conn = None
        cur = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("UPDATE asesores SET activo=%s WHERE id=%s", (False, int(asesor_id)))
            conn.commit()
        except Exception:
            LOG.exception("No se pudo eliminar asesor")
            raise
        finally:
            try:
                if cur is not None:
                    cur.close()
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def obtener_asesor(self, asesor_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un asesor por id."""
        conn = None
        cur = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, username, rol, nombres, apellidos, activo, requiere_cambio_password, ultimo_acceso, primer_nombre, segundo_nombre, apellido_paterno, apellido_materno, curp, fecha_nacimiento, edad, genero, estado_civil, telefono, correo, pais, estado, ciudad, zona, inmobiliaria, area, anos_experiencia, comision_asignada, fecha_ingreso FROM asesores WHERE id=%s",
                (int(asesor_id),),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "username": row[1],
                "rol": row[2],
                "nombres": row[3],
                "apellidos": row[4],
                "activo": bool(row[5]),
                "requiere_cambio_password": bool(row[6]),
                "ultimo_acceso": row[7],
                "primer_nombre": row[8],
                "segundo_nombre": row[9],
                "apellido_paterno": row[10],
                "apellido_materno": row[11],
                "curp": row[12],
                "fecha_nacimiento": row[13],
                "edad": row[14],
                "genero": row[15],
                "estado_civil": row[16],
                "telefono": row[17],
                "correo": row[18],
                "pais": row[19],
                "estado": row[20],
                "ciudad": row[21],
                "zona": row[22],
                "inmobiliaria": row[23],
                "area": row[24],
                "anos_experiencia": row[25],
                "comision_asignada": row[26],
                "fecha_ingreso": row[27],
            }
        except Exception:
            LOG.exception("No se pudo obtener asesor")
            raise
        finally:
            try:
                if cur is not None:
                    cur.close()
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def listar_asesores(self, activo: bool = True) -> List[Dict[str, Any]]:
        """Lista asesores, filtrando por estado activo si aplica."""
        conn = None
        cur = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            if activo is None:
                cur.execute(
                    "SELECT id, username, rol, nombres, apellidos, activo, requiere_cambio_password, ultimo_acceso, primer_nombre, segundo_nombre, apellido_paterno, apellido_materno, curp, fecha_nacimiento, edad, genero, estado_civil, telefono, correo, pais, estado, ciudad, zona, inmobiliaria, area, anos_experiencia, comision_asignada, fecha_ingreso FROM asesores"
                )
            else:
                cur.execute(
                    "SELECT id, username, rol, nombres, apellidos, activo, requiere_cambio_password, ultimo_acceso, primer_nombre, segundo_nombre, apellido_paterno, apellido_materno, curp, fecha_nacimiento, edad, genero, estado_civil, telefono, correo, pais, estado, ciudad, zona, inmobiliaria, area, anos_experiencia, comision_asignada, fecha_ingreso FROM asesores WHERE activo=%s",
                    (int(bool(activo)),),
                )
            rows = cur.fetchall() or []
            data: List[Dict[str, Any]] = []
            for row in rows:
                data.append(
                    {
                        "id": row[0],
                        "username": row[1],
                        "rol": row[2],
                        "nombres": row[3],
                        "apellidos": row[4],
                        "activo": bool(row[5]),
                        "requiere_cambio_password": bool(row[6]),
                        "ultimo_acceso": row[7],
                        "primer_nombre": row[8],
                        "segundo_nombre": row[9],
                        "apellido_paterno": row[10],
                        "apellido_materno": row[11],
                        "curp": row[12],
                        "fecha_nacimiento": row[13],
                        "edad": row[14],
                        "genero": row[15],
                        "estado_civil": row[16],
                        "telefono": row[17],
                        "correo": row[18],
                        "pais": row[19],
                        "estado": row[20],
                        "ciudad": row[21],
                        "zona": row[22],
                        "inmobiliaria": row[23],
                        "area": row[24],
                        "anos_experiencia": row[25],
                        "comision_asignada": row[26],
                        "fecha_ingreso": row[27],
                    }
                )
            return data
        except Exception:
            LOG.exception("No se pudo listar asesores")
            raise
        finally:
            try:
                if cur is not None:
                    cur.close()
                if conn is not None:
                    conn.close()
            except Exception:
                pass


asesores_manager = AsesoresManager()
