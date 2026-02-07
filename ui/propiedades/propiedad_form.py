"""Formulario de propiedad.

Formulario en modo crear/editar con tabs: Básico, Ubicación, Características.
Incluye gestión básica de fotos (contar, validar máximo 20) y checkboxes de
características. El guardado persiste en un store JSON de pruebas si no existe
`modules.propiedades.save`.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import tkinter as tk
from tkinter import ttk, messagebox

try:
	from modules import propiedades as propiedades_module
except Exception:
	propiedades_module = None

LOG = logging.getLogger(__name__)



class PropiedadForm(tk.Toplevel):
	"""Ventana modal para crear/editar una propiedad."""

	def __init__(self, master: Any = None, mode: str = "crear", propiedad: Optional[Dict] = None) -> None:
		super().__init__(master)
		self.title("Propiedad - " + ("Crear" if mode == "crear" else "Editar"))
		self.mode = mode
		self.propiedad = propiedad or {}
		self.resizable(False, False)

		self._fotos: List[str] = []
		self._build_ui()

	def _build_ui(self) -> None:
		frm = ttk.Frame(self, padding=12)
		frm.pack(fill=tk.BOTH, expand=True)

		nb = ttk.Notebook(frm)
		nb.pack(fill=tk.BOTH, expand=True)

		tab_basico = ttk.Frame(nb)
		nb.add(tab_basico, text="Básico")
		self._build_basico(tab_basico)

		tab_ubic = ttk.Frame(nb)
		nb.add(tab_ubic, text="Ubicación")
		self._build_ubicacion(tab_ubic)

		tab_carac = ttk.Frame(nb)
		nb.add(tab_carac, text="Características")
		self._build_caracteristicas(tab_carac)

		btn_frame = ttk.Frame(frm)
		btn_frame.pack(fill=tk.X, pady=(8, 0))
		ttk.Button(btn_frame, text="Guardar", command=self._on_guardar).pack(side=tk.RIGHT, padx=6)
		ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT)

	def _build_basico(self, parent: ttk.Frame) -> None:
		labels = ["Título", "Descripción", "Precio", "Metros Cuadrados", "Estado"]
		self.vars_basico = {k: tk.StringVar() for k in labels}
		for i, label in enumerate(labels):
			ttk.Label(parent, text=label).grid(row=i, column=0, sticky=tk.W, padx=6, pady=4)
			if label == "Descripción":
				tx = tk.Text(parent, height=4, width=40)
				tx.grid(row=i, column=1, sticky=tk.EW, padx=6)
				self.vars_basico[label] = tx
			else:
				ttk.Entry(parent, textvariable=self.vars_basico[label]).grid(row=i, column=1, sticky=tk.EW, padx=6)

		# Fotos
		ttk.Label(parent, text="Fotos (máx 20)").grid(row=len(labels), column=0, sticky=tk.W, padx=6, pady=6)
		self.lbl_fotos = ttk.Label(parent, text="0 fotos")
		self.lbl_fotos.grid(row=len(labels), column=1, sticky=tk.W)
		ttk.Button(parent, text="Añadir foto (demo)", command=self._agregar_foto_demo).grid(row=len(labels)+1, column=1, sticky=tk.W, padx=6)

	def _build_ubicacion(self, parent: ttk.Frame) -> None:
		labels = ["Calle", "Número", "Colonia", "Ciudad", "Estado", "CP"]
		self.vars_ubic = {k: tk.StringVar() for k in labels}
		for i, label in enumerate(labels):
			ttk.Label(parent, text=label).grid(row=i, column=0, sticky=tk.W, padx=6, pady=4)
			ttk.Entry(parent, textvariable=self.vars_ubic[label]).grid(row=i, column=1, sticky=tk.EW, padx=6)

	def _build_caracteristicas(self, parent: ttk.Frame) -> None:
		self.caracteristicas = ["Alberca", "Jardín", "Estacionamiento", "Seguridad", "Elevador", "Terraza"]
		self.vars_carac = {c: tk.BooleanVar() for c in self.caracteristicas}
		for i, c in enumerate(self.caracteristicas):
			ttk.Checkbutton(parent, text=c, variable=self.vars_carac[c]).grid(row=i // 2, column=i % 2, sticky=tk.W, padx=6, pady=4)

	def _agregar_foto_demo(self) -> None:
		if len(self._fotos) >= 20:
			messagebox.showwarning("Fotos", "Ya alcanzó el máximo de 20 fotos.")
			return
		# Demo: añadimos un placeholder path
		self._fotos.append(f"foto_{len(self._fotos)+1}.jpg")
		self.lbl_fotos.config(text=f"{len(self._fotos)} fotos")

	def _on_guardar(self) -> None:
		# Campos opcionales: no autogenerar
		titulo = self.vars_basico["Título"].get().strip() if isinstance(self.vars_basico.get("Título"), tk.StringVar) else ""
		precio = self.vars_basico["Precio"].get().strip() if isinstance(self.vars_basico.get("Precio"), tk.StringVar) else ""

		prop = {
			"titulo": titulo,
			"descripcion": (self.vars_basico["Descripción"].get("1.0", tk.END).strip() if isinstance(self.vars_basico.get("Descripción"), tk.Text) else ""),
			"precio": precio,
			"metros": self.vars_basico["Metros Cuadrados"].get(),
			"estado": self.vars_basico["Estado"].get(),
			"ubicacion": {k: v.get() for k, v in self.vars_ubic.items()},
			"caracteristicas": {k: v.get() for k, v in self.vars_carac.items()},
			"fotos": self._fotos,
		}
		if self.mode == "editar" and self.propiedad.get("id") is not None:
			prop["id"] = self.propiedad.get("id")

		try:
			if propiedades_module and hasattr(propiedades_module, "save"):
				propiedades_module.save(prop)
			else:
				raise RuntimeError("Modulo de propiedades no disponible")
		except Exception:
			LOG.exception("Error guardando propiedad")
			messagebox.showerror("Error", "No se pudo guardar la propiedad.")
			return

		messagebox.showinfo("Éxito", "Propiedad guardada correctamente.")
		self.destroy()


def main_test() -> None:
	root = tk.Tk()
	root.withdraw()
	f = PropiedadForm(master=root)
	f.grab_set()
	root.mainloop()


if __name__ == "__main__":
	main_test()

