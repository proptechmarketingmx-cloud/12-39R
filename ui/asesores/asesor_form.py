"""Formulario de asesor.

Formulario en modo crear/editar con campos extendidos solicitados.
Nota: la tabla `asesores` actual solo persiste campos basicos (username,
password_hash, rol, nombres, apellidos, activo, requiere_cambio_password,
ultimo_acceso). Los campos extendidos se muestran en la UI pero no se
persisten hasta que el schema se actualice.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import tkinter as tk
from tkinter import ttk, messagebox

try:
    from modules.asesores import asesores_manager
except Exception:
    asesores_manager = None  # type: ignore

try:
    from modules.auth import auth_manager
except Exception:
    auth_manager = None  # type: ignore

try:
    import config.config as _config
except Exception:
    _config = None

LOG = logging.getLogger(__name__)


def _get_font() -> tuple:
    family = getattr(_config, "FONT_FAMILY", "Segoe UI") if _config else "Segoe UI"
    size = getattr(_config, "FONT_SIZE_BASE", 10) if _config else 10
    return (family, size)


def _get_color(name: str, default: str) -> str:
    if _config is None:
        return default
    colors = getattr(_config, "COLORS", None)
    if isinstance(colors, dict):
        for key in (name, name.upper(), name.lower()):
            if key in colors:
                return colors[key]
    for key in (name.upper(), name.lower(), f"{name}_color", f"{name.upper()}_COLOR"):
        if hasattr(_config, key):
            return getattr(_config, key)
    return default


class AsesorForm(tk.Toplevel):
    """Ventana modal para crear/editar asesores."""

    def __init__(self, master: Any = None, mode: str = "crear", asesor: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(master)
        self.title("Asesor - " + ("Crear" if mode == "crear" else "Editar"))
        self.mode = mode
        self.asesor = asesor or {}
        self.resizable(True, True)
        self.geometry("700x650")

        self._build_ui()
        if self.mode == "editar":
            self._populate()

    def _build_ui(self) -> None:
        font = _get_font()
        primary = _get_color("primary", "#2196F3")

        header = ttk.Label(self, text="Formulario de Asesor")
        header.config(font=(font[0], font[1] + 4, "bold"), foreground=primary)
        header.pack(anchor=tk.W, padx=12, pady=(12, 6))

        # Scrollable frame
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        self.form_frame = ttk.Frame(canvas)

        self.form_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=self.form_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Campos
        self.vars: Dict[str, tk.StringVar] = {}
        self.vars_bool: Dict[str, tk.BooleanVar] = {}

        row = 0

        def _section(title: str) -> None:
            nonlocal row
            ttk.Label(self.form_frame, text=title, font=(font[0], font[1] + 1, "bold")).grid(
                row=row, column=0, sticky=tk.W, padx=6, pady=(12, 4)
            )
            row += 1

        def _add(key: str, label: str, widget: str = "entry", values: Optional[list[str]] = None) -> None:
            nonlocal row
            ttk.Label(self.form_frame, text=label, font=font).grid(row=row, column=0, sticky=tk.W, padx=6, pady=4)
            self.vars[key] = tk.StringVar()
            if widget == "combo":
                cb = ttk.Combobox(self.form_frame, textvariable=self.vars[key], state="readonly")
                cb["values"] = values or []
                cb.grid(row=row, column=1, sticky=tk.EW, padx=6)
            elif widget == "password":
                ent = ttk.Entry(self.form_frame, textvariable=self.vars[key], show="*")
                ent.grid(row=row, column=1, sticky=tk.EW, padx=6)
                if self.mode == "editar":
                    ent.configure(state="disabled")
            else:
                ttk.Entry(self.form_frame, textvariable=self.vars[key]).grid(row=row, column=1, sticky=tk.EW, padx=6)
            row += 1

        _section("General")
        _add("username", "Usuario (username)")
        _add("password", "Contraseña", widget="password")
        _add("rol", "Rol", widget="combo", values=["asesor", "admin"])
        _add("primer_nombre", "Primer nombre")
        _add("segundo_nombre", "Segundo nombre")
        _add("apellido_paterno", "Apellido paterno")
        _add("apellido_materno", "Apellido materno")
        _add("curp", "CURP")
        _add("fecha_nacimiento", "Fecha de nacimiento (YYYY-MM-DD)")
        _add("edad", "Edad")
        _add("genero", "Genero", widget="combo", values=["Hombre", "Mujer"])
        _add("estado_civil", "Estado civil", widget="combo", values=["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a"])

        _section("Metodo de contacto")
        _add("telefono", "Telefono")
        _add("correo", "Correo")

        _section("Residencia")
        _add("pais", "Pais")
        _add("estado", "Estado")
        _add("ciudad", "Ciudad")
        _add("zona", "Zona")

        _section("Laboral")
        _add("inmobiliaria", "Inmobiliaria")
        _add("area", "Area")
        _add("anos_experiencia", "Años de experiencia")
        _add("comision_asignada", "Comision asignada")
        _add("fecha_ingreso", "Fecha de ingreso (YYYY-MM-DD)")

        # Checkboxes
        self.vars_bool["activo"] = tk.BooleanVar(value=True)
        self.vars_bool["requiere_cambio_password"] = tk.BooleanVar(value=False)

        ttk.Checkbutton(self.form_frame, text="Activo", variable=self.vars_bool["activo"]).grid(
            row=row, column=0, sticky=tk.W, padx=6, pady=6
        )
        ttk.Checkbutton(self.form_frame, text="Requiere cambio de contraseña", variable=self.vars_bool["requiere_cambio_password"]).grid(
            row=row, column=1, sticky=tk.W, padx=6, pady=6
        )

        self.form_frame.columnconfigure(1, weight=1)

        # Aviso de persistencia
        note = ttk.Label(
            self,
            text="Nota: los campos extendidos no se guardan en BD hasta actualizar el schema.",
            foreground=_get_color("danger", "#F44336"),
            font=font,
        )
        note.pack(anchor=tk.W, padx=12, pady=(0, 6))

        # Botones
        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, padx=12, pady=10)
        ttk.Button(btns, text="Guardar", command=self._on_guardar).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT)

    def _populate(self) -> None:
        try:
            p = self.asesor
            for key in self.vars:
                if key == "password":
                    continue
                if key in p:
                    self.vars[key].set(str(p.get(key, "")))
            self.vars_bool["activo"].set(bool(p.get("activo", True)))
            self.vars_bool["requiere_cambio_password"].set(bool(p.get("requiere_cambio_password", False)))
        except Exception:
            LOG.exception("Error poblando formulario de asesor")

    def _validar(self) -> Optional[str]:
        correo = self.vars.get("correo").get().strip()
        if correo and ("@" not in correo or "." not in correo):
            return "El correo no es valido."

        telefono = self.vars.get("telefono").get().strip()
        if telefono and (not telefono.isdigit() or len(telefono) != 10):
            return "El telefono debe tener 10 digitos."

        curp = self.vars.get("curp").get().strip()
        if curp and len(curp) != 18:
            return "El CURP debe tener 18 caracteres."

        fecha_ingreso = self.vars.get("fecha_ingreso").get().strip()
        if fecha_ingreso:
            try:
                datetime.strptime(fecha_ingreso, "%Y-%m-%d")
            except Exception:
                return "La fecha de ingreso debe ser YYYY-MM-DD."

        return None

    def _on_guardar(self) -> None:
        err = self._validar()
        if err:
            messagebox.showerror("Validacion", err, parent=self)
            return

        if asesores_manager is None:
            messagebox.showerror("Error", "Modulo de asesores no disponible.", parent=self)
            return

        datos = {k: v.get().strip() for k, v in self.vars.items() if k != "password"}
        datos["activo"] = bool(self.vars_bool["activo"].get())
        datos["requiere_cambio_password"] = bool(self.vars_bool["requiere_cambio_password"].get())

        primer = self.vars.get("primer_nombre").get().strip()
        segundo = self.vars.get("segundo_nombre").get().strip()
        ap_pat = self.vars.get("apellido_paterno").get().strip()
        ap_mat = self.vars.get("apellido_materno").get().strip()
        nombres = " ".join([x for x in [primer, segundo] if x]).strip()
        apellidos = " ".join([x for x in [ap_pat, ap_mat] if x]).strip()
        if nombres:
            datos["nombres"] = nombres
        if apellidos:
            datos["apellidos"] = apellidos

        try:
            if self.mode == "crear":
                username = self.vars.get("username").get().strip()
                password = self.vars.get("password").get().strip()
                datos["username"] = username
                datos["password"] = password
                creador_id = 0
                if auth_manager and auth_manager.get_current_user():
                    creador_id = int(auth_manager.get_current_user().get("id", 0))
                asesores_manager.crear_asesor(datos, creador_id)  # type: ignore
            else:
                asesor_id = int(self.asesor.get("id"))
                asesores_manager.editar_asesor(asesor_id, datos)  # type: ignore
            messagebox.showinfo("Exito", "Asesor guardado correctamente.", parent=self)
            self.destroy()
        except Exception:
            LOG.exception("Error guardando asesor")
            messagebox.showerror("Error", "No se pudo guardar el asesor.", parent=self)


def main_test() -> None:
    root = tk.Tk()
    root.withdraw()
    f = AsesorForm(master=root, mode="crear")
    f.grab_set()
    root.mainloop()


if __name__ == "__main__":
    main_test()
