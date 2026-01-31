"""Ventana principal demo para el CRM Inmobiliario.

Archivo mínimo para pruebas de integración con `ui/login_window.LoginWindow`.
Muestra un encabezado con el usuario autenticado y un botón para cerrar sesión.
"""
from __future__ import annotations

import logging
import sys
from typing import Optional, Dict, Any
import tkinter as tk
from tkinter import ttk

try:
    import config.config as _config

    def _get_color(name: str, default: str) -> str:
        for key in (name.upper(), name.lower(), f"{name}_color", f"{name.upper()}_COLOR"):
            if hasattr(_config, key):
                return getattr(_config, key)
        return default

    _primary_color_value = _get_color("primary", "#2196F3")
except Exception:
    def _get_color(name: str, default: str) -> str:
        return default
    _primary_color_value = "#2196F3"

PRIMARY_COLOR = _primary_color_value

LOG = logging.getLogger(__name__)

try:
    from ui.change_password_dialog import ChangePasswordDialog
except Exception:
    ChangePasswordDialog = None

try:
    from ui.clientes.cliente_form import ClienteForm
except Exception:
    ClienteForm = None

try:
    from ui.propiedades.propiedad_form import PropiedadForm
except Exception:
    PropiedadForm = None


class MainWindow:
    """Ventana principal mínima.

    Parámetros:
    - `user`: diccionario público con al menos la clave `username`.
    """

    def __init__(self, user: Optional[Dict[str, Any]] = None) -> None:
        self.user = user or {"username": "Usuario"}
        self.root = tk.Tk()
        self.root.title("CRM Inmobiliario - Principal")
        # Maximizar ventana (Windows). En otros sistemas `zoomed` puede no existir.
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self._build_ui()

    def _build_ui(self) -> None:
        self.frame = ttk.Frame(self.root, padding=16)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self._build_menu()

        header = ttk.Label(self.frame, text=f"Bienvenido, {self.user.get('username')}")
        header.config(font=("Segoe UI", 16, "bold"), foreground=PRIMARY_COLOR)
        header.pack(anchor=tk.W)

        # Área principal placeholder
        content = ttk.Frame(self.frame)
        content.pack(fill=tk.BOTH, expand=True, pady=20)

        lbl = ttk.Label(content, text="Ventana principal (demo). Implementar dashboard real en ui/main_window.py.")
        lbl.pack()

        # Botón logout
        btn_logout = ttk.Button(self.frame, text="Cerrar sesión", command=self._on_logout)
        btn_logout.pack(side=tk.BOTTOM, anchor=tk.E)

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Cambiar contraseña", command=self._on_change_password)
        file_menu.add_separator()
        file_menu.add_command(label="Cerrar sesión", command=self._on_logout)
        file_menu.add_command(label="Salir", command=self._on_exit)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        modules_menu = tk.Menu(menubar, tearoff=0)
        modules_menu.add_command(label="Clientes", command=self._open_clientes)
        modules_menu.add_command(label="Propiedades", command=self._open_propiedades)
        menubar.add_cascade(label="Módulos", menu=modules_menu)

        self.root.config(menu=menubar)

    def _on_change_password(self) -> None:
        username = self.user.get("username") or "Usuario"
        if ChangePasswordDialog is None:
            message = "El diálogo de cambio de contraseña no está disponible."
            LOG.warning(message)
            try:
                from tkinter import messagebox

                messagebox.showwarning("Advertencia", message)
            except Exception:
                pass
            return
        dlg = ChangePasswordDialog(self.frame, username)
        dlg.show()

    def _open_clientes(self) -> None:
        if ClienteForm is None:
            LOG.warning("ClienteForm no disponible")
            try:
                from tkinter import messagebox

                messagebox.showinfo("No implementado", "El formulario de Clientes no está disponible.")
            except Exception:
                pass
            return
        # Abrir formulario como modal
        try:
            f = ClienteForm(master=self.root)
            f.grab_set()
        except Exception:
            LOG.exception("Error abriendo ClienteForm")

    def _open_propiedades(self) -> None:
        if PropiedadForm is None:
            LOG.warning("PropiedadForm no disponible")
            try:
                from tkinter import messagebox

                messagebox.showinfo("No implementado", "El formulario de Propiedades no está disponible.")
            except Exception:
                pass
            return
        try:
            f = PropiedadForm(master=self.root)
            f.grab_set()
        except Exception:
            LOG.exception("Error abriendo PropiedadForm")

    def _on_exit(self) -> None:
        try:
            self.root.destroy()
            sys.exit(0)
        except SystemExit:
            pass

    def _on_logout(self) -> None:
        try:
            self.root.destroy()
            sys.exit(0)
        except SystemExit:
            pass

    def run(self) -> None:
        """Inicia el mainloop de la ventana principal."""
        self.root.mainloop()


def main() -> None:
    win = MainWindow(user={"username": "demo"})
    win.run()


if __name__ == "__main__":
    main()
