"""Formulario de cliente.

Formulario completo en modo crear/editar con 5 pestañas:
- Personal
- Laboral
- Financiero
- Propiedad Interés
- Otros

Incluye validaciones básicas (CURP longitud, teléfonos 10 dígitos), cálculo
automático de edad desde fecha de nacimiento, y cálculo de scoring predictivo.

El guardado intenta delegar en `modules.clientes` si existe, en otro caso
persiste en `database/seeds/clientes_store.json` para pruebas.
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
	"""Ventana modal para crear/editar cliente.

	Parámetros:
	- `master`: widget padre
	- `mode`: 'crear' o 'editar'
	- `cliente`: dict con datos cuando `mode='editar'`
	"""

	def __init__(self, master: Any = None, mode: str = "crear", cliente: Optional[Dict[str, Any]] = None) -> None:
		super().__init__(master)
		self.title("Cliente - " + ("Crear" if mode == "crear" else "Editar"))
		self.mode = mode
		self.cliente = cliente or {}
		self.resizable(False, False)

		self._build_ui()
		if self.mode == "editar":
			self._populate()

	def _build_ui(self) -> None:
		frm = ttk.Frame(self, padding=12)
		frm.pack(fill=tk.BOTH, expand=True)

		self.notebook = ttk.Notebook(frm)
		self.notebook.pack(fill=tk.BOTH, expand=True)

		# Personal
		self.tab_personal = ttk.Frame(self.notebook)
		self.notebook.add(self.tab_personal, text="Personal")
		self._build_personal(self.tab_personal)

		# Laboral
		self.tab_laboral = ttk.Frame(self.notebook)
		self.notebook.add(self.tab_laboral, text="Laboral")
		self._build_laboral(self.tab_laboral)

		# Financiero
		self.tab_financiero = ttk.Frame(self.notebook)
		self.notebook.add(self.tab_financiero, text="Financiero")
		self._build_financiero(self.tab_financiero)

		# Propiedad Interés
		self.tab_prop_interes = ttk.Frame(self.notebook)
		self.notebook.add(self.tab_prop_interes, text="Propiedad Interés")
		self._build_prop_interes(self.tab_prop_interes)

		# Otros
		self.tab_otros = ttk.Frame(self.notebook)
		self.notebook.add(self.tab_otros, text="Otros")
		self._build_otros(self.tab_otros)

		# Botones
		btn_frame = ttk.Frame(frm)
		btn_frame.pack(fill=tk.X, pady=(10, 0))
		ttk.Button(btn_frame, text="Guardar", command=self._on_guardar).pack(side=tk.RIGHT, padx=6)
		ttk.Button(btn_frame, text="Limpiar", command=self._on_limpiar).pack(side=tk.RIGHT)
		ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT, padx=6)

	def _build_personal(self, parent: ttk.Frame) -> None:
		# Campos: nombre, apellido paterno, apellido materno, CURP, fecha nacimiento, edad, genero
		labels = ["Nombre", "Apellido Paterno", "Apellido Materno", "CURP", "Fecha Nac (YYYY-MM-DD)", "Edad", "Género"]
		self.vars_personal = {k: tk.StringVar() for k in labels}

		for i, label in enumerate(labels):
			ttk.Label(parent, text=label + (" *" if label in ("Nombre", "CURP") else "")).grid(row=i, column=0, sticky=tk.W, pady=4, padx=6)
			if label == "Fecha Nac (YYYY-MM-DD)":
				if DateEntry:
					entry = DateEntry(parent, date_pattern="yyyy-mm-dd")  # type: ignore
					entry.grid(row=i, column=1, sticky=tk.EW, padx=6)  # type: ignore
					self.vars_personal[label].set("")
					self.vars_personal[label + "__widget"] = entry
				else:
					e = ttk.Entry(parent, textvariable=self.vars_personal[label])
					e.grid(row=i, column=1, sticky=tk.EW, padx=6)
					e.bind("<FocusOut>", lambda ev: self._calc_edad())
			elif label == "Edad":
				e = ttk.Entry(parent, textvariable=self.vars_personal[label], state="readonly")
				e.grid(row=i, column=1, sticky=tk.EW, padx=6)
			else:
				ttk.Entry(parent, textvariable=self.vars_personal[label]).grid(row=i, column=1, sticky=tk.EW, padx=6)

	def _build_laboral(self, parent: ttk.Frame) -> None:
		labels = ["Ocupación", "Empresa", "Teléfono Principal", "Teléfono Secundario", "Teléfono Terciario", "Estado Civil"]
		self.vars_laboral = {k: tk.StringVar() for k in labels}
		for i, label in enumerate(labels):
			ttk.Label(parent, text=label + (" *" if label.startswith("Teléfono") else "")).grid(row=i, column=0, sticky=tk.W, pady=4, padx=6)
			if label.startswith("Teléfono"):
				ttk.Entry(parent, textvariable=self.vars_laboral[label]).grid(row=i, column=1, sticky=tk.EW, padx=6)
			elif label == "Estado Civil":
				cb = ttk.Combobox(parent, values=["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a"], state="readonly", textvariable=self.vars_laboral[label])
				cb.grid(row=i, column=1, sticky=tk.EW, padx=6)
			else:
				ttk.Entry(parent, textvariable=self.vars_laboral[label]).grid(row=i, column=1, sticky=tk.EW, padx=6)

	def _build_financiero(self, parent: ttk.Frame) -> None:
		labels = ["Ingreso Mensual", "Presupuesto", "Crédito Disponible", "Tipo Crédito", "Nivel Educativo"]
		self.vars_financiero = {k: tk.StringVar() for k in labels}
		for i, label in enumerate(labels):
			ttk.Label(parent, text=label).grid(row=i, column=0, sticky=tk.W, pady=4, padx=6)
			if label == "Tipo Crédito":
				cb = ttk.Combobox(parent, values=["Hipotecario", "Infonavit", "Bancario", "Contado", "No Aplica"], state="readonly", textvariable=self.vars_financiero[label])
				cb.grid(row=i, column=1, sticky=tk.EW, padx=6)
			else:
				ttk.Entry(parent, textvariable=self.vars_financiero[label]).grid(row=i, column=1, sticky=tk.EW, padx=6)

		# Scoring
		ttk.Label(parent, text="Scoring (0-100)").grid(row=len(labels), column=0, sticky=tk.W, pady=6, padx=6)
		self.var_scoring = tk.StringVar(value="0")
		ttk.Entry(parent, textvariable=self.var_scoring, state="readonly").grid(row=len(labels), column=1, sticky=tk.EW, padx=6)
		ttk.Button(parent, text="Calcular Scoring", command=self._calcular_scoring).grid(row=len(labels)+1, column=1, sticky=tk.E, padx=6, pady=6)

	def _build_prop_interes(self, parent: ttk.Frame) -> None:
		labels = ["Tipo Propiedad", "Zona de Interés", "Número de Habitaciones", "Estado Propiedad"]
		self.vars_prop_interes = {k: tk.StringVar() for k in labels}
		for i, label in enumerate(labels):
			ttk.Label(parent, text=label).grid(row=i, column=0, sticky=tk.W, pady=4, padx=6)
			if label == "Número de Habitaciones":
				ttk.Spinbox(parent, from_=0, to=20, textvariable=self.vars_prop_interes[label]).grid(row=i, column=1, sticky=tk.W, padx=6)
			else:
				ttk.Entry(parent, textvariable=self.vars_prop_interes[label]).grid(row=i, column=1, sticky=tk.EW, padx=6)

	def _build_otros(self, parent: ttk.Frame) -> None:
		labels = ["Notas", "Fuente de Captación", "Estado Cliente"]
		self.vars_otros = {k: tk.StringVar() for k in labels}
		self.txt_notas: tk.Text | None = None
		for i, label in enumerate(labels):
			ttk.Label(parent, text=label).grid(row=i, column=0, sticky=tk.W, pady=4, padx=6)
			if label == "Notas":
				txt = tk.Text(parent, height=6, width=40)
				txt.grid(row=i, column=1, sticky=tk.EW, padx=6)
				self.txt_notas = txt
			else:
				if label == "Estado Cliente":
					cb = ttk.Combobox(parent, values=["Activo", "Inactivo", "Potencial", "No Interesado"], state="readonly", textvariable=self.vars_otros[label])
					cb.grid(row=i, column=1, sticky=tk.EW, padx=6)
				else:
					ttk.Entry(parent, textvariable=self.vars_otros[label]).grid(row=i, column=1, sticky=tk.EW, padx=6)

	def _populate(self) -> None:
		# Rellenar campos con datos del cliente (modo editar)
		try:
			p = self.cliente
			if not p:
				return
			# Personal
			mp = self.vars_personal
			mp["Nombre"].set(p.get("nombre", ""))
			mp["Apellido Paterno"].set(p.get("apellido_paterno", ""))
			mp["Apellido Materno"].set(p.get("apellido_materno", ""))
			mp["CURP"].set(p.get("curp", ""))
			mp["Fecha Nac (YYYY-MM-DD)"].set(p.get("fecha_nacimiento", ""))
			mp["Edad"].set(str(p.get("edad", "")))
			mp["Género"].set(p.get("genero", ""))
			# Otros (simplificado)
			self.vars_otros.get("Estado Cliente", tk.StringVar()).set(p.get("estado_cliente", ""))
		except Exception:
			LOG.exception("Error poblando formulario de cliente")

	def _on_limpiar(self) -> None:
		for d in (self.vars_personal, self.vars_laboral, self.vars_financiero, self.vars_prop_interes):
			for v in d.values():
				try:
					v.set("")
				except Exception:
					pass
		# Notas
		if self.txt_notas:
			self.txt_notas.delete("1.0", tk.END)

	def _calc_edad(self) -> None:
		val = self.vars_personal.get("Fecha Nac (YYYY-MM-DD)", tk.StringVar()).get()
		try:
			dt = datetime.strptime(val, "%Y-%m-%d")
			today = datetime.today()
			edad = today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
			self.vars_personal["Edad"].set(str(edad))
		except Exception:
			# Ignore parse errors
			pass

	def _validar_telefonos(self) -> Optional[str]:
		for key in ("Teléfono Principal", "Teléfono Secundario", "Teléfono Terciario"):
			val = self.vars_laboral[key].get().strip()
			if val and (not val.isdigit() or len(val) != 10):
				return f"El campo {key} debe tener 10 dígitos numéricos."
		return None

	def _validar_curp(self) -> Optional[str]:
		curp = self.vars_personal["CURP"].get().strip()
		if not curp:
			return "El CURP es obligatorio."
		if len(curp) != 18:
			return "CURP inválido (debe tener 18 caracteres)."
		return None

	def _existe_por_curp(self, curp: str) -> bool:
		# Primero delegar a modules.clientes si existe
		try:
			if clientes_module and hasattr(clientes_module, "find_by_curp"):
				return bool(clientes_module.find_by_curp(curp))  # type: ignore[call-arg, misc]
		except Exception:
			LOG.exception("Error consultando modules.clientes.find_by_curp")

		# Fallback a store local
		data = _load_store()
		for c in data:
			if c.get("curp") == curp:
				# Si estamos en modo editar, permitir que sea el mismo registro
				if self.mode == "editar" and c.get("id") == self.cliente.get("id"):
					return False
				return True
		return False

	def _calcular_scoring(self) -> None:
		try:
			ingreso = float(self.vars_financiero["Ingreso Mensual"].get() or 0)
		except Exception:
			ingreso = 0.0
		try:
			presupuesto = float(self.vars_financiero["Presupuesto"].get() or 0)
		except Exception:
			presupuesto = 0.0
		try:
			credito = float(self.vars_financiero["Crédito Disponible"].get() or 0)
		except Exception:
			credito = 0.0
		tipo = self.vars_financiero["Tipo Crédito"].get()

		score = 0.0
		# 40% presupuesto vs ingreso
		if ingreso > 0:
			ratio = min(1.0, presupuesto / ingreso)
			score += ratio * 40
		# 40% crédito disponible relativo a presupuesto
		if presupuesto > 0:
			score += min(1.0, credito / presupuesto) * 40
		# 20% tipo crédito
		tipo_map = {"Hipotecario": 1.0, "Contado": 1.0, "Infonavit": 0.8, "Bancario": 0.9, "No Aplica": 0.2}
		score += tipo_map.get(tipo, 0.5) * 20

		final = int(round(score))
		self.var_scoring.set(str(max(0, min(100, final))))

	def _on_guardar(self) -> None:
		# Validaciones
		err = self._validar_curp() or self._validar_telefonos()
		if err:
			messagebox.showerror("Validación", err)
			return

		curp = self.vars_personal["CURP"].get().strip()
		if self._existe_por_curp(curp):
			if not messagebox.askyesno("Duplicado", "Ya existe un cliente con ese CURP. ¿Desea continuar? "):
				return

		# Recolectar datos
		cliente = {
			"nombre": self.vars_personal["Nombre"].get().strip(),
			"apellido_paterno": self.vars_personal["Apellido Paterno"].get().strip(),
			"apellido_materno": self.vars_personal["Apellido Materno"].get().strip(),
			"curp": curp,
			"fecha_nacimiento": self.vars_personal["Fecha Nac (YYYY-MM-DD)"].get(),
			"edad": self.vars_personal["Edad"].get(),
			"genero": self.vars_personal["Género"].get(),
			"ocupacion": self.vars_laboral["Ocupación"].get(),
			"empresa": self.vars_laboral["Empresa"].get(),
			"telefono_principal": self.vars_laboral["Teléfono Principal"].get(),
			"telefono_secundario": self.vars_laboral["Teléfono Secundario"].get(),
			"telefono_terciario": self.vars_laboral["Teléfono Terciario"].get(),
			"estado_civil": self.vars_laboral["Estado Civil"].get(),
			"ingreso_mensual": self.vars_financiero["Ingreso Mensual"].get(),
			"presupuesto": self.vars_financiero["Presupuesto"].get(),
			"credito_disponible": self.vars_financiero["Crédito Disponible"].get(),
			"tipo_credito": self.vars_financiero["Tipo Crédito"].get(),
			"nivel_educativo": self.vars_financiero["Nivel Educativo"].get(),
			"tipo_propiedad_interes": self.vars_prop_interes["Tipo Propiedad"].get(),
			"zona_interes": self.vars_prop_interes["Zona de Interés"].get(),
			"habitaciones": self.vars_prop_interes["Número de Habitaciones"].get(),
			"estado_propiedad": self.vars_prop_interes["Estado Propiedad"].get(),
			"notas": (self.txt_notas.get("1.0", tk.END).strip() if self.txt_notas else ""),
			"fuente": self.vars_otros["Fuente de Captación"].get(),
			"estado_cliente": self.vars_otros["Estado Cliente"].get(),
			"scoring": self.var_scoring.get(),
		}

		# Intentar delegar a modules.clientes.save si existe
		try:
			if clientes_module and hasattr(clientes_module, "save"):
				clientes_module.save(cliente)  # type: ignore
			else:
				data = _load_store()
				# asignar id simple
				cliente["id"] = str(max((int(c.get("id", 0)) for c in data), default=0) + 1)
				data.append(cliente)
				_save_store(data)
		except Exception:
			LOG.exception("Error guardando cliente")
			messagebox.showerror("Error", "No se pudo guardar el cliente.")
			return

		messagebox.showinfo("Éxito", "Cliente guardado correctamente.")
		self.destroy()


def main_test() -> None:
	root = tk.Tk()
	root.withdraw()
	f = ClienteForm(master=root)
	f.grab_set()
	root.mainloop()


if __name__ == "__main__":
	main_test()

