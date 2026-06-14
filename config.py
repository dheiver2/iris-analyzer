"""Configuracao central do Iris Analyzer.

Reune caminhos, limiares e parametros num unico lugar, com possibilidade de
sobrescrever por variaveis de ambiente (prefixo IRIS_).
"""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# --- Modelo MediaPipe ---
MODELO_PATH = Path(os.environ.get("IRIS_MODELO", BASE_DIR / "face_landmarker.task"))
MODELO_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)

# --- Camera / preview ---
CAMERA_INDEX = int(os.environ.get("IRIS_CAMERA", "0"))
PREVIEW_W = 640
PREVIEW_H = 480
ANALISE_INTERVALO_S = 0.12          # ~8 fps de analise no preview

# --- Qualidade de imagem ---
NITIDEZ_MIN = 40.0                  # variancia do Laplaciano
REFLEXO_MAX_PCT = 8.0

# --- Captura guiada ---
RAIO_MIN_PX = 16.0
FRAMES_ESTAVEL = 18
COOLDOWN_FRAMES = 60

# --- Mapa de zonas (iridologia) ---
N_SETORES = 12
CONTRASTE_LACUNA = 22               # niveis de cinza abaixo da vizinhanca
EDGE_BASE = 0.16
OCLUSAO_MAX = 0.55
MARCA_MIN = 0.40

# --- Daugman ---
DAUGMAN_ALTURA = 64
DAUGMAN_LARGURA = 256

__all__ = [name for name in dir() if name.isupper()]
