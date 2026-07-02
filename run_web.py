#!/usr/bin/env python3
"""Inicia o Iris Analyzer como web app e abre o navegador.

    python3 run_web.py

A camera fica no NAVEGADOR (sem permissoes de sistema/TCC). O Python so
analisa a imagem. Funciona em qualquer SO, sem empacotamento.

Configuravel por variaveis de ambiente (ver iris_analyzer/config.py):
IRIS_WEB_HOST, IRIS_WEB_PORT, IRIS_MAX_UPLOAD_MB, IRIS_CORS_ORIGINS.
"""
from __future__ import annotations

import logging
import threading
import webbrowser

import uvicorn

from iris_analyzer import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def _abrir():
    webbrowser.open(f"http://{config.WEB_HOST}:{config.WEB_PORT}/")


if __name__ == "__main__":
    if config.WEB_HOST in ("127.0.0.1", "localhost"):
        threading.Timer(1.5, _abrir).start()
    uvicorn.run("iris_analyzer.server:app", host=config.WEB_HOST, port=config.WEB_PORT,
                log_level="warning")
