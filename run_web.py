#!/usr/bin/env python3
"""Inicia o Iris Analyzer como web app e abre o navegador.

    python3 run_web.py

A camera fica no NAVEGADOR (sem permissoes de sistema/TCC). O Python so
analisa a imagem. Funciona em qualquer SO, sem empacotamento.
"""
from __future__ import annotations

import threading
import webbrowser

import uvicorn

PORTA = 8000


def _abrir():
    webbrowser.open(f"http://127.0.0.1:{PORTA}/")


if __name__ == "__main__":
    threading.Timer(1.5, _abrir).start()
    uvicorn.run("iris_analyzer.server:app", host="127.0.0.1", port=PORTA, log_level="warning")
