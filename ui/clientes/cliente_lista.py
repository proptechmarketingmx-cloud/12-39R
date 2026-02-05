"""Lista de clientes con busqueda, filtros y paginacion.

Usa `modules.clientes` si existe (listar_clientes, buscar_clientes, contar_clientes)
y cae a un store JSON de desarrollo cuando no estan disponibles.
"""
from __future__ import annotations

import json
import logging
import os
import math
from typing import Any, Dict, List, Optional, Callable

import tkinter as tk
from tkinter import ttk, messagebox

try:
	from modules import clientes as clientes_module
except Exception:
	clientes_module = None

try:
	from modules.auth import auth_manager
except Exception:
	auth_manager = None  # type: ignore

try:
	from ui.clientes.cliente_form import ClienteForm
except Exception:
	ClienteForm = None  # type: ignore

try:
	import config.config as _config
except Exception:
	_config = None

LOG = logging.getLogger(__name__)

STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "database", "seeds", "clientes_store.json")


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


def _load_store() -> List[Dict[str, Any]]:
	path = os.path.abspath(STORE_PATH)
	if not os.path.exists(path):
		return []
	try:
		with open(path, "r", encoding="utf-8") as f:
			return json.load(f)
	except Exception:
		LOG.exception("No se pudo leer el store de clientes")
		return []


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


