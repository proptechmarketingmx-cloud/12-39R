"""Punto de entrada principal para CRM Inmobiliario."""

from __future__ import annotations

if __name__ == "__main__":
    from ui.main_window import MainWindow

    win = MainWindow(user={"username": "Usuario"})
    win.run()
