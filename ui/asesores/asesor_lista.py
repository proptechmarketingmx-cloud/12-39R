"""Lista de asesores con busqueda, filtros y paginacion."""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional

import tkinter as tk
from tkinter import ttk, messagebox

try:
    from modules.asesores import asesores_manager
except Exception:
    asesores_manager = None  # type: ignore

try:
    from ui.asesores.asesor_form import AsesorForm
except Exception:
    AsesorForm = None  # type: ignore

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


class AsesorLista(ttk.Frame):
    """Vista de lista de asesores con busqueda, filtros y paginacion."""

    def __init__(self, master: Optional[tk.Widget] = None) -> None:
        super().__init__(master)
        self.page_size = 50
        self.page = 1
        self.total = 0
        self._rows: List[Dict[str, Any]] = []

        self._build_ui()
        self._load_data()

    def _build_ui(self) -> None:
        font = _get_font()
        primary = _get_color("primary", "#2196F3")

        # Barra de busqueda
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=8, pady=(8, 4))
        ttk.Label(search_frame, text="Buscar:", font=font).pack(side=tk.LEFT)
        self.var_search = tk.StringVar()
        self.entry_search = ttk.Entry(search_frame, textvariable=self.var_search)
        self.entry_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        self.entry_search.bind("<Return>", lambda e: self._on_buscar())
        ttk.Button(search_frame, text="Buscar", command=self._on_buscar).pack(side=tk.LEFT, padx=4)
        ttk.Button(search_frame, text="Limpiar", command=self._on_limpiar_busqueda).pack(side=tk.LEFT)

        # Filtros
        filters = ttk.Frame(self)
        filters.pack(fill=tk.X, padx=8, pady=(0, 6))

        self.var_activo = tk.StringVar(value="Activos")
        self.var_rol = tk.StringVar(value="Todos")

        ttk.Label(filters, text="Estado:", font=font).grid(row=0, column=0, sticky=tk.W)
        cb_activo = ttk.Combobox(filters, textvariable=self.var_activo, state="readonly")
        cb_activo["values"] = ["Activos", "Inactivos", "Todos"]
        cb_activo.grid(row=0, column=1, sticky=tk.W, padx=4)

        ttk.Label(filters, text="Rol:", font=font).grid(row=0, column=2, sticky=tk.W, padx=(8, 0))
        cb_rol = ttk.Combobox(filters, textvariable=self.var_rol, state="readonly")
        cb_rol["values"] = ["Todos", "admin", "asesor"]
        cb_rol.grid(row=0, column=3, sticky=tk.W, padx=4)

        ttk.Button(filters, text="Aplicar", command=self._on_buscar).grid(row=0, column=4, sticky=tk.W, padx=(8, 0))

        # Acciones
        actions = ttk.Frame(self)
        actions.pack(fill=tk.X, padx=8, pady=(0, 6))
        ttk.Button(actions, text="Nuevo Asesor", command=self._on_nuevo).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Editar", command=self._on_editar).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Ver Detalle", command=self._on_ver_detalle).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Eliminar", command=self._on_eliminar).pack(side=tk.LEFT, padx=4)

        # Tabla
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 6))

        columns = ("id", "username", "rol", "nombres", "apellidos", "activo", "ultimo")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("id", text="ID")
        self.tree.heading("username", text="Usuario")
        self.tree.heading("rol", text="Rol")
        self.tree.heading("nombres", text="Nombres")
        self.tree.heading("apellidos", text="Apellidos")
        self.tree.heading("activo", text="Activo")
        self.tree.heading("ultimo", text="Ultimo acceso")

        self.tree.column("id", width=60, anchor=tk.CENTER)
        self.tree.column("username", width=140, anchor=tk.W)
        self.tree.column("rol", width=90, anchor=tk.CENTER)
        self.tree.column("nombres", width=160, anchor=tk.W)
        self.tree.column("apellidos", width=160, anchor=tk.W)
        self.tree.column("activo", width=80, anchor=tk.CENTER)
        self.tree.column("ultimo", width=160, anchor=tk.CENTER)

        sb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", lambda e: self._on_editar())

        # Paginacion
        pager = ttk.Frame(self)
        pager.pack(fill=tk.X, padx=8, pady=(0, 8))
        self.lbl_pager = ttk.Label(pager, text="Pagina 1", font=font)
        self.lbl_pager.pack(side=tk.LEFT)
        self.btn_prev = ttk.Button(pager, text="Anterior", command=self._prev_page)
        self.btn_next = ttk.Button(pager, text="Siguiente", command=self._next_page)
        self.btn_prev.pack(side=tk.RIGHT)
        self.btn_next.pack(side=tk.RIGHT, padx=6)

        style = ttk.Style()
        style.configure("Treeview.Heading", foreground=primary)

    def _get_filters(self) -> Dict[str, Any]:
        filtros: Dict[str, Any] = {}
        estado = self.var_activo.get()
        rol = self.var_rol.get()
        if estado == "Activos":
            filtros["activo"] = True
        elif estado == "Inactivos":
            filtros["activo"] = False
        if rol and rol != "Todos":
            filtros["rol"] = rol
        return filtros

    def _load_data(self) -> None:
        if asesores_manager is None:
            self._rows = []
            self.total = 0
            self._render_table()
            return

        filtros = self._get_filters()
        search_text = (self.var_search.get() or "").strip().lower()

        try:
            data = asesores_manager.listar_asesores(activo=filtros.get("activo", True))
        except Exception:
            LOG.exception("Error listando asesores")
            data = []

        if filtros.get("rol"):
            data = [a for a in data if str(a.get("rol", "")).lower() == str(filtros.get("rol")).lower()]

        if search_text:
            def _match(a: Dict[str, Any]) -> bool:
                parts = [
                    str(a.get("username", "")),
                    str(a.get("nombres", "")),
                    str(a.get("apellidos", "")),
                ]
                return search_text in " ".join(parts).lower()
            data = [a for a in data if _match(a)]

        self.total = len(data)
        start = (self.page - 1) * self.page_size
        end = start + self.page_size
        self._rows = data[start:end]
        self._render_table()

    def _render_table(self) -> None:
        for i in self.tree.get_children():
            self.tree.delete(i)

        for a in self._rows:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    a.get("id", ""),
                    a.get("username", ""),
                    a.get("rol", ""),
                    a.get("nombres", ""),
                    a.get("apellidos", ""),
                    "Si" if a.get("activo") else "No",
                    a.get("ultimo_acceso", ""),
                ),
            )

        total_pages = max(1, int(math.ceil(self.total / float(self.page_size))))
        self.page = min(max(1, self.page), total_pages)
        self.lbl_pager.config(text=f"Pagina {self.page} de {total_pages} (Total: {self.total})")
        self.btn_prev.config(state=tk.NORMAL if self.page > 1 else tk.DISABLED)
        self.btn_next.config(state=tk.NORMAL if self.page < total_pages else tk.DISABLED)

    def _on_buscar(self) -> None:
        self.page = 1
        self._load_data()

    def _on_limpiar_busqueda(self) -> None:
        self.var_search.set("")
        self.var_activo.set("Activos")
        self.var_rol.set("Todos")
        self.page = 1
        self._load_data()

    def _get_selected(self) -> Optional[Dict[str, Any]]:
        sel = self.tree.selection()
        if not sel:
            return None
        idx = self.tree.index(sel[0])
        if idx < 0 or idx >= len(self._rows):
            return None
        return self._rows[idx]

    def _on_nuevo(self) -> None:
        if AsesorForm is None:
            messagebox.showerror("Error", "AsesorForm no disponible.")
            return
        dlg = AsesorForm(master=self.winfo_toplevel(), mode="crear")
        dlg.grab_set()
        self.wait_window(dlg)
        self._load_data()

    def _on_editar(self) -> None:
        asesor = self._get_selected()
        if not asesor:
            messagebox.showwarning("Atencion", "Seleccione un asesor.")
            return
        if AsesorForm is None:
            messagebox.showerror("Error", "AsesorForm no disponible.")
            return
        dlg = AsesorForm(master=self.winfo_toplevel(), mode="editar", asesor=asesor)
        dlg.grab_set()
        self.wait_window(dlg)
        self._load_data()

    def _on_ver_detalle(self) -> None:
        self._on_editar()

    def _on_eliminar(self) -> None:
        asesor = self._get_selected()
        if not asesor:
            messagebox.showwarning("Atencion", "Seleccione un asesor.")
            return
        if not messagebox.askyesno("Confirmar", "Desea eliminar el asesor seleccionado?"):
            return
        if asesores_manager is None:
            messagebox.showerror("Error", "Modulo de asesores no disponible.")
            return
        try:
            asesores_manager.eliminar_asesor(int(asesor.get("id")))
            self._load_data()
        except Exception:
            LOG.exception("Error eliminando asesor")
            messagebox.showerror("Error", "No se pudo eliminar el asesor.")

    def _prev_page(self) -> None:
        if self.page > 1:
            self.page -= 1
            self._load_data()

    def _next_page(self) -> None:
        self.page += 1
        self._load_data()


def main_test() -> None:
    root = tk.Tk()
    root.title("Asesores")
    vista = AsesorLista(root)
    vista.pack(fill=tk.BOTH, expand=True)
    root.mainloop()


if __name__ == "__main__":
    main_test()
