"""Formulario de cliente.

Formulario completo en modo crear/editar con pestañas por seccion.
Todos los campos son opcionales; se autocompletan valores minimos para guardar.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import tkinter as tk
from tkinter import messagebox, ttk

try:
	from tkcalendar import DateEntry  # type: ignore
except Exception:
	DateEntry = None  # type: ignore

try:
	from modules import clientes as clientes_module
except Exception:
	clientes_module = None

LOG = logging.getLogger(__name__)



class ClienteForm(tk.Toplevel):
	"""Ventana modal para crear/editar cliente."""

	def __init__(self, master: Any = None, mode: str = "crear", cliente: Optional[Dict[str, Any]] = None) -> None:
		super().__init__(master)
		self.title("Cliente - " + ("Crear" if mode == "crear" else "Editar"))
		self.mode = mode
		self.cliente = cliente or {}
		self.resizable(True, True)
		self.geometry("900x700")

		self._build_ui()
		if self.mode == "editar":
			self._populate()

	def _build_ui(self) -> None:
		frm = ttk.Frame(self, padding=12)
		frm.pack(fill=tk.BOTH, expand=True)

		self.notebook = ttk.Notebook(frm)
		self.notebook.pack(fill=tk.BOTH, expand=True)

		# Tabs
		self.tab_personal = ttk.Frame(self.notebook)
		self.tab_laboral = ttk.Frame(self.notebook)
		self.tab_financiero = ttk.Frame(self.notebook)
		self.tab_academico = ttk.Frame(self.notebook)
		self.tab_familiar = ttk.Frame(self.notebook)
		self.tab_captacion = ttk.Frame(self.notebook)
		self.tab_prop_interes = ttk.Frame(self.notebook)
		self.tab_historial = ttk.Frame(self.notebook)

		self.notebook.add(self.tab_personal, text="Personal")
		self.notebook.add(self.tab_laboral, text="Laboral")
		self.notebook.add(self.tab_financiero, text="Financiero")
		self.notebook.add(self.tab_academico, text="Academico")
		self.notebook.add(self.tab_familiar, text="Familiar")
		self.notebook.add(self.tab_captacion, text="Captacion")
		self.notebook.add(self.tab_prop_interes, text="Propiedad Interes")
		self.notebook.add(self.tab_historial, text="Historial")

		self._build_personal(self.tab_personal)
		self._build_laboral(self.tab_laboral)
		self._build_financiero(self.tab_financiero)
		self._build_academico(self.tab_academico)
		self._build_familiar(self.tab_familiar)
		self._build_captacion(self.tab_captacion)
		self._build_prop_interes(self.tab_prop_interes)
		self._build_historial(self.tab_historial)
		self._build_estadisticas(self.tab_historial)

		# Botones
		btn_frame = ttk.Frame(frm)
		btn_frame.pack(fill=tk.X, pady=(10, 0))
		ttk.Button(btn_frame, text="Guardar", command=self._on_guardar).pack(side=tk.RIGHT, padx=6)
		ttk.Button(btn_frame, text="Limpiar", command=self._on_limpiar).pack(side=tk.RIGHT)
		ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT, padx=6)

	def _build_personal(self, parent: ttk.Frame) -> None:
		self.vars_personal: Dict[str, tk.StringVar] = {}

		row = 0
		def _add(label: str, key: str, widget: str = "entry", values: Optional[list[str]] = None) -> None:
			nonlocal row
			ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=6, pady=4)
			self.vars_personal[key] = tk.StringVar()
			if widget == "combo":
				cb = ttk.Combobox(parent, textvariable=self.vars_personal[key], state="readonly")
				cb["values"] = values or []
				cb.grid(row=row, column=1, sticky=tk.EW, padx=6)
			elif widget == "date":
				if DateEntry:
					entry = DateEntry(parent, date_pattern="yyyy-mm-dd")  # type: ignore
					entry.grid(row=row, column=1, sticky=tk.EW, padx=6)  # type: ignore
					self.vars_personal[key + "__widget"] = entry
				else:
					ttk.Entry(parent, textvariable=self.vars_personal[key]).grid(row=row, column=1, sticky=tk.EW, padx=6)
			else:
				ttk.Entry(parent, textvariable=self.vars_personal[key]).grid(row=row, column=1, sticky=tk.EW, padx=6)
			row += 1

		_add("Primer nombre", "primer_nombre")
		_add("Segundo nombre", "segundo_nombre")
		_add("Apellido paterno", "apellido_paterno")
		_add("Apellido materno", "apellido_materno")
		_add("CURP", "curp")
		_add("Fecha de nacimiento (YYYY-MM-DD)", "fecha_nacimiento", widget="date")
		_add("Edad", "edad")
		_add("Genero", "genero", widget="combo", values=["Hombre", "Mujer"])
		_add("Estado civil", "estado_civil", widget="combo", values=["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a"])

		# Metodo de contacto
		ttk.Label(parent, text="Metodo de contacto", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=6, pady=(12, 4))
		row += 1
		_add("Telefono", "telefono")
		_add("Correo", "correo")

		# Residencia
		ttk.Label(parent, text="Residencia", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=6, pady=(12, 4))
		row += 1
		_add("Pais", "pais")
		_add("Estado", "estado")
		_add("Ciudad", "ciudad")
		_add("Zona", "zona")

		parent.columnconfigure(1, weight=1)

	def _build_laboral(self, parent: ttk.Frame) -> None:
		self.vars_laboral: Dict[str, tk.StringVar] = {}
		labels = [
			("Ocupacion", "ocupacion"),
			("Antiguedad laboral", "antiguedad_laboral"),
		]
		for i, (label, key) in enumerate(labels):
			ttk.Label(parent, text=label).grid(row=i, column=0, sticky=tk.W, padx=6, pady=4)
			self.vars_laboral[key] = tk.StringVar()
			ttk.Entry(parent, textvariable=self.vars_laboral[key]).grid(row=i, column=1, sticky=tk.EW, padx=6)
		parent.columnconfigure(1, weight=1)

	def _build_financiero(self, parent: ttk.Frame) -> None:
		self.vars_financiero: Dict[str, tk.StringVar] = {}
		labels = [
			("Ingreso x mes", "ingreso_mensual"),
			("Tipo de credito disponible", "tipo_credito"),
			("Buro de credito", "buro_credito"),
		]
		row = 0
		for label, key in labels:
			ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=6, pady=4)
			self.vars_financiero[key] = tk.StringVar()
			if key == "tipo_credito":
				cb = ttk.Combobox(parent, textvariable=self.vars_financiero[key], state="readonly")
				cb["values"] = ["Infonavit", "Fovissste", "Bancario", "Contado"]
				cb.grid(row=row, column=1, sticky=tk.EW, padx=6)
			elif key == "buro_credito":
				cb = ttk.Combobox(parent, textvariable=self.vars_financiero[key], state="readonly")
				cb["values"] = ["Si", "No"]
				cb.grid(row=row, column=1, sticky=tk.EW, padx=6)
			else:
				ttk.Entry(parent, textvariable=self.vars_financiero[key]).grid(row=row, column=1, sticky=tk.EW, padx=6)
			row += 1

		ttk.Label(parent, text="Presupuesto", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=6, pady=(12, 4))
		row += 1
		for label, key in [("Minimo", "presupuesto_min"), ("Maximo", "presupuesto_max")]:
			ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=6, pady=4)
			self.vars_financiero[key] = tk.StringVar()
			ttk.Entry(parent, textvariable=self.vars_financiero[key]).grid(row=row, column=1, sticky=tk.EW, padx=6)
			row += 1

		parent.columnconfigure(1, weight=1)

	def _build_academico(self, parent: ttk.Frame) -> None:
		self.vars_academico: Dict[str, tk.StringVar] = {}
		ttk.Label(parent, text="Nivel educativo").grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
		self.vars_academico["nivel_educativo"] = tk.StringVar()
		cb = ttk.Combobox(parent, textvariable=self.vars_academico["nivel_educativo"], state="readonly")
		cb["values"] = ["Primaria", "Secundaria", "Preparatoria", "Licenciatura", "Posgrado"]
		cb.grid(row=0, column=1, sticky=tk.EW, padx=6)
		parent.columnconfigure(1, weight=1)

	def _build_familiar(self, parent: ttk.Frame) -> None:
		self.vars_familiar: Dict[str, tk.StringVar] = {}
		ttk.Label(parent, text="Hijos").grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
		self.vars_familiar["hijos"] = tk.StringVar()
		ttk.Entry(parent, textvariable=self.vars_familiar["hijos"]).grid(row=0, column=1, sticky=tk.EW, padx=6)
		parent.columnconfigure(1, weight=1)

	def _build_captacion(self, parent: ttk.Frame) -> None:
		self.vars_captacion: Dict[str, tk.StringVar] = {}
		origenes = ["Referido", "WhatsApp", "Marketplace", "Otro"]
		ttk.Label(parent, text="Origen de captacion").grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
		self.vars_captacion["origen_captacion"] = tk.StringVar()
		cb2 = ttk.Combobox(parent, textvariable=self.vars_captacion["origen_captacion"], state="readonly")
		cb2["values"] = origenes
		cb2.grid(row=0, column=1, sticky=tk.EW, padx=6)
		parent.columnconfigure(1, weight=1)

	def _build_prop_interes(self, parent: ttk.Frame) -> None:
		self.vars_prop_interes: Dict[str, tk.StringVar] = {}
		labels = [
			("Pais", "pi_pais"),
			("Estado", "pi_estado"),
			("Ciudad", "pi_ciudad"),
			("Zona", "pi_zona"),
			("Tipo de interes (compra/renta/venta)", "pi_tipo"),
			("Zona de interes (mapa de calor)", "zona_interes"),
		]
		for i, (label, key) in enumerate(labels):
			ttk.Label(parent, text=label).grid(row=i, column=0, sticky=tk.W, padx=6, pady=4)
			self.vars_prop_interes[key] = tk.StringVar()
			if key == "pi_tipo":
				cb = ttk.Combobox(parent, textvariable=self.vars_prop_interes[key], state="readonly")
				cb["values"] = ["Compra", "Renta", "Venta"]
				cb.grid(row=i, column=1, sticky=tk.EW, padx=6)
			else:
				ttk.Entry(parent, textvariable=self.vars_prop_interes[key]).grid(row=i, column=1, sticky=tk.EW, padx=6)
		parent.columnconfigure(1, weight=1)

	def _build_historial(self, parent: ttk.Frame) -> None:
		self.vars_historial: Dict[str, tk.StringVar] = {}
		labels = [
			("Deudor alimenticio", "deudor_alimenticio"),
			("Propiedades previas (si/no)", "propiedades_previas"),
			("N° de propiedades previas", "num_propiedades_previas"),
			("Edad de adquisicion", "edad_adquisicion"),
		]
		for i, (label, key) in enumerate(labels):
			ttk.Label(parent, text=label).grid(row=i, column=0, sticky=tk.W, padx=6, pady=4)
			self.vars_historial[key] = tk.StringVar()
			if key in ("deudor_alimenticio", "propiedades_previas"):
				cb = ttk.Combobox(parent, textvariable=self.vars_historial[key], state="readonly")
				cb["values"] = ["Si", "No"]
				cb.grid(row=i, column=1, sticky=tk.EW, padx=6)
			else:
				ttk.Entry(parent, textvariable=self.vars_historial[key]).grid(row=i, column=1, sticky=tk.EW, padx=6)
		parent.columnconfigure(1, weight=1)

	def _build_estadisticas(self, parent: ttk.Frame) -> None:
		"""Campos para estadisticas y segmentacion."""
		self.vars_stats: Dict[str, tk.StringVar] = {}
		row = 5
		ttk.Label(parent, text="Estadisticas", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=6, pady=(12, 4))
		row += 1

		ttk.Label(parent, text="Estado cliente").grid(row=row, column=0, sticky=tk.W, padx=6, pady=4)
		self.vars_stats["estado_cliente"] = tk.StringVar()
		cb_estado = ttk.Combobox(parent, textvariable=self.vars_stats["estado_cliente"], state="readonly")
		cb_estado["values"] = ["Prospecto", "Caliente", "Frio", "Cerrado"]
		cb_estado.grid(row=row, column=1, sticky=tk.EW, padx=6)
		row += 1

		ttk.Label(parent, text="Tipo cliente").grid(row=row, column=0, sticky=tk.W, padx=6, pady=4)
		self.vars_stats["tipo_cliente"] = tk.StringVar()
		cb_tipo = ttk.Combobox(parent, textvariable=self.vars_stats["tipo_cliente"], state="readonly")
		cb_tipo["values"] = ["Comprador", "Vendedor", "Arrendador", "Arrendatario"]
		cb_tipo.grid(row=row, column=1, sticky=tk.EW, padx=6)
		row += 1

		ttk.Label(parent, text="Etapa embudo").grid(row=row, column=0, sticky=tk.W, padx=6, pady=4)
		self.vars_stats["etapa_embudo"] = tk.StringVar()
		cb_etapa = ttk.Combobox(parent, textvariable=self.vars_stats["etapa_embudo"], state="readonly")
		cb_etapa["values"] = ["Nuevo", "Contactado", "Visitado", "Negociacion", "Cierre"]
		cb_etapa.grid(row=row, column=1, sticky=tk.EW, padx=6)
		row += 1

	def _populate(self) -> None:
		try:
			p = self.cliente
			if not p:
				return
			def _v(val: Any) -> str:
				if val is None:
					return ""
				s = str(val)
				return "" if s.lower() == "none" else s
			def _v_bool(val: Any) -> str:
				if val is True or str(val).strip().lower() in ("true", "1", "si", "sí"):
					return "Si"
				if val is False or str(val).strip().lower() in ("false", "0", "no"):
					return "No"
				return _v(val)
			def _interes_val(key: str) -> Any:
				val = p.get(key)
				if val is None and key.startswith("pi_"):
					alt = "interes_" + key[3:]
					val = p.get(alt)
				return val
			# personal
			self.vars_personal.get("primer_nombre", tk.StringVar()).set(_v(p.get("primer_nombre")))
			self.vars_personal.get("segundo_nombre", tk.StringVar()).set(_v(p.get("segundo_nombre")))
			self.vars_personal.get("apellido_paterno", tk.StringVar()).set(_v(p.get("apellido_paterno")))
			self.vars_personal.get("apellido_materno", tk.StringVar()).set(_v(p.get("apellido_materno")))
			self.vars_personal.get("curp", tk.StringVar()).set(_v(p.get("curp")))
			self._set_fecha_nacimiento(p.get("fecha_nacimiento"))
			self.vars_personal.get("edad", tk.StringVar()).set(_v(p.get("edad")))
			self.vars_personal.get("genero", tk.StringVar()).set(_v(p.get("genero")))
			self.vars_personal.get("estado_civil", tk.StringVar()).set(_v(p.get("estado_civil")))
			self.vars_personal.get("telefono", tk.StringVar()).set(_v(p.get("telefono")))
			self.vars_personal.get("correo", tk.StringVar()).set(_v(p.get("correo")))
			self.vars_personal.get("pais", tk.StringVar()).set(_v(p.get("pais")))
			self.vars_personal.get("estado", tk.StringVar()).set(_v(p.get("estado")))
			self.vars_personal.get("ciudad", tk.StringVar()).set(_v(p.get("ciudad")))
			self.vars_personal.get("zona", tk.StringVar()).set(_v(p.get("zona")))

			# laboral
			self.vars_laboral.get("ocupacion", tk.StringVar()).set(_v(p.get("ocupacion")))
			self.vars_laboral.get("antiguedad_laboral", tk.StringVar()).set(_v(p.get("antiguedad_laboral")))

			# financiero
			for key in ["ingreso_mensual", "tipo_credito", "buro_credito", "presupuesto_min", "presupuesto_max"]:
				self.vars_financiero.get(key, tk.StringVar()).set(_v(p.get(key)))

			# academico
			self.vars_academico.get("nivel_educativo", tk.StringVar()).set(_v(p.get("nivel_educativo")))

			# familiar
			self.vars_familiar.get("hijos", tk.StringVar()).set(_v(p.get("hijos")))

			# captacion
			self.vars_captacion.get("origen_captacion", tk.StringVar()).set(_v(p.get("origen_captacion")))

			# propiedad interes
			for key in ["pi_pais", "pi_estado", "pi_ciudad", "pi_zona", "pi_tipo", "zona_interes"]:
				self.vars_prop_interes.get(key, tk.StringVar()).set(_v(_interes_val(key)))

			# historial
			self.vars_historial.get("deudor_alimenticio", tk.StringVar()).set(_v_bool(p.get("deudor_alimenticio")))
			self.vars_historial.get("propiedades_previas", tk.StringVar()).set(_v_bool(p.get("propiedades_previas")))
			self.vars_historial.get("num_propiedades_previas", tk.StringVar()).set(_v(p.get("num_propiedades_previas")))
			self.vars_historial.get("edad_adquisicion", tk.StringVar()).set(_v(p.get("edad_adquisicion")))

			# stats
			if hasattr(self, "vars_stats"):
				self.vars_stats.get("estado_cliente", tk.StringVar()).set(_v(p.get("estado_cliente")))
				self.vars_stats.get("tipo_cliente", tk.StringVar()).set(_v(p.get("tipo_cliente")))
				self.vars_stats.get("etapa_embudo", tk.StringVar()).set(_v(p.get("etapa_embudo")))
		except Exception:
			LOG.exception("Error poblando formulario de cliente")

	def _set_fecha_nacimiento(self, value: Any) -> None:
		widget = self.vars_personal.get("fecha_nacimiento__widget")
		if value is None or str(value).lower() == "none":
			value = ""
		if widget:
			try:
				if value:
					widget.set_date(value)  # type: ignore
				else:
					widget.delete(0, tk.END)  # type: ignore
			except Exception:
				pass
		else:
			self.vars_personal.get("fecha_nacimiento", tk.StringVar()).set(value or "")

	def _get_fecha_nacimiento(self) -> str:
		widget = self.vars_personal.get("fecha_nacimiento__widget")
		if widget:
			try:
				val = widget.get()  # type: ignore
				return str(val).strip()
			except Exception:
				return ""
		return self.vars_personal.get("fecha_nacimiento", tk.StringVar()).get().strip()

	def _on_limpiar(self) -> None:
		for d in (
			self.vars_personal,
			self.vars_laboral,
			self.vars_financiero,
			self.vars_academico,
			self.vars_familiar,
			self.vars_captacion,
			self.vars_prop_interes,
			self.vars_historial,
		):
			for v in d.values():
				try:
					v.set("")
				except Exception:
					pass
		if hasattr(self, "vars_stats"):
			for v in self.vars_stats.values():
				try:
					v.set("")
				except Exception:
					pass
		self._set_fecha_nacimiento("")

	def _validar_telefonos(self) -> Optional[str]:
		val = self.vars_personal.get("telefono", tk.StringVar()).get().strip()
		if val and (not val.isdigit() or len(val) != 10):
			return "El telefono debe tener 10 digitos numericos."
		return None

	def _validar_edad(self) -> Optional[str]:
		val = self.vars_personal.get("edad", tk.StringVar()).get().strip()
		if not val:
			return None
		if not val.isdigit():
			return "La edad debe ser un numero entero."
		return None

	def _validar_montos(self) -> Optional[str]:
		def _to_float(v: str) -> Optional[float]:
			if not v:
				return None
			try:
				return float(v)
			except Exception:
				return None

		ingreso = self.vars_financiero.get("ingreso_mensual", tk.StringVar()).get().strip()
		pmin = self.vars_financiero.get("presupuesto_min", tk.StringVar()).get().strip()
		pmax = self.vars_financiero.get("presupuesto_max", tk.StringVar()).get().strip()

		if ingreso and _to_float(ingreso) is None:
			return "Ingreso mensual debe ser numerico."
		if pmin and _to_float(pmin) is None:
			return "Presupuesto minimo debe ser numerico."
		if pmax and _to_float(pmax) is None:
			return "Presupuesto maximo debe ser numerico."
		if pmin and pmax:
			min_val = _to_float(pmin)
			max_val = _to_float(pmax)
			if min_val is not None and max_val is not None and min_val > max_val:
				return "Presupuesto minimo no puede ser mayor al maximo."
		return None

	def _validar_curp(self) -> Optional[str]:
		curp = self.vars_personal.get("curp", tk.StringVar()).get().strip()
		if not curp:
			return None
		if len(curp) != 18:
			return "CURP invalido (debe tener 18 caracteres)."
		return None

	def _existe_por_curp(self, curp: str) -> bool:
		try:
			if clientes_module and hasattr(clientes_module, "find_by_curp"):
				found = clientes_module.find_by_curp(curp)  # type: ignore
				if not found:
					return False
				if self.mode == "editar" and self.cliente.get("id") is not None:
					return int(found.get("id", 0)) != int(self.cliente.get("id"))
				return True
		except Exception:
			LOG.exception("Error consultando modules.clientes.find_by_curp")
		return False

	def _on_guardar(self) -> None:
		# Validaciones opcionales
		err = self._validar_curp() or self._validar_telefonos() or self._validar_edad() or self._validar_montos()
		if err:
			messagebox.showerror("Validacion", err)
			return

		primer = self.vars_personal.get("primer_nombre", tk.StringVar()).get().strip()
		segundo = self.vars_personal.get("segundo_nombre", tk.StringVar()).get().strip()
		ap_pat = self.vars_personal.get("apellido_paterno", tk.StringVar()).get().strip()
		ap_mat = self.vars_personal.get("apellido_materno", tk.StringVar()).get().strip()

		nombre = " ".join([x for x in [primer, segundo] if x]).strip()

		curp = self.vars_personal.get("curp", tk.StringVar()).get().strip()
		if curp and self._existe_por_curp(curp):
			if not messagebox.askyesno("Duplicado", "Ya existe un cliente con ese CURP. ¿Desea continuar?"):
				return

		cliente = {
			"primer_nombre": primer,
			"segundo_nombre": segundo,
			"apellido_paterno": ap_pat,
			"apellido_materno": ap_mat,
			"nombre": nombre,
			"curp": curp,
			"fecha_nacimiento": self._get_fecha_nacimiento(),
			"edad": self.vars_personal.get("edad", tk.StringVar()).get(),
			"genero": self.vars_personal.get("genero", tk.StringVar()).get(),
			"estado_civil": self.vars_personal.get("estado_civil", tk.StringVar()).get(),
			"telefono": self.vars_personal.get("telefono", tk.StringVar()).get(),
			"correo": self.vars_personal.get("correo", tk.StringVar()).get(),
			"pais": self.vars_personal.get("pais", tk.StringVar()).get(),
			"estado": self.vars_personal.get("estado", tk.StringVar()).get(),
			"ciudad": self.vars_personal.get("ciudad", tk.StringVar()).get(),
			"zona": self.vars_personal.get("zona", tk.StringVar()).get(),
			"ocupacion": self.vars_laboral.get("ocupacion", tk.StringVar()).get(),
			"antiguedad_laboral": self.vars_laboral.get("antiguedad_laboral", tk.StringVar()).get(),
			"ingreso_mensual": self.vars_financiero.get("ingreso_mensual", tk.StringVar()).get(),
			"tipo_credito": self.vars_financiero.get("tipo_credito", tk.StringVar()).get(),
			"buro_credito": self.vars_financiero.get("buro_credito", tk.StringVar()).get(),
			"presupuesto_min": self.vars_financiero.get("presupuesto_min", tk.StringVar()).get(),
			"presupuesto_max": self.vars_financiero.get("presupuesto_max", tk.StringVar()).get(),
			"nivel_educativo": self.vars_academico.get("nivel_educativo", tk.StringVar()).get(),
			"hijos": self.vars_familiar.get("hijos", tk.StringVar()).get(),
			"origen_captacion": self.vars_captacion.get("origen_captacion", tk.StringVar()).get(),
			"pi_pais": self.vars_prop_interes.get("pi_pais", tk.StringVar()).get(),
			"pi_estado": self.vars_prop_interes.get("pi_estado", tk.StringVar()).get(),
			"pi_ciudad": self.vars_prop_interes.get("pi_ciudad", tk.StringVar()).get(),
			"pi_zona": self.vars_prop_interes.get("pi_zona", tk.StringVar()).get(),
			"pi_tipo": self.vars_prop_interes.get("pi_tipo", tk.StringVar()).get(),
			"zona_interes": self.vars_prop_interes.get("zona_interes", tk.StringVar()).get(),
			"deudor_alimenticio": self.vars_historial.get("deudor_alimenticio", tk.StringVar()).get(),
			"propiedades_previas": self.vars_historial.get("propiedades_previas", tk.StringVar()).get(),
			"num_propiedades_previas": self.vars_historial.get("num_propiedades_previas", tk.StringVar()).get(),
			"edad_adquisicion": self.vars_historial.get("edad_adquisicion", tk.StringVar()).get(),
			"estado_cliente": self.vars_stats.get("estado_cliente", tk.StringVar()).get() if hasattr(self, "vars_stats") else "",
			"tipo_cliente": self.vars_stats.get("tipo_cliente", tk.StringVar()).get() if hasattr(self, "vars_stats") else "",
			"etapa_embudo": self.vars_stats.get("etapa_embudo", tk.StringVar()).get() if hasattr(self, "vars_stats") else "",
		}
		if not cliente.get("metodo_captacion"):
			cliente["metodo_captacion"] = cliente.get("origen_captacion", "")
		if self.mode == "editar" and self.cliente.get("id") is not None:
			cliente["id"] = self.cliente.get("id")

		try:
			if clientes_module and hasattr(clientes_module, "save"):
				clientes_module.save(cliente)  # type: ignore
			else:
				raise RuntimeError("Modulo de clientes no disponible")
		except Exception:
			LOG.exception("Error guardando cliente")
			messagebox.showerror("Error", "No se pudo guardar el cliente.")
			return

		messagebox.showinfo("Exito", "Cliente guardado correctamente.")
		self.destroy()


def main_test() -> None:
	root = tk.Tk()
	root.withdraw()
	f = ClienteForm(master=root)
	f.grab_set()
	root.mainloop()


if __name__ == "__main__":
	main_test()
