"""Lista de propiedades con busqueda, filtros y paginacion.

Usa `modules.propiedades` (listar_propiedades, buscar_propiedades, contar_propiedades).
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Callable

import tkinter as tk
from tkinter import ttk, messagebox

try:
	from modules import propiedades as propiedades_module
except Exception:
	propiedades_module = None

try:
	from ui.propiedades.propiedad_form import PropiedadForm
except Exception:
	PropiedadForm = None  # type: ignore

try:
	import config.config as _config
except Exception:
	_config = None

LOG = logging.getLogger(__name__)



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


def _get_font() -> tuple:
	family = getattr(_config, "FONT_FAMILY", "Segoe UI") if _config else "Segoe UI"
	size = getattr(_config, "FONT_SIZE_BASE", 10) if _config else 10
	return (family, size)


def _safe_float(value: Any, default: float = 0.0) -> float:
	try:
		return float(value)
	except Exception:
		return default


def _call_with_supported_kwargs(func: Callable[..., Any], **kwargs: Any) -> Any:
	try:
		import inspect

		sig = inspect.signature(func)
		params = sig.parameters
		filtered = {k: v for k, v in kwargs.items() if k in params}
		return func(**filtered)
	except TypeError:
		try:
			return func(**kwargs)
		except Exception:
			return None
	except Exception:
		return None


class PropiedadLista(ttk.Frame):
	"""Vista de lista de propiedades con busqueda, filtros y paginacion."""

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

		self.var_estado = tk.StringVar(value="Todos")
		self.var_precio_min = tk.StringVar()
		self.var_precio_max = tk.StringVar()

		ttk.Label(filters, text="Estado:", font=font).grid(row=0, column=0, sticky=tk.W)
		cb_estado = ttk.Combobox(filters, textvariable=self.var_estado, state="readonly")
		cb_estado["values"] = ["Todos", "Disponible", "Reservado", "Vendido", "Renta"]
		cb_estado.grid(row=0, column=1, sticky=tk.W, padx=4)

		ttk.Label(filters, text="Precio Min:", font=font).grid(row=0, column=2, sticky=tk.W, padx=(8, 0))
		ttk.Entry(filters, textvariable=self.var_precio_min, width=12).grid(row=0, column=3, sticky=tk.W, padx=4)

		ttk.Label(filters, text="Precio Max:", font=font).grid(row=0, column=4, sticky=tk.W, padx=(8, 0))
		ttk.Entry(filters, textvariable=self.var_precio_max, width=12).grid(row=0, column=5, sticky=tk.W, padx=4)

		ttk.Button(filters, text="Aplicar", command=self._on_buscar).grid(row=0, column=6, sticky=tk.W, padx=(8, 0))

		# Acciones
		actions = ttk.Frame(self)
		actions.pack(fill=tk.X, padx=8, pady=(0, 6))
		btn_new = ttk.Button(actions, text="Nueva Propiedad", command=self._on_nuevo)
		btn_edit = ttk.Button(actions, text="Editar", command=self._on_editar)
		btn_view = ttk.Button(actions, text="Ver Detalle", command=self._on_ver_detalle)
		btn_del = ttk.Button(actions, text="Eliminar", command=self._on_eliminar)
		btn_new.pack(side=tk.LEFT, padx=4)
		btn_edit.pack(side=tk.LEFT, padx=4)
		btn_view.pack(side=tk.LEFT, padx=4)
		btn_del.pack(side=tk.LEFT, padx=4)

		# Tabla
		table_frame = ttk.Frame(self)
		table_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 6))

		columns = ("id", "titulo", "precio", "estado", "ciudad", "metros")
		self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
		self.tree.heading("id", text="ID")
		self.tree.heading("titulo", text="Titulo")
		self.tree.heading("precio", text="Precio")
		self.tree.heading("estado", text="Estado")
		self.tree.heading("ciudad", text="Ciudad")
		self.tree.heading("metros", text="Metros")

		self.tree.column("id", width=60, anchor=tk.CENTER)
		self.tree.column("titulo", width=220, anchor=tk.W)
		self.tree.column("precio", width=120, anchor=tk.E)
		self.tree.column("estado", width=120, anchor=tk.CENTER)
		self.tree.column("ciudad", width=140, anchor=tk.W)
		self.tree.column("metros", width=100, anchor=tk.CENTER)

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
		estado = self.var_estado.get()
		precio_min = _safe_float(self.var_precio_min.get() or 0, 0.0)
		precio_max = _safe_float(self.var_precio_max.get() or 0, 0.0)
		filtros: Dict[str, Any] = {}
		if estado and estado != "Todos":
			filtros["estado"] = estado
		if precio_min:
			filtros["precio_min"] = precio_min
		if precio_max:
			filtros["precio_max"] = precio_max
		return filtros

	def _load_data(self) -> None:
		search_text = (self.var_search.get() or "").strip()
		filtros = self._get_filters()

		data: List[Dict[str, Any]] = []
		total = 0

		if propiedades_module is not None:
			listar = getattr(propiedades_module, "listar_propiedades", None)
			buscar = getattr(propiedades_module, "buscar_propiedades", None)
			contar = getattr(propiedades_module, "contar_propiedades", None)

			try:
				if search_text and buscar:
					data = _call_with_supported_kwargs(
						buscar,
						texto=search_text,
						page=self.page,
						page_size=self.page_size,
						filtros=filtros,
					)
				elif listar:
					data = _call_with_supported_kwargs(
						listar,
						page=self.page,
						page_size=self.page_size,
						filtros=filtros,
					)
				if contar:
					total = _call_with_supported_kwargs(
						contar,
						texto=search_text,
						filtros=filtros,
					)
			except Exception:
				LOG.exception("Error consultando propiedades en module.propiedades")

		if not isinstance(data, list):
			data = []
		if not total:
			total = len(data)

		self.total = total
		self._rows = data
		self._render_table()

	def _render_table(self) -> None:
		for i in self.tree.get_children():
			self.tree.delete(i)

		for p in self._rows:
			pid = p.get("id", "")
			titulo = p.get("titulo", "")
			precio = p.get("precio", "")
			estado = p.get("estado", "")
			ciudad = p.get("ciudad", "")
			metros = p.get("metros", "")
			self.tree.insert("", tk.END, values=(pid, titulo, precio, estado, ciudad, metros))

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
		self.var_estado.set("Todos")
		self.var_precio_min.set("")
		self.var_precio_max.set("")
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
		if PropiedadForm is None:
			messagebox.showerror("Error", "PropiedadForm no disponible.")
			return
		dlg = PropiedadForm(master=self.winfo_toplevel(), mode="crear")
		dlg.grab_set()
		self.wait_window(dlg)
		self._load_data()

	def _on_editar(self) -> None:
		prop = self._get_selected()
		if not prop:
			messagebox.showwarning("Atencion", "Seleccione una propiedad.")
			return
		if PropiedadForm is None:
			messagebox.showerror("Error", "PropiedadForm no disponible.")
			return
		dlg = PropiedadForm(master=self.winfo_toplevel(), mode="editar", propiedad=prop)
		dlg.grab_set()
		self.wait_window(dlg)
		self._load_data()

	def _on_ver_detalle(self) -> None:
		self._on_editar()

	def _on_eliminar(self) -> None:
		prop = self._get_selected()
		if not prop:
			messagebox.showwarning("Atencion", "Seleccione una propiedad.")
			return
		if not messagebox.askyesno("Confirmar", "Desea eliminar la propiedad seleccionada?"):
			return
		eliminar = getattr(propiedades_module, "eliminar_propiedad", None) if propiedades_module else None
		if eliminar is None:
			messagebox.showerror("Error", "El modulo de propiedades no soporta eliminacion.")
			return
		try:
			eliminar(prop.get("id"))
			self._load_data()
		except Exception:
			LOG.exception("Error eliminando propiedad")
			messagebox.showerror("Error", "No se pudo eliminar la propiedad.")

	def _prev_page(self) -> None:
		if self.page > 1:
			self.page -= 1
			self._load_data()

	def _next_page(self) -> None:
		self.page += 1
		self._load_data()


def main_test() -> None:
	root = tk.Tk()
	root.title("Propiedades")
	vista = PropiedadLista(root)
	vista.pack(fill=tk.BOTH, expand=True)
	root.mainloop()


if __name__ == "__main__":
	main_test()
