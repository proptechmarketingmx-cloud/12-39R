"""Módulo de autenticación con soporte MySQL (tabla `asesores`).

Intenta usar `database.db.get_connection()` para operaciones en la tabla
`asesores`. Si la conexión o la tabla no están disponibles lanzará
excepciones en tiempo de ejecución; para facilitar desarrollo el módulo
incluye un fallback al store JSON local cuando la BD no está operativa.

API compatible con la versión anterior (para no romper la UI):
- `auth_manager.login(username, password)` -> (bool, usuario_publico, mensaje)
- `auth_manager.requiere_cambio_password()` -> bool
- `auth_manager.cambiar_password(username, nueva_password)` -> None
- también expone métodos adicionales para administración: crear_usuario,
  cambiar_password_by_id, resetear_password, get_current_user, is_admin
"""
from __future__ import annotations

import bcrypt
import json
import logging
import os
from datetime import datetime
from typing import Dict, Optional, Tuple, Any

LOG = logging.getLogger(__name__)

_STORE_PATH = os.path.join(os.path.dirname(__file__), "_auth_store.json")

try:
    from database import db as _db
except Exception:
    _db = None  # type: ignore


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _load_store() -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(_STORE_PATH):
        return {}
    try:
        with open(_STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        LOG.exception("No se pudo leer el store de autenticación (fallback)")
        return {}


def _save_store(store: Dict[str, Dict[str, Any]]) -> None:
    try:
        with open(_STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2, ensure_ascii=False)
    except Exception:
        LOG.exception("No se pudo guardar el store de autenticación (fallback)")


class AuthManager:
    """Gestor de autenticación que prioriza MySQL y cae a JSON en desarrollo.

    Mantiene el usuario autenticado en memoria para operaciones posteriores
    como `requiere_cambio_password()`.
    """

    def __init__(self) -> None:
        self._current_user: Optional[Dict[str, Any]] = None
        self._use_db = _db is not None
        if not self._use_db:
            LOG.warning("database.db no disponible: usando fallback JSON para auth")
        # Ensure JSON admin exists for fallback
        self._ensure_default_admin_fallback()

    # -------------------------- Fallback helpers --------------------------
    def _ensure_default_admin_fallback(self) -> None:
        store = _load_store()
        if "admin" not in store:
            store["admin"] = {
                "id": 1,
                "username": "admin",
                "password_hash": _hash_password("admin123"),
                "rol": "admin",
                "nombres": "Administrador",
                "apellidos": "Sistema",
                "activo": True,
                "requiere_cambio_password": True,
                "ultimo_acceso": None,
            }
            _save_store(store)

    # -------------------------- DB helpers --------------------------
    def _get_conn(self):
        if not self._use_db or _db is None:
            raise RuntimeError("Base de datos no disponible")
        return _db.get_connection()

    def _fetch_asesor_by_username_db(self, username: str) -> Optional[Dict[str, Any]]:
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, username, password_hash, rol, nombres, apellidos, activo, requiere_cambio_password, ultimo_acceso FROM asesores WHERE username=%s",
                (username,),
            )
            row = cur.fetchone()
            cur.close()
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
            return None

    def _update_ultimo_acceso_db(self, asesor_id: int) -> None:
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            now = datetime.utcnow()
            cur.execute("UPDATE asesores SET ultimo_acceso=%s WHERE id=%s", (now, asesor_id))
            conn.commit()
            cur.close()
        except Exception:
            LOG.exception("No se pudo actualizar ultimo_acceso en BD")

    def _update_password_db(self, asesor_id: int, password_hash: str, requiere_cambio: bool = False) -> None:
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "UPDATE asesores SET password_hash=%s, requiere_cambio_password=%s WHERE id=%s",
                (password_hash, int(bool(requiere_cambio)), asesor_id),
            )
            conn.commit()
            cur.close()
        except Exception:
            LOG.exception("No se pudo actualizar contraseña en BD")

    def _insert_usuario_db(self, datos: Dict[str, Any]) -> int:
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
            cur.close()
            return int(new_id) if new_id is not None else 0
        except Exception:
            LOG.exception("No se pudo insertar usuario en BD")
            raise

    # -------------------------- Public API --------------------------
    def login(self, username: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Intenta autenticar al usuario.

        Retorna (exito, usuario_publico, mensaje_error).
        """
        # Intentar BD primero
        if self._use_db:
            try:
                asesor = self._fetch_asesor_by_username_db(username)
                # Si no existe en BD, no devolvemos error inmediato: permitimos
                # intentar el fallback JSON (útil en entornos de desarrollo).
                if asesor is None:
                    raise LookupError("Sin registro en BD")

                if not asesor.get("activo", False):
                    return False, None, "Usuario no encontrado o inactivo."
                if not _verify_password(password, asesor["password_hash"]):
                    return False, None, "Usuario o contraseña inválidos."

                # Actualizar ultimo acceso
                try:
                    self._update_ultimo_acceso_db(asesor["id"])
                except Exception:
                    LOG.exception("No se pudo actualizar ultimo acceso después de login")

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
            except LookupError:
                # No existe en BD: continuar a fallback
                LOG.info("Usuario no encontrado en BD, probando fallback JSON")
            except Exception:
                LOG.exception("Error durante login con BD; intentando fallback JSON")

        # Fallback a JSON store
        store = _load_store()
        user = store.get(username)
        if not user:
            return False, None, "Usuario no encontrado."
        if not _verify_password(password, user["password_hash"]):
            return False, None, "Usuario o contraseña inválidos."

        # Éxito fallback
        self._current_user = {"username": username, "rol": user.get("rol", "asesor"), "id": user.get("id")}
        usuario_publico = {"username": username, "role": user.get("rol", "asesor")}
        # actualizar ultimo acceso en fallback
        try:
            user["ultimo_acceso"] = datetime.utcnow().isoformat()
            store[username] = user
            _save_store(store)
        except Exception:
            LOG.exception("No se pudo actualizar ultimo_acceso en fallback")
        return True, usuario_publico, None

    def requiere_cambio_password(self) -> bool:
        """Indica si el usuario actualmente autenticado debe cambiar su contraseña."""
        if not self._current_user:
            return False
        return bool(self._current_user.get("requiere_cambio_password", False))

    def cambiar_password(self, username: str, nueva_password: str) -> None:
        """Compatibilidad: cambia contraseña por username (usa BD si está disponible)."""
        if self._use_db:
            asesor = self._fetch_asesor_by_username_db(username)
            if not asesor:
                raise ValueError("Usuario no existe")
            new_hash = _hash_password(nueva_password)
            self._update_password_db(asesor["id"], new_hash, requiere_cambio=False)
            # si el usuario en memoria coincide, actualizar flag
            if self._current_user and self._current_user.get("username") == username:
                self._current_user["requiere_cambio_password"] = False
            return

        # Fallback
        store = _load_store()
        if username not in store:
            raise ValueError("Usuario no existe")
        store[username]["password_hash"] = _hash_password(nueva_password)
        store[username]["requiere_cambio_password"] = False
        _save_store(store)

    def cambiar_password_by_id(self, asesor_id: int, password_actual: str, password_nueva: str) -> None:
        """Cambia la contraseña validando la actual (solo BD)."""
        if not self._use_db:
            raise RuntimeError("Operación disponible solo con BD")
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT password_hash FROM asesores WHERE id=%s", (asesor_id,))
            row = cur.fetchone()
            cur.close()
            if not row:
                raise ValueError("Usuario no existe")
            if not _verify_password(password_actual, row[0]):
                raise ValueError("Contraseña actual inválida")
            new_hash = _hash_password(password_nueva)
            self._update_password_db(asesor_id, new_hash, requiere_cambio=False)
        except Exception:
            LOG.exception("Error cambiando contraseña por id")
            raise

    def resetear_password(self, asesor_id: int, password_nueva: str, performed_by: Optional[int] = None) -> None:
        """Resetea la contraseña de un asesor y marca requiere_cambio_password=TRUE.

        `performed_by` puede ser el id del asesor que realiza la operación; se
        valida que tenga rol admin si la BD está disponible.
        """
        if self._use_db and performed_by is not None:
            try:
                # comprobar rol del performed_by
                conn = self._get_conn()
                cur = conn.cursor()
                cur.execute("SELECT rol FROM asesores WHERE id=%s", (performed_by,))
                r = cur.fetchone()
                cur.close()
                if not r or r[0] != "admin":
                    raise PermissionError("Permisos insuficientes")
            except Exception:
                LOG.exception("Validación de permisos falló")
                raise

        new_hash = _hash_password(password_nueva)
        if self._use_db:
            self._update_password_db(asesor_id, new_hash, requiere_cambio=True)
            return

        # fallback
        store = _load_store()
        for k, v in store.items():
            if int(v.get("id", 0)) == int(asesor_id):
                v["password_hash"] = new_hash
                v["requiere_cambio_password"] = True
                _save_store(store)
                return
        raise ValueError("Usuario no existe en fallback")

    def crear_usuario(self, datos: Dict[str, Any]) -> int:
        """Crea un nuevo asesor. `datos` debe contener al menos `username` y `password`.

        Retorna el `id` del nuevo usuario.
        """
        username = datos.get("username")
        password = datos.get("password")
        if not username or not password:
            raise ValueError("username y password son obligatorios")

        if self._use_db:
            # validar username único
            try:
                conn = self._get_conn()
                cur = conn.cursor()
                cur.execute("SELECT id FROM asesores WHERE username=%s", (username,))
                if cur.fetchone():
                    cur.close()
                    raise ValueError("Username ya existe")
                cur.close()
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
            except Exception:
                LOG.exception("Error creando usuario en BD")
                raise

        # fallback JSON
        store = _load_store()
        if username in store:
            raise ValueError("Username ya existe")
        new_id = max((int(v.get("id", 0)) for v in store.values()), default=0) + 1
        store[username] = {
            "id": new_id,
            "username": username,
            "password_hash": _hash_password(password),
            "rol": datos.get("rol", "asesor"),
            "nombres": datos.get("nombres", ""),
            "apellidos": datos.get("apellidos", ""),
            "activo": True,
            "requiere_cambio_password": bool(datos.get("requiere_cambio_password", False)),
            "ultimo_acceso": None,
        }
        _save_store(store)
        return new_id

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Retorna el usuario autenticado (público) o None."""
        if not self._current_user:
            return None
        return self._current_user.copy()

    def is_admin(self) -> bool:
        """Indica si el usuario autenticado tiene rol admin."""
        if not self._current_user:
            return False
        return str(self._current_user.get("rol", "")).lower() == "admin"


auth_manager = AuthManager()
