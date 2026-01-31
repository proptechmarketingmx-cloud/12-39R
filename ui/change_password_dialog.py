"""Diálogo modal para cambiar la contraseña del usuario.

Provee una interfaz visual en lugar de `simpledialog` y llama a
`auth_manager.cambiar_password(username, nueva_password)` si el usuario
confirma y las validaciones pasan.
"""
from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

try:
    from modules.auth import auth_manager
except Exception:
    auth_manager = None  # type: ignore

LOG = logging.getLogger(__name__)


class ChangePasswordDialog(tk.Toplevel):
    """Diálogo modal para cambiar contraseña.

    Uso:
        dlg = ChangePasswordDialog(parent, username)
        success = dlg.show()
    """

    def __init__(self, parent: tk.Widget, username: str) -> None:
        super().__init__(parent)
        self.parent = parent
        self.username = username
        self.title("Cambiar contraseña")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.var_new = tk.StringVar()
        self.var_confirm = tk.StringVar()
        self._result: Optional[bool] = None

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _build(self) -> None:
        pad = 8
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text=f"Cambiar contraseña para: {self.username}").pack(anchor=tk.W)

        ttk.Label(frm, text="Nueva contraseña:").pack(anchor=tk.W, pady=(10, 0))
        ent_new = ttk.Entry(frm, textvariable=self.var_new, show="*")
        ent_new.pack(fill=tk.X, pady=4)
        ent_new.focus_set()

        ttk.Label(frm, text="Confirmar contraseña:").pack(anchor=tk.W, pady=(8, 0))
        ttk.Entry(frm, textvariable=self.var_confirm, show="*").pack(fill=tk.X, pady=4)

        btns = ttk.Frame(frm)
        btns.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(btns, text="Aceptar", command=self._on_accept).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btns, text="Cancelar", command=self._on_cancel).pack(side=tk.RIGHT)

        self.bind("<Return>", lambda e: self._on_accept())
        self.bind("<Escape>", lambda e: self._on_cancel())

    def _validate(self) -> Optional[str]:
        a = self.var_new.get() or ""
        b = self.var_confirm.get() or ""
        if not a or not b:
            return "Ambos campos son obligatorios."
        if a != b:
            return "Las contraseñas no coinciden."
        if len(a) < 8:
            return "La contraseña debe tener al menos 8 caracteres."
        return None

    def _on_accept(self) -> None:
        err = self._validate()
        if err:
            messagebox.showerror("Error", err, parent=self)
            return

        if auth_manager is None or not hasattr(auth_manager, "cambiar_password"):
            messagebox.showwarning("Advertencia", "Módulo de autenticación no disponible para cambiar contraseña.", parent=self)
            self._result = False
            self.destroy()
            return

        try:
            auth_manager.cambiar_password(self.username, self.var_new.get())
            messagebox.showinfo("Éxito", "Contraseña cambiada correctamente.", parent=self)
            self._result = True
        except Exception:
            LOG.exception("Error cambiando contraseña para %s", self.username)
            messagebox.showerror("Error", "No se pudo cambiar la contraseña.", parent=self)
            self._result = False

        self.destroy()

    def _on_cancel(self) -> None:
        self._result = False
        self.destroy()

    def show(self) -> bool:
        """Muestra el diálogo de forma modal y retorna True si la contraseña fue cambiada."""
        self.wait_window()
        return bool(self._result)

