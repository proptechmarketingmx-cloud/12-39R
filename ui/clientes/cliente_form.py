"""Formulario de cliente.

Formulario completo en modo crear/editar con pestañas por seccion.
Todos los campos son opcionales; se autocompletan valores minimos para guardar.
"""
from __future__ import annotations

import json
import logging
import os
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

STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "database", "seeds", "clientes_store.json")


def _load_store() -> list[Dict[str, Any]]:
	path = os.path.abspath(STORE_PATH)
	if not os.path.exists(path):
		return []
	try:
		with open(path, "r", encoding="utf-8") as f:
			return json.load(f)
	except Exception:
		LOG.exception("No se pudo leer el store de clientes")
		return []


def _save_store(data: list[Dict[str, Any]]) -> None:
	path = os.path.abspath(STORE_PATH)
	os.makedirs(os.path.dirname(path), exist_ok=True)
	try:
		with open(path, "w", encoding="utf-8") as f:
			json.dump(data, f, indent=2, ensure_ascii=False)
	except Exception:
		LOG.exception("No se pudo guardar el store de clientes")


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
		options = ["Messenger Marketplace", "Referido", "Otro"]
		ttk.Label(parent, text="Metodo de captacion").grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
		self.vars_captacion["metodo_captacion"] = tk.StringVar()
		cb = ttk.Combobox(parent, textvariable=self.vars_captacion["metodo_captacion"], state="readonly")
		cb["values"] = options
		cb.grid(row=0, column=1, sticky=tk.EW, padx=6)
		parent.columnconfigure(1, weight=1)

	def _build_prop_interes(self, parent: ttk.Frame) -> None:
		self.vars_prop_interes: Dict[str, tk.StringVar] = {}
		labels = [
			("Pais", "pi_pais"),
			("Estado", "pi_estado"),
			("Ciudad", "pi_ciudad"),
			("Zona", "pi_zona"),
			("Tipo de interes (compra/renta/venta)", "pi_tipo"),
		]
		for i, (label, key) in enumerate(labels):
			ttk.Label(parent, text=label).grid(row=i, column=0, sticky=tk.W, padx=6, pady=4)
			self.vars_prop_interes[key] = tk.StringVar()
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
			ttk.Entry(parent, textvariable=self.vars_historial[key]).grid(row=i, column=1, sticky=tk.EW, padx=6)
		parent.columnconfigure(1, weight=1)

	def _populate(self) -> None:
		try:
			p = self.cliente
			if not p:
				return
			# personal
			self.vars_personal.get("primer_nombre", tk.StringVar()).set(p.get("primer_nombre", ""))
			self.vars_personal.get("segundo_nombre", tk.StringVar()).set(p.get("segundo_nombre", ""))
			self.vars_personal.get("apellido_paterno", tk.StringVar()).set(p.get("apellido_paterno", ""))
			self.vars_personal.get("apellido_materno", tk.StringVar()).set(p.get("apellido_materno", ""))
			self.vars_personal.get("curp", tk.StringVar()).set(p.get("curp", ""))
			self.vars_personal.get("fecha_nacimiento", tk.StringVar()).set(p.get("fecha_nacimiento", ""))
			self.vars_personal.get("edad", tk.StringVar()).set(str(p.get("edad", "")))
			self.vars_personal.get("genero", tk.StringVar()).set(p.get("genero", ""))
			self.vars_personal.get("estado_civil", tk.StringVar()).set(p.get("estado_civil", ""))
			self.vars_personal.get("telefono", tk.StringVar()).set(p.get("telefono", ""))
			self.vars_personal.get("correo", tk.StringVar()).set(p.get("correo", ""))
			self.vars_personal.get("pais", tk.StringVar()).set(p.get("pais", ""))
			self.vars_personal.get("estado", tk.StringVar()).set(p.get("estado", ""))
			self.vars_personal.get("ciudad", tk.StringVar()).set(p.get("ciudad", ""))
			self.vars_personal.get("zona", tk.StringVar()).set(p.get("zona", ""))

			# laboral
			self.vars_laboral.get("ocupacion", tk.StringVar()).set(p.get("ocupacion", ""))
			self.vars_laboral.get("antiguedad_laboral", tk.StringVar()).set(p.get("antiguedad_laboral", ""))

			# financiero
			for key in ["ingreso_mensual", "tipo_credito", "buro_credito", "presupuesto_min", "presupuesto_max"]:
				self.vars_financiero.get(key, tk.StringVar()).set(p.get(key, ""))

			# academico
			self.vars_academico.get("nivel_educativo", tk.StringVar()).set(p.get("nivel_educativo", ""))

			# familiar
			self.vars_familiar.get("hijos", tk.StringVar()).set(p.get("hijos", ""))

			# captacion
			self.vars_captacion.get("metodo_captacion", tk.StringVar()).set(p.get("metodo_captacion", ""))

			# propiedad interes
			for key in ["pi_pais", "pi_estado", "pi_ciudad", "pi_zona", "pi_tipo"]:
				self.vars_prop_interes.get(key, tk.StringVar()).set(p.get(key, ""))

			# historial
			for key in ["deudor_alimenticio", "propiedades_previas", "num_propiedades_previas", "edad_adquisicion"]:
				self.vars_historial.get(key, tk.StringVar()).set(p.get(key, ""))
		except Exception:
			LOG.exception("Error poblando formulario de cliente")

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

	def _validar_telefonos(self) -> Optional[str]:
		val = self.vars_personal.get("telefono", tk.StringVar()).get().strip()
		if val and (not val.isdigit() or len(val) != 10):
			return "El telefono debe tener 10 digitos numericos."
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
				return bool(clientes_module.find_by_curp(curp))  # type: ignore
		except Exception:
			LOG.exception("Error consultando modules.clientes.find_by_curp")

		data = _load_store()
		for c in data:
			if c.get("curp") == curp:
				if self.mode == "editar" and c.get("id") == self.cliente.get("id"):
					return False
				return True
		return False

	def _on_guardar(self) -> None:
		# Validaciones opcionales
		err = self._validar_curp() or self._validar_telefonos()
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
			"fecha_nacimiento": self.vars_personal.get("fecha_nacimiento", tk.StringVar()).get(),
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
			"metodo_captacion": self.vars_captacion.get("metodo_captacion", tk.StringVar()).get(),
			"pi_pais": self.vars_prop_interes.get("pi_pais", tk.StringVar()).get(),
			"pi_estado": self.vars_prop_interes.get("pi_estado", tk.StringVar()).get(),
			"pi_ciudad": self.vars_prop_interes.get("pi_ciudad", tk.StringVar()).get(),
			"pi_zona": self.vars_prop_interes.get("pi_zona", tk.StringVar()).get(),
			"pi_tipo": self.vars_prop_interes.get("pi_tipo", tk.StringVar()).get(),
			"deudor_alimenticio": self.vars_historial.get("deudor_alimenticio", tk.StringVar()).get(),
			"propiedades_previas": self.vars_historial.get("propiedades_previas", tk.StringVar()).get(),
			"num_propiedades_previas": self.vars_historial.get("num_propiedades_previas", tk.StringVar()).get(),
			"edad_adquisicion": self.vars_historial.get("edad_adquisicion", tk.StringVar()).get(),
		}

		try:
			if clientes_module and hasattr(clientes_module, "save"):
				clientes_module.save(cliente)  # type: ignore
			else:
				data = _load_store()
				cliente["id"] = str(max((int(c.get("id", 0)) for c in data), default=0) + 1)
				data.append(cliente)
				_save_store(data)
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