class ClienteLista(ttk.Frame):
	"""Vista de lista de clientes con busqueda, filtros y paginacion."""

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
		self.var_tipo = tk.StringVar(value="Todos")
		self.var_pres_min = tk.StringVar()
		self.var_pres_max = tk.StringVar()

		ttk.Label(filters, text="Estado:", font=font).grid(row=0, column=0, sticky=tk.W)
		cb_estado = ttk.Combobox(filters, textvariable=self.var_estado, state="readonly")
		cb_estado["values"] = ["Todos", "Prospecto", "Caliente", "Frio", "Cerrado"]
		cb_estado.grid(row=0, column=1, sticky=tk.W, padx=4)

		ttk.Label(filters, text="Tipo Cliente:", font=font).grid(row=0, column=2, sticky=tk.W, padx=(8, 0))
		cb_tipo = ttk.Combobox(filters, textvariable=self.var_tipo, state="readonly")
		cb_tipo["values"] = ["Todos", "Comprador", "Vendedor", "Arrendador", "Arrendatario"]
		cb_tipo.grid(row=0, column=3, sticky=tk.W, padx=4)

		ttk.Label(filters, text="Presupuesto Min:", font=font).grid(row=0, column=4, sticky=tk.W, padx=(8, 0))
		ttk.Entry(filters, textvariable=self.var_pres_min, width=12).grid(row=0, column=5, sticky=tk.W, padx=4)

		ttk.Label(filters, text="Presupuesto Max:", font=font).grid(row=0, column=6, sticky=tk.W, padx=(8, 0))
		ttk.Entry(filters, textvariable=self.var_pres_max, width=12).grid(row=0, column=7, sticky=tk.W, padx=4)

		ttk.Button(filters, text="Aplicar", command=self._on_buscar).grid(row=0, column=8, sticky=tk.W, padx=(8, 0))

		# Acciones
		actions = ttk.Frame(self)
		actions.pack(fill=tk.X, padx=8, pady=(0, 6))
		btn_new = ttk.Button(actions, text="Nuevo Cliente", command=self._on_nuevo)
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

		columns = ("id", "nombre", "telefono", "estado", "score", "fecha")
		self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
		self.tree.heading("id", text="ID")
		self.tree.heading("nombre", text="Nombre Completo")
		self.tree.heading("telefono", text="Telefono")
		self.tree.heading("estado", text="Estado Cliente")
		self.tree.heading("score", text="Score")
		self.tree.heading("fecha", text="Fecha Registro")

		self.tree.column("id", width=60, anchor=tk.CENTER)
		self.tree.column("nombre", width=220, anchor=tk.W)
		self.tree.column("telefono", width=120, anchor=tk.W)
		self.tree.column("estado", width=120, anchor=tk.CENTER)
		self.tree.column("score", width=80, anchor=tk.CENTER)
		self.tree.column("fecha", width=120, anchor=tk.CENTER)

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

		# Estilo basico
		style = ttk.Style()
		style.configure("Treeview.Heading", foreground=primary)

	def _get_current_user(self) -> Optional[Dict[str, Any]]:
		if auth_manager is None:
			return None
		return auth_manager.get_current_user()

	def _es_admin(self) -> bool:
		if auth_manager is None:
			return False
		return auth_manager.is_admin()

	def _get_filters(self) -> Dict[str, Any]:
		estado = self.var_estado.get()
		tipo = self.var_tipo.get()
		pres_min = _safe_float(self.var_pres_min.get() or 0, 0.0)
		pres_max = _safe_float(self.var_pres_max.get() or 0, 0.0)
		filtros: Dict[str, Any] = {}
		if estado and estado != "Todos":
			filtros["estado_cliente"] = estado
		if tipo and tipo != "Todos":
			filtros["tipo_cliente"] = tipo
		if pres_min:
			filtros["presupuesto_min"] = pres_min
		if pres_max:
			filtros["presupuesto_max"] = pres_max
		return filtros

	def _load_data(self) -> None:
		search_text = (self.var_search.get() or "").strip()
		filtros = self._get_filters()

		usuario = self._get_current_user()
		asesor_id = None
		if usuario and not self._es_admin():
			asesor_id = usuario.get("id")

		data: List[Dict[str, Any]] = []
		total = 0

		if clientes_module is not None:
			listar = getattr(clientes_module, "listar_clientes", None)
			buscar = getattr(clientes_module, "buscar_clientes", None)
			contar = getattr(clientes_module, "contar_clientes", None)

			try:
				if search_text and buscar:
					data = _call_with_supported_kwargs(
						buscar,
						texto=search_text,
						page=self.page,
						page_size=self.page_size,
						asesor_id=asesor_id,
						filtros=filtros,
					)
				elif listar:
					data = _call_with_supported_kwargs(
						listar,
						page=self.page,
						page_size=self.page_size,
						asesor_id=asesor_id,
						filtros=filtros,
					)
				if contar:
					total = _call_with_supported_kwargs(
						contar,
						texto=search_text,
						asesor_id=asesor_id,
						filtros=filtros,
					)
			except Exception:
				LOG.exception("Error consultando clientes en module.clientes")

		if not isinstance(data, list):
			data = []
		if not total:
			total = len(data)

		# Fallback JSON si no hay modulo o no retorno data
		if clientes_module is None or (not data and total == 0):
			data_all = _load_store()
			if asesor_id:
				data_all = [c for c in data_all if int(c.get("asesor_id", 0)) == int(asesor_id)]
			if filtros.get("estado_cliente"):
				data_all = [c for c in data_all if c.get("estado_cliente") == filtros["estado_cliente"]]
			if filtros.get("tipo_cliente"):
				data_all = [c for c in data_all if c.get("tipo_cliente") == filtros["tipo_cliente"]]
			if filtros.get("presupuesto_min"):
				data_all = [c for c in data_all if _safe_float(c.get("presupuesto", 0)) >= filtros["presupuesto_min"]]
			if filtros.get("presupuesto_max"):
				data_all = [c for c in data_all if _safe_float(c.get("presupuesto", 0)) <= filtros["presupuesto_max"]]
			if search_text:
				st = search_text.lower()
				def _match(c: Dict[str, Any]) -> bool:
					parts = [
						str(c.get("nombre", "")),
						str(c.get("apellido_paterno", "")),
						str(c.get("apellido_materno", "")),
						str(c.get("curp", "")),
						str(c.get("telefono_principal", "")),
					]
					return st in " ".join(parts).lower()
				data_all = [c for c in data_all if _match(c)]
			total = len(data_all)
			start = (self.page - 1) * self.page_size
			end = start + self.page_size
			data = data_all[start:end]

		self.total = total
		self._rows = data
		self._render_table()

	def _render_table(self) -> None:
		for i in self.tree.get_children():
			self.tree.delete(i)

		for c in self._rows:
			cid = c.get("id", "")
			nombre = " ".join(
				[
					str(c.get("nombre", c.get("nombres", ""))).strip(),
					str(c.get("apellido_paterno", "")).strip(),
					str(c.get("apellido_materno", "")).strip(),
					str(c.get("apellidos", "")).strip(),
				]
			).strip()
			telefono = c.get("telefono_principal", c.get("telefono", ""))
			estado = c.get("estado_cliente", c.get("estado", ""))
			score = c.get("scoring", c.get("score", ""))
			fecha = c.get("fecha_registro", c.get("created_at", ""))
			self.tree.insert("", tk.END, values=(cid, nombre, telefono, estado, score, fecha))

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
		self.var_tipo.set("Todos")
		self.var_pres_min.set("")
		self.var_pres_max.set("")
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
		if ClienteForm is None:
			messagebox.showerror("Error", "ClienteForm no disponible.")
			return
		dlg = ClienteForm(master=self.winfo_toplevel(), mode="crear")
		dlg.grab_set()
		self.wait_window(dlg)
		self._load_data()

	def _on_editar(self) -> None:
		cliente = self._get_selected()
		if not cliente:
			messagebox.showwarning("Atencion", "Seleccione un cliente.")
			return
		if ClienteForm is None:
			messagebox.showerror("Error", "ClienteForm no disponible.")
			return
		dlg = ClienteForm(master=self.winfo_toplevel(), mode="editar", cliente=cliente)
		dlg.grab_set()
		self.wait_window(dlg)
		self._load_data()

	def _on_ver_detalle(self) -> None:
		self._on_editar()

	def _on_eliminar(self) -> None:
		cliente = self._get_selected()
		if not cliente:
			messagebox.showwarning("Atencion", "Seleccione un cliente.")
			return
		if not messagebox.askyesno("Confirmar", "Desea eliminar el cliente seleccionado?"):
			return
		if not messagebox.askyesno("Confirmar nuevamente", "Esta accion no se puede deshacer. Desea continuar?"):
			return
		eliminar = getattr(clientes_module, "eliminar_cliente", None) if clientes_module else None
		if eliminar is None:
			messagebox.showerror("Error", "El modulo de clientes no soporta eliminacion.")
			return
		try:
			eliminar(cliente.get("id"))
			self._load_data()
		except Exception:
			LOG.exception("Error eliminando cliente")
			messagebox.showerror("Error", "No se pudo eliminar el cliente.")

	def _prev_page(self) -> None:
		if self.page > 1:
			self.page -= 1
			self._load_data()

	def _next_page(self) -> None:
		self.page += 1
		self._load_data()


def main_test() -> None:
	root = tk.Tk()
	root.title("Clientes")
	vista = ClienteLista(root)
	vista.pack(fill=tk.BOTH, expand=True)
	root.mainloop()


if __name__ == "__main__":
	main_test()
