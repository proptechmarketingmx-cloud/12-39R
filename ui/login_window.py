"""Ventana de login para CRM Inmobiliario.

Cumple las especificaciones del proyecto: centrada, 400x500, no redimensionable,
uso de `auth_manager` para autenticación y colores desde `config/config.py`.
"""
from __future__ import annotations

import logging
import sys
from typing import Optional, Tuple
import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import ttk

try:
    from modules.auth import auth_manager
except Exception:
    auth_manager = None  # type: ignore

try:
    from ui.change_password_dialog import ChangePasswordDialog
except Exception:
    ChangePasswordDialog = None  # type: ignore

# Intentar importar colores desde config; usar valores por defecto si no existen
try:
    import config.config as _config

    def _get_color(name: str, default: str) -> str:
        for key in (name.upper(), name.lower(), f"{name}_color", f"{name.upper()}_COLOR"):
            if hasattr(_config, key):
                return getattr(_config, key)
        return default

    PRIMARY_COLOR = _get_color("primary", "#2196F3")
    SUCCESS_COLOR = _get_color("success", "#4CAF50")
    DANGER_COLOR = _get_color("danger", "#F44336")
except Exception:
    PRIMARY_COLOR = "#2196F3"
    SUCCESS_COLOR = "#4CAF50"
    DANGER_COLOR = "#F44336"

LOG = logging.getLogger(__name__)


