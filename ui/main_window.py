"""Ventana principal demo para el CRM Inmobiliario.

Archivo minimo para pruebas de integracion con `ui/login_window.LoginWindow`.
Muestra un encabezado con el usuario autenticado y un boton para cerrar sesion.
"""
from __future__ import annotations

import logging
import sys
from typing import Optional, Dict, Any
import tkinter as tk
from tkinter import ttk

try:
    from database import db as _db
except Exception:
    _db = None  # type: ignore

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
    from ui.clientes.cliente_lista import ClienteLista
except Exception:
    ClienteLista = None

try:
    from ui.propiedades.propiedad_form import PropiedadForm
except Exception:
    PropiedadForm = None

try:
    from ui.propiedades.propiedad_lista import PropiedadLista
except Exception:
    PropiedadLista = None

try:
    from ui.asesores.asesor_form import AsesorForm
except Exception:
    AsesorForm = None

try:
    from ui.asesores.asesor_lista import AsesorLista
except Exception:
    AsesorLista = None


class MainWindow:
    """Ventana principal minima.

    Parametros:
    - `user`: diccionario publico con al menos la clave `username`.
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

        header = ttk.Label(self.frame, text=f"Bienvenido, {self.user.get('username')}")
        header.config(font=("Segoe UI", 16, "bold"), foreground=PRIMARY_COLOR)
        header.pack(anchor=tk.W)

        # Panel principal con accesos directos
        content = ttk.Frame(self.frame)
        content.pack(fill=tk.BOTH, expand=True, pady=20)

        ttk.Label(content, text="Accesos rápidos").pack(anchor=tk.W, pady=(0, 8))

        grid = ttk.Frame(content)
        grid.pack(fill=tk.BOTH, expand=True)

        btns = [
            ("Formularios", self._open_formularios),
            ("Clientes", self._open_clientes_lista),
            ("Propiedades", self._open_propiedades_lista),
            ("Asesores", self._open_asesores_lista),
            ("Estadisticas", self._open_estadisticas),
            ("Mapa de Calor", self._open_mapa_calor),
        ]

        cols = 2
        for i, (label, cmd) in enumerate(btns):
            r = i // cols
            c = i % cols
            b = ttk.Button(grid, text=label, command=cmd)
            b.grid(row=r, column=c, sticky=tk.EW, padx=8, pady=6)

        for c in range(cols):
            grid.columnconfigure(c, weight=1)

        # Boton logout
        btn_logout = ttk.Button(self.frame, text="Cerrar sesion", command=self._on_logout)
        btn_logout.pack(side=tk.BOTTOM, anchor=tk.E)

    def _open_formularios(self) -> None:
        try:
            win = tk.Toplevel(self.root)
            win.title("Formularios")
            win.geometry("520x360")
            frame = ttk.Frame(win, padding=16)
            frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(frame, text="Formularios").pack(anchor=tk.W, pady=(0, 8))

            ttk.Button(frame, text="Formulario de Clientes", command=self._open_clientes_form).pack(fill=tk.X, pady=4)
            ttk.Button(frame, text="Formulario de Propiedades", command=self._open_propiedades_form).pack(fill=tk.X, pady=4)
            ttk.Button(frame, text="Formulario de Asesores", command=self._open_asesores_form).pack(fill=tk.X, pady=4)
        except Exception:
            LOG.exception("Error abriendo ventana de formularios")

    def _on_change_password(self) -> None:
        username = self.user.get("username") or "Usuario"
        if ChangePasswordDialog is None:
            message = "El dialogo de cambio de contrasena no esta disponible."
            LOG.warning(message)
            try:
                from tkinter import messagebox

                messagebox.showwarning("Advertencia", message)
            except Exception:
                pass
            return
        dlg = ChangePasswordDialog(self.frame, username)
        dlg.show()

    def _open_clientes_form(self) -> None:
        if ClienteForm is None:
            LOG.warning("ClienteForm no disponible")
            try:
                from tkinter import messagebox

                messagebox.showinfo("No implementado", "El formulario de Clientes no esta disponible.")
            except Exception:
                pass
            return
        # Abrir formulario como modal
        try:
            f = ClienteForm(master=self.root)
            f.grab_set()
        except Exception:
            LOG.exception("Error abriendo ClienteForm")

    def _open_clientes_lista(self) -> None:
        if ClienteLista is None:
            LOG.warning("ClienteLista no disponible")
            try:
                from tkinter import messagebox

                messagebox.showinfo("No implementado", "La lista de Clientes no esta disponible.")
            except Exception:
                pass
            return
        try:
            win = tk.Toplevel(self.root)
            win.title("Clientes")
            win.geometry("1000x600")
            view = ClienteLista(win)
            view.pack(fill=tk.BOTH, expand=True)
        except Exception:
            LOG.exception("Error abriendo ClienteLista")

    def _open_propiedades_form(self) -> None:
        if PropiedadForm is None:
            LOG.warning("PropiedadForm no disponible")
            try:
                from tkinter import messagebox

                messagebox.showinfo("No implementado", "El formulario de Propiedades no esta disponible.")
            except Exception:
                pass
            return
        try:
            f = PropiedadForm(master=self.root)
            f.grab_set()
        except Exception:
            LOG.exception("Error abriendo PropiedadForm")

    def _open_propiedades_lista(self) -> None:
        if PropiedadLista is None:
            LOG.warning("PropiedadLista no disponible")
            try:
                from tkinter import messagebox

                messagebox.showinfo("No implementado", "La lista de Propiedades no esta disponible.")
            except Exception:
                pass
            return
        try:
            win = tk.Toplevel(self.root)
            win.title("Propiedades")
            win.geometry("1000x600")
            view = PropiedadLista(win)
            view.pack(fill=tk.BOTH, expand=True)
        except Exception:
            LOG.exception("Error abriendo PropiedadLista")

    def _open_asesores_form(self) -> None:
        if AsesorForm is None:
            LOG.warning("AsesorForm no disponible")
            try:
                from tkinter import messagebox

                messagebox.showinfo("No implementado", "El formulario de Asesores no esta disponible.")
            except Exception:
                pass
            return
        try:
            f = AsesorForm(master=self.root, mode="crear")
            f.grab_set()
        except Exception:
            LOG.exception("Error abriendo AsesorForm")

    def _open_asesores_lista(self) -> None:
        if AsesorLista is None:
            LOG.warning("AsesorLista no disponible")
            try:
                from tkinter import messagebox

                messagebox.showinfo("No implementado", "La lista de Asesores no esta disponible.")
            except Exception:
                pass
            return
        try:
            win = tk.Toplevel(self.root)
            win.title("Asesores")
            win.geometry("1000x600")
            view = AsesorLista(win)
            view.pack(fill=tk.BOTH, expand=True)
        except Exception:
            LOG.exception("Error abriendo AsesorLista")

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

    def _open_estadisticas(self) -> None:
        try:
            win = tk.Toplevel(self.root)
            win.title("Estadisticas")
            win.geometry("760x520")

            root_frame = ttk.Frame(win, padding=12)
            root_frame.pack(fill=tk.BOTH, expand=True)

            sidebar = ttk.Frame(root_frame)
            sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

            content = ttk.Frame(root_frame)
            content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

            current_view = {"name": "clientes"}

            def _switch(view_name: str) -> None:
                current_view["name"] = view_name
                for w in content.winfo_children():
                    w.destroy()
                _build_view(content, view_name)

            ttk.Label(sidebar, text="Secciones").pack(anchor=tk.W, pady=(0, 8))
            ttk.Button(sidebar, text="Clientes", command=lambda: _switch("clientes")).pack(fill=tk.X, pady=4)
            ttk.Button(sidebar, text="Propiedades", command=lambda: _switch("propiedades")).pack(fill=tk.X, pady=4)
            ttk.Button(sidebar, text="Asesores", command=lambda: _switch("asesores")).pack(fill=tk.X, pady=4)

            def _draw_bars(canvas: tk.Canvas, labels: list[str], values: list[int]) -> None:
                canvas.delete("all")
                w = int(canvas.winfo_width() or 520)
                h = int(canvas.winfo_height() or 220)
                padding = 30
                max_val = max(values) if values else 1
                bar_w = max(30, int((w - padding * 2) / max(1, len(values))))
                for i, (lbl, val) in enumerate(zip(labels, values)):
                    x0 = padding + i * bar_w + 10
                    x1 = x0 + bar_w - 20
                    bar_h = int((h - padding * 2) * (val / max_val)) if max_val else 0
                    y1 = h - padding
                    y0 = y1 - bar_h
                    canvas.create_rectangle(x0, y0, x1, y1, fill="#2196F3", outline="")
                    canvas.create_text((x0 + x1) / 2, y1 + 12, text=lbl, anchor=tk.N)
                    canvas.create_text((x0 + x1) / 2, y0 - 6, text=str(val), anchor=tk.S)

            def _build_view(parent: ttk.Frame, view_name: str) -> None:
                header = ttk.Frame(parent)
                header.pack(fill=tk.X, pady=(0, 8))
                ttk.Label(header, text=f"Estadisticas - {view_name.title()}").pack(side=tk.LEFT)

                filters = ttk.Frame(parent)
                filters.pack(fill=tk.X, pady=(0, 8))
                ttk.Label(filters, text="Filtro:").pack(side=tk.LEFT)
                var_estado = tk.StringVar(value="Todos")
                cb = ttk.Combobox(filters, textvariable=var_estado, state="readonly", width=14)
                cb["values"] = ["Todos", "Activos", "Inactivos"]
                cb.pack(side=tk.LEFT, padx=6)

                chart = tk.Canvas(parent, height=220)
                chart.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

                histo = tk.Canvas(parent, height=180)
                histo.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

                kpis = ttk.Frame(parent)
                kpis.pack(fill=tk.X)

                kpi_vars: Dict[str, tk.StringVar] = {
                    "total": tk.StringVar(value="..."),
                    "activos": tk.StringVar(value="..."),
                    "inactivos": tk.StringVar(value="..."),
                    "precio_min": tk.StringVar(value="-"),
                    "precio_max": tk.StringVar(value="-"),
                    "precio_avg": tk.StringVar(value="-"),
                }

                ttk.Label(kpis, text="Total:").grid(row=0, column=0, sticky=tk.W, padx=4, pady=2)
                ttk.Label(kpis, textvariable=kpi_vars["total"]).grid(row=0, column=1, sticky=tk.W, padx=4, pady=2)
                ttk.Label(kpis, text="Activos:").grid(row=1, column=0, sticky=tk.W, padx=4, pady=2)
                ttk.Label(kpis, textvariable=kpi_vars["activos"]).grid(row=1, column=1, sticky=tk.W, padx=4, pady=2)
                ttk.Label(kpis, text="Inactivos:").grid(row=2, column=0, sticky=tk.W, padx=4, pady=2)
                ttk.Label(kpis, textvariable=kpi_vars["inactivos"]).grid(row=2, column=1, sticky=tk.W, padx=4, pady=2)

                ttk.Label(kpis, text="Precio minimo:").grid(row=3, column=0, sticky=tk.W, padx=4, pady=2)
                ttk.Label(kpis, textvariable=kpi_vars["precio_min"]).grid(row=3, column=1, sticky=tk.W, padx=4, pady=2)
                ttk.Label(kpis, text="Precio maximo:").grid(row=4, column=0, sticky=tk.W, padx=4, pady=2)
                ttk.Label(kpis, textvariable=kpi_vars["precio_max"]).grid(row=4, column=1, sticky=tk.W, padx=4, pady=2)
                ttk.Label(kpis, text="Precio promedio:").grid(row=5, column=0, sticky=tk.W, padx=4, pady=2)
                ttk.Label(kpis, textvariable=kpi_vars["precio_avg"]).grid(row=5, column=1, sticky=tk.W, padx=4, pady=2)

                def _draw_histogram(canvas: tk.Canvas, values: list[float], bins: int = 6) -> None:
                    canvas.delete("all")
                    if not values:
                        return
                    w = int(canvas.winfo_width() or 520)
                    h = int(canvas.winfo_height() or 180)
                    padding = 30
                    vmin = min(values)
                    vmax = max(values)
                    if vmin == vmax:
                        counts = [len(values)]
                        edges = [vmin, vmax]
                    else:
                        step = (vmax - vmin) / bins
                        edges = [vmin + i * step for i in range(bins + 1)]
                        counts = [0 for _ in range(bins)]
                        for v in values:
                            idx = int((v - vmin) / step)
                            if idx == bins:
                                idx -= 1
                            counts[idx] += 1
                    max_count = max(counts) if counts else 1
                    bar_w = max(20, int((w - padding * 2) / max(1, len(counts))))
                    for i, c in enumerate(counts):
                        x0 = padding + i * bar_w + 6
                        x1 = x0 + bar_w - 12
                        bar_h = int((h - padding * 2) * (c / max_count)) if max_count else 0
                        y1 = h - padding
                        y0 = y1 - bar_h
                        canvas.create_rectangle(x0, y0, x1, y1, fill="#4CAF50", outline="")
                        label = f"{int(edges[i]):,}"
                        canvas.create_text((x0 + x1) / 2, y1 + 12, text=label, anchor=tk.N)
                        canvas.create_text((x0 + x1) / 2, y0 - 6, text=str(c), anchor=tk.S)

                def _refresh() -> None:
                    if _db is None:
                        for k in kpi_vars:
                            kpi_vars[k].set("N/A")
                        return
                    conn = None
                    cur = None
                    try:
                        conn = _db.get_connection()
                        cur = conn.cursor()
                        if view_name == "clientes":
                            total = self._fetch_scalar(cur, "SELECT COUNT(*) FROM clientes")
                            activos = self._fetch_scalar(cur, "SELECT COUNT(*) FROM clientes WHERE activo=1")
                            precio_min = precio_max = precio_avg = "-"
                            precios: list[float] = []
                        elif view_name == "propiedades":
                            total = self._fetch_scalar(cur, "SELECT COUNT(*) FROM propiedades")
                            activos = self._fetch_scalar(cur, "SELECT COUNT(*) FROM propiedades WHERE activo=1")
                            precio_min = self._fetch_scalar(cur, "SELECT MIN(precio) FROM propiedades")
                            precio_max = self._fetch_scalar(cur, "SELECT MAX(precio) FROM propiedades")
                            precio_avg = self._fetch_scalar(cur, "SELECT AVG(precio) FROM propiedades")
                            cur.execute("SELECT precio FROM propiedades")
                            precios = [float(r[0]) for r in (cur.fetchall() or []) if r and r[0] is not None]
                        else:
                            total = self._fetch_scalar(cur, "SELECT COUNT(*) FROM asesores")
                            activos = self._fetch_scalar(cur, "SELECT COUNT(*) FROM asesores WHERE activo=1")
                            precio_min = precio_max = precio_avg = "-"
                            precios = []
                        inactivos = max(0, int(total) - int(activos))

                        kpi_vars["total"].set(str(total))
                        kpi_vars["activos"].set(str(activos))
                        kpi_vars["inactivos"].set(str(inactivos))
                        kpi_vars["precio_min"].set(str(precio_min if precio_min is not None else "-"))
                        kpi_vars["precio_max"].set(str(precio_max if precio_max is not None else "-"))
                        kpi_vars["precio_avg"].set(str(round(float(precio_avg), 2)) if isinstance(precio_avg, (int, float)) else "-")

                        labels = ["Activos", "Inactivos"]
                        values = [int(activos), int(inactivos)]

                        estado = var_estado.get()
                        if estado == "Activos":
                            labels = ["Activos"]
                            values = [int(activos)]
                        elif estado == "Inactivos":
                            labels = ["Inactivos"]
                            values = [int(inactivos)]

                        _draw_bars(chart, labels, values)
                        _draw_histogram(histo, precios)
                    except Exception:
                        LOG.exception("Error obteniendo estadisticas")
                        for k in kpi_vars:
                            kpi_vars[k].set("N/A")
                    finally:
                        try:
                            if cur is not None:
                                cur.close()
                            if conn is not None:
                                conn.close()
                        except Exception:
                            pass

                ttk.Button(filters, text="Actualizar", command=_refresh).pack(side=tk.RIGHT)
                cb.bind("<<ComboboxSelected>>", lambda e: _refresh())
                chart.bind("<Configure>", lambda e: _refresh())
                histo.bind("<Configure>", lambda e: _refresh())
                _refresh()

            _build_view(content, "clientes")
        except Exception:
            LOG.exception("Error abriendo panel de estadisticas")

    def _fetch_scalar(self, cursor, query: str) -> Any:
        cursor.execute(query)
        row = cursor.fetchone()
        if not row:
            return 0
        return row[0]

    def _refresh_estadisticas(self) -> None:
        if not hasattr(self, "_stats_vars"):
            return
        if _db is None:
            for k in self._stats_vars:
                self._stats_vars[k].set("N/A")
            return
        conn = None
        cur = None
        try:
            conn = _db.get_connection()
            cur = conn.cursor()
            self._stats_vars["clientes_total"].set(str(self._fetch_scalar(cur, "SELECT COUNT(*) FROM clientes")))
            self._stats_vars["clientes_activos"].set(str(self._fetch_scalar(cur, "SELECT COUNT(*) FROM clientes WHERE activo=1")))
            self._stats_vars["propiedades_total"].set(str(self._fetch_scalar(cur, "SELECT COUNT(*) FROM propiedades")))
            self._stats_vars["propiedades_activas"].set(str(self._fetch_scalar(cur, "SELECT COUNT(*) FROM propiedades WHERE activo=1")))
            self._stats_vars["asesores_total"].set(str(self._fetch_scalar(cur, "SELECT COUNT(*) FROM asesores")))
            self._stats_vars["asesores_activos"].set(str(self._fetch_scalar(cur, "SELECT COUNT(*) FROM asesores WHERE activo=1")))
        except Exception:
            LOG.exception("Error obteniendo estadisticas")
            for k in self._stats_vars:
                self._stats_vars[k].set("N/A")
        finally:
            try:
                if cur is not None:
                    cur.close()
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def _open_mapa_calor(self) -> None:
        try:
            from tkinter import messagebox

            messagebox.showinfo("Mapa de calor", "Mapa de calor pendiente de implementar.")
        except Exception:
            pass

    def run(self) -> None:
        """Inicia el mainloop de la ventana principal."""
        self.root.mainloop()


def main() -> None:
    win = MainWindow(user={"username": "demo"})
    win.run()


if __name__ == "__main__":
    main()
