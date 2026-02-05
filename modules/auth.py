"""Modulo de autenticacion con MySQL (tabla `asesores`).

Usa `database.db.get_connection()` para operar contra la tabla `asesores`.
Mantiene compatibilidad con la UI (login y cambio de password).

API:
- `auth_manager.login(username, password)` -> (bool, usuario_publico, mensaje)
- `auth_manager.requiere_cambio_password()` -> bool
- `auth_manager.cambiar_password(...)` -> None
- `auth_manager.resetear_password(user_id, password_nueva)` -> None (solo admin)
- `auth_manager.crear_usuario(datos)` -> int
- `auth_manager.get_current_user()` -> dict | None
- `auth_manager.is_admin()` -> bool
"""
from __future__ import annotations

import bcrypt
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple, Any

from database import db as _db

LOG = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


class AuthManager:
    """Gestor de autenticacion con BD.

    Mantiene el usuario autenticado en memoria para operaciones posteriores
    como `requiere_cambio_password()`.
    """

    def __init__(self) -> None:
        self._current_user: Optional[Dict[str, Any]] = None

    # -------------------------- DB helpers --------------------------
    def _get_conn(self):
        return _db.get_connection()

    def _fetch_asesor_by_username_db(self, username: str) -> Optional[Dict[str, Any]]:
        conn = None
        cur = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, username, password_hash, rol, nombres, apellidos, activo, requiere_cambio_password, ultimo_acceso FROM asesores WHERE username=%s",
                (username,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "username": row[1],
                "password_hash": row[2],
                "rol": row[3],
                "nombres": row[4],
                "apellidos": row[5],
                "activo": bool(row[6]),
                "requiere_cambio_password": bool(row[7]),
                "ultimo_acceso": row[8],
            }
        except Exception:
            LOG.exception("Error consultando asesor por username en BD")
            raise
        finally:
            try:
                if cur is not None:
                    cur.close()
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def _fetch_password_hash_by_id(self, asesor_id: int) -> Optional[str]:
        conn = None
        cur = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT password_hash FROM asesores WHERE id=%s", (asesor_id,))
            row = cur.fetchone()
            if not row:
                return None
            return row[0]
        except Exception:
            LOG.exception("Error consultando password_hash por id")
            raise
        finally:
            try:
                if cur is not None:
                    cur.close()
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def _update_ultimo_acceso_db(self, asesor_id: int) -> None:
        conn = None
        cur = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            now = datetime.utcnow()
            cur.execute("UPDATE asesores SET ultimo_acceso=%s WHERE id=%s", (now, asesor_id))
            conn.commit()
        except Exception:
            LOG.exception("No se pudo actualizar ultimo_acceso en BD")
            raise
        finally:
            try:
                if cur is not None:
                    cur.close()
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def _update_password_db(self, asesor_id: int, password_hash: str, requiere_cambio: bool = False) -> None:
        conn = None
        cur = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "UPDATE asesores SET password_hash=%s, requiere_cambio_password=%s WHERE id=%s",
                (password_hash, int(bool(requiere_cambio)), asesor_id),
            )
            conn.commit()
        except Exception:
            LOG.exception("No se pudo actualizar contrasena en BD")
            raise
        finally:
            try:
                if cur is not None:
                    cur.close()
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def _insert_usuario_db(self, datos: Dict[str, Any]) -> int:
        conn = None
        cur = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO asesores (username, password_hash, rol, nombres, apellidos, activo, requiere_cambio_password, ultimo_acceso) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    datos.get("username"),
                    datos.get("password_hash"),
                    datos.get("rol", "asesor"),
                    datos.get("nombres", ""),
                    datos.get("apellidos", ""),
                    int(bool(datos.get("activo", True))),
                    int(bool(datos.get("requiere_cambio_password", False))),
                    datos.get("ultimo_acceso"),
                ),
            )
            conn.commit()
            new_id = cur.lastrowid if hasattr(cur, "lastrowid") else None
            return int(new_id) if new_id is not None else 0
        except Exception:
            LOG.exception("No se pudo insertar usuario en BD")
            raise
        finally:
            try:
                if cur is not None:
                    cur.close()
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    # -------------------------- Public API --------------------------
    def login(self, username: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Intenta autenticar al usuario.

        Retorna (exito, usuario_publico, mensaje_error).
        """
        try:
            asesor = self._fetch_asesor_by_username_db(username)
            if asesor is None or not asesor.get("activo", False):
                return False, None, "Usuario no encontrado o inactivo."
            if not _verify_password(password, asesor["password_hash"]):
                return False, None, "Usuario o contrasena invalidos."

            try:
                self._update_ultimo_acceso_db(asesor["id"])
            except Exception:
                LOG.exception("No se pudo actualizar ultimo acceso despues de login")

            self._current_user = {
                "id": asesor["id"],
                "username": asesor["username"],
                "rol": asesor.get("rol", "asesor"),
                "nombres": asesor.get("nombres"),
                "apellidos": asesor.get("apellidos"),
                "requiere_cambio_password": asesor.get("requiere_cambio_password", False),
            }
            usuario_publico = {"username": asesor["username"], "role": asesor.get("rol", "asesor")}
            return True, usuario_publico, None
        except Exception:
            LOG.exception("Error durante login con BD")
            return False, None, "Error inesperado al autenticar."

    def requiere_cambio_password(self) -> bool:
        """Indica si el usuario actualmente autenticado debe cambiar su contrasena."""
        if not self._current_user:
            return False
        return bool(self._current_user.get("requiere_cambio_password", False))

    def cambiar_password(self, *args: Any) -> None:
        """Cambia password.

        Soporta dos firmas para compatibilidad con la UI:
        - (username, nueva_password) para primer cambio sin password actual.
        - (user_id, password_actual, password_nueva) con validacion.
        """
        if len(args) == 2:
            username, nueva_password = args
            if not self._current_user:
                raise PermissionError("Sesion no iniciada")
            if str(self._current_user.get("username")) != str(username):
                raise PermissionError("No autorizado")
            if not self._current_user.get("requiere_cambio_password", False):
                raise PermissionError("Cambio no permitido sin password actual")
            new_hash = _hash_password(str(nueva_password))
            self._update_password_db(int(self._current_user["id"]), new_hash, requiere_cambio=False)
            self._current_user["requiere_cambio_password"] = False
            return

        if len(args) == 3:
            asesor_id, password_actual, password_nueva = args
            stored_hash = self._fetch_password_hash_by_id(int(asesor_id))
            if not stored_hash:
                raise ValueError("Usuario no existe")
            if not _verify_password(str(password_actual), stored_hash):
                raise ValueError("Contrasena actual invalida")
            new_hash = _hash_password(str(password_nueva))
            self._update_password_db(int(asesor_id), new_hash, requiere_cambio=False)
            if self._current_user and int(self._current_user.get("id", 0)) == int(asesor_id):
                self._current_user["requiere_cambio_password"] = False
            return

        raise TypeError("cambiar_password espera 2 o 3 argumentos")

    def cambiar_password_by_id(self, asesor_id: int, password_actual: str, password_nueva: str) -> None:
        """Alias explicito para cambio con password actual."""
        self.cambiar_password(asesor_id, password_actual, password_nueva)

    def resetear_password(self, asesor_id: int, password_nueva: str) -> None:
        """Resetea la contrasena de un asesor y marca requiere_cambio_password=TRUE.

        Solo permitido para usuarios admin.
        """
        if not self.is_admin():
            raise PermissionError("Permisos insuficientes")
        new_hash = _hash_password(password_nueva)
        self._update_password_db(asesor_id, new_hash, requiere_cambio=True)

    def crear_usuario(self, datos: Dict[str, Any]) -> int:
        """Crea un nuevo asesor. `datos` debe contener al menos `username` y `password`.

        Retorna el `id` del nuevo usuario.
        """
        username = datos.get("username")
        password = datos.get("password")
        if not username or not password:
            raise ValueError("username y password son obligatorios")

        conn = None
        cur = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id FROM asesores WHERE username=%s", (username,))
            if cur.fetchone():
                raise ValueError("Username ya existe")
        except Exception:
            LOG.exception("Error validando username en BD")
            raise
        finally:
            try:
                if cur is not None:
                    cur.close()
                if conn is not None:
                    conn.close()
            except Exception:
                pass

        datos_db = {
            "username": username,
            "password_hash": _hash_password(password),
            "rol": datos.get("rol", "asesor"),
            "nombres": datos.get("nombres", ""),
            "apellidos": datos.get("apellidos", ""),
            "activo": datos.get("activo", True),
            "requiere_cambio_password": datos.get("requiere_cambio_password", False),
            "ultimo_acceso": None,
        }
        return self._insert_usuario_db(datos_db)

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Retorna el usuario autenticado (publico) o None."""
        if not self._current_user:
            return None
        return self._current_user.copy()

    def is_admin(self) -> bool:
        """Indica si el usuario autenticado tiene rol admin."""
        if not self._current_user:
            return False
        return str(self._current_user.get("rol", "")).lower() == "admin"


auth_manager = AuthManager()