class LoginWindow:
    """Clase que crea y controla la ventana de login.

    Métodos principales:
    - `run()`: inicia el loop de la ventana.

    La ventana cierra la aplicación si se cierra sin autenticación.
    """

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Login - CRM Inmobiliario")
        self.width = 400
        self.height = 500
        self._center_window()
        self.root.resizable(False, False)
        self.authenticated_user: Optional[dict] = None

        self._build_ui()

        # Bind cierre de ventana a handler que termina la app si no autenticado
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center_window(self) -> None:
        """Centra la ventana en pantalla usando geometry."""
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = int((sw - self.width) / 2)
        y = int((sh - self.height) / 2)
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def _build_ui(self) -> None:
        """Construye widgets de la ventana de login."""
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True, fill=tk.BOTH)

        # Logo placeholder
        logo = ttk.Label(frame, text="CRM INMOBILIARIO", anchor=tk.CENTER)
        logo.config(font=("Segoe UI", 18, "bold"), foreground=PRIMARY_COLOR)
        logo.pack(pady=(10, 30))

        # Username
        lbl_user = ttk.Label(frame, text="Usuario:")
        lbl_user.pack(anchor=tk.W, padx=10)
        self.var_username = tk.StringVar()
        self.entry_username = ttk.Entry(frame, textvariable=self.var_username)
        self.entry_username.pack(fill=tk.X, padx=10, pady=5)

        # Password
        lbl_pass = ttk.Label(frame, text="Contraseña:")
        lbl_pass.pack(anchor=tk.W, padx=10, pady=(10, 0))
        self.var_password = tk.StringVar()
        self.entry_password = ttk.Entry(frame, textvariable=self.var_password, show="*")
        self.entry_password.pack(fill=tk.X, padx=10, pady=5)

        # Botón iniciar sesión
        btn_login = ttk.Button(frame, text="Iniciar Sesión", command=self._on_login)
        btn_login.pack(pady=20)

        # Atajos teclado
        self.entry_username.bind("<Return>", lambda e: self._on_login())
        self.entry_password.bind("<Return>", lambda e: self._on_login())
        self.root.bind("<Escape>", lambda e: self._on_close())

        # Focus inicial
        self.entry_username.focus_set()

    def _validate_inputs(self) -> Tuple[bool, Optional[str]]:
        """Valida que los campos no estén vacíos.

        Retorna (True, None) si válido, o (False, mensaje_error).
        """
        user = self.var_username.get().strip()
        pwd = self.var_password.get()
        if not user:
            return False, "El campo 'Usuario' es obligatorio."
        if not pwd:
            return False, "El campo 'Contraseña' es obligatorio."
        return True, None

    def _on_login(self) -> None:
        """Handler del botón/enter para intentar autenticación."""
        valido, mensaje = self._validate_inputs()
        if not valido:
            messagebox.showerror("Error de validación", mensaje)
            return

        username = self.var_username.get().strip()
        password = self.var_password.get()

        if auth_manager is None:
            LOG.warning("auth_manager no disponible en modules.auth")
            messagebox.showerror("Error", "Módulo de autenticación no disponible.")
            return

        try:
            exito, usuario, msg = auth_manager.login(username, password)
        except Exception as e:  # pragma: no cover - dependencias externas
            LOG.exception("Error al llamar auth_manager.login: %s", e)
            messagebox.showerror("Error", "Error inesperado al autenticar.")
            return

        if exito:
            self.authenticated_user = usuario
            # Si requiere cambio de password, solicitarlo
            try:
                if hasattr(auth_manager, "requiere_cambio_password") and auth_manager.requiere_cambio_password():
                    self._handle_password_change(username)
            except Exception:
                LOG.exception("Error comprobando requiere_cambio_password")

            # Cerrar login y abrir ventana principal
            self._open_main_window()
        else:
            messagebox.showerror("Autenticación", msg or "Usuario o contraseña inválidos.")
            # Limpiar sólo password
            self.var_password.set("")
            self.entry_password.focus_set()

    def _handle_password_change(self, username: str) -> None:
        """Pide al usuario cambiar la contraseña en primer login.

        Intenta llamar a un método de cambio de password en `auth_manager` si existe.
        """
        # Preferir el diálogo visual implementado; si no está disponible, caer
        # en la lógica previa basada en simpledialog.
        if ChangePasswordDialog is not None:
            try:
                dlg = ChangePasswordDialog(self.root, username)
                success = dlg.show()
                if success:
                    return
                # si no se cambió, notificar
                messagebox.showwarning("Atención", "Debe cambiar la contraseña para continuar.", parent=self.root)
                return
            except Exception:
                LOG.exception("Error mostrando ChangePasswordDialog")

        # Fallback: mantener comportamiento original con simpledialog
        intento = 0
        while intento < 3:
            new_pwd = simpledialog.askstring("Cambiar contraseña", "Ingrese nueva contraseña:", show="*")
            if new_pwd is None:
                messagebox.showwarning("Atención", "Debe cambiar la contraseña para continuar.")
                continue
            confirm = simpledialog.askstring("Confirmar contraseña", "Confirme la nueva contraseña:", show="*")
            if confirm != new_pwd:
                messagebox.showerror("Error", "Las contraseñas no coinciden.")
                intento += 1
                continue

            # Intentar aplicar cambio con métodos comunes
            for method_name in ("cambiar_password", "change_password", "reset_password", "set_password"):
                if hasattr(auth_manager, method_name):
                    try:
                        getattr(auth_manager, method_name)(username, new_pwd)
                        messagebox.showinfo("Éxito", "Contraseña cambiada correctamente.")
                        return
                    except Exception:
                        LOG.exception("Fallo al invocar %s en auth_manager", method_name)
        # Si no se pudo cambiar tras los intentos, informar y salir
        messagebox.showinfo("Información", "No se pudo cambiar la contraseña automáticamente. Cambie la contraseña desde el panel de configuración.")
        return

    def _open_main_window(self) -> None:
        """Intenta abrir `ui.main_window`. Si no existe, informa al usuario y termina.

        Se cierra la ventana de login tras abrir la principal.
        """
        try:
            from ui.main_window import MainWindow  # type: ignore

            self.root.destroy()
            main = MainWindow(user=self.authenticated_user)
            main.run()
        except Exception:
            LOG.exception("No se pudo abrir ui.main_window")
            # Aun así cerramos login y terminamos. El usuario puede implementar MainWindow.
            messagebox.showinfo("Autenticado", "Inicio de sesión correcto. Implementar `ui.main_window.MainWindow` para continuar.")
            self.root.destroy()

    def _on_close(self) -> None:
        """Handler al cerrar la ventana: si no está autenticado, terminar la app completa."""
        if not self.authenticated_user:
            self.root.quit()
            try:
                sys.exit(0)
            except SystemExit:
                pass
        else:
            self.root.destroy()

    def run(self) -> None:
        """Inicia el mainloop de la ventana de login."""
        self.root.mainloop()


def main() -> None:
    """Punto de entrada para ejecutar la ventana de login directamente (para pruebas)."""
    logging.basicConfig(level=logging.INFO)
    win = LoginWindow()
    win.run()


if __name__ == "__main__":
    main()
