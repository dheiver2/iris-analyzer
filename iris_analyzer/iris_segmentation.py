"""Segmentacao precisa da iris e da pupila usando MediaPipe FaceLandmarker.

Retorna centro/raio da iris e da pupila em pixels, com precisao sub-pixel,
robusto a inclinacao da cabeca e iluminacao. Muito superior ao Hough Circles.
Usa a Tasks API (modelo face_landmarker.task, 478 landmarks com iris).
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    FaceLandmarker,
    FaceLandmarkerOptions,
    RunningMode,
)

from . import config
from .validation import ModeloAusenteError, validar_imagem

_MODELO = str(config.MODELO_PATH)


# Indices dos landmarks de iris no Face Mesh (refine_landmarks=True).
# Olho direito (do ponto de vista da pessoa) e esquerdo.
_IRIS_RIGHT = [469, 470, 471, 472]
_IRIS_LEFT = [474, 475, 476, 477]
# Centros aproximados de iris fornecidos pelo modelo.
_IRIS_RIGHT_CENTER = 468
_IRIS_LEFT_CENTER = 473
# Contorno da abertura do olho (palpebras) — para mascarar oclusao.
_OLHO_DIR_CONTORNO = [33, 7, 163, 144, 145, 153, 154, 155, 133,
                      173, 157, 158, 159, 160, 161, 246]
_OLHO_ESQ_CONTORNO = [263, 249, 390, 373, 374, 380, 381, 382, 362,
                      398, 384, 385, 386, 387, 388, 466]


@dataclass
class Olho:
    lado: str                       # "direito" | "esquerdo"
    centro: tuple[float, float]     # iris (x, y) sub-pixel
    raio_iris: float
    raio_pupila: float              # estimado
    pontos_iris: np.ndarray         # 4 landmarks da borda da iris
    contorno: np.ndarray | None = None  # poligono da abertura do olho (palpebras)


def _circulo_de_pontos(pts: np.ndarray) -> tuple[tuple[float, float], float]:
    """Ajuste de circulo por minimos quadrados (algebrico, Kasa).

    Mais preciso que a media simples: minimiza o erro algebrico
    (x-a)^2+(y-b)^2 = R^2 sobre os landmarks de iris. Cai para a media se
    o sistema for mal-condicionado.
    """
    x, y = pts[:, 0], pts[:, 1]
    try:
        A = np.column_stack([2 * x, 2 * y, np.ones(len(x))])
        b = x ** 2 + y ** 2
        sol, *_ = np.linalg.lstsq(A, b, rcond=None)
        a, c, d = sol
        r = float(np.sqrt(max(d + a * a + c * c, 1e-6)))
        # sanidade: centro perto da media e raio plausivel
        cm = pts.mean(axis=0)
        if np.hypot(a - cm[0], c - cm[1]) < r and r > 1.0:
            return (float(a), float(c)), r
    except np.linalg.LinAlgError:
        pass
    cm = pts.mean(axis=0)
    return (float(cm[0]), float(cm[1])), float(np.linalg.norm(pts - cm, axis=1).mean())


def criar_landmarker() -> FaceLandmarker:
    """Cria um FaceLandmarker reutilizavel (use em loop de webcam)."""
    return _criar_landmarker()


def _criar_landmarker() -> FaceLandmarker:
    if not config.MODELO_PATH.exists():
        raise ModeloAusenteError(
            f"Modelo nao encontrado: {_MODELO}. Baixe com:\n"
            f"  curl -sL -o face_landmarker.task {config.MODELO_URL}"
        )
    opts = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=_MODELO),
        running_mode=RunningMode.IMAGE,
        num_faces=1,
    )
    return FaceLandmarker.create_from_options(opts)


def segmentar_olhos(
    imagem_bgr: np.ndarray, landmarker: FaceLandmarker | None = None
) -> list[Olho]:
    """Detecta ambos os olhos e retorna a geometria de cada iris.

    Passe um ``landmarker`` reutilizavel (ver ``criar_landmarker``) para uso
    em tempo real; sem ele, um e criado/descartado a cada chamada (mais lento).
    """
    validar_imagem(imagem_bgr, "imagem_bgr")
    h, w = imagem_bgr.shape[:2]
    rgb = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    if landmarker is not None:
        res = landmarker.detect(mp_image)
    else:
        with _criar_landmarker() as own:
            res = own.detect(mp_image)

    if not res.face_landmarks:
        return []

    lm = res.face_landmarks[0]

    def px(idxs):
        return np.array([[lm[i].x * w, lm[i].y * h] for i in idxs], dtype=np.float64)

    olhos: list[Olho] = []
    for lado, idxs, cont_idx in (
        ("direito", _IRIS_RIGHT, _OLHO_DIR_CONTORNO),
        ("esquerdo", _IRIS_LEFT, _OLHO_ESQ_CONTORNO),
    ):
        pts = px(idxs)
        centro, r_iris = _circulo_de_pontos(pts)
        # Pupila tipicamente ~0.4-0.5 do raio da iris em luz ambiente.
        r_pup = max(r_iris * 0.45, 2.0)
        contorno = px(cont_idx).astype(np.int32)
        olhos.append(
            Olho(lado=lado, centro=centro, raio_iris=r_iris,
                 raio_pupila=r_pup, pontos_iris=pts, contorno=contorno)
        )
    return olhos


def detectar_face(imagem_bgr: np.ndarray, landmarker: FaceLandmarker | None = None):
    """Como segmentar_olhos, mas tambem retorna os 478 landmarks da face.

    Retorna (olhos, pontos) onde ``pontos`` e um array Nx2 (px) de todos os
    landmarks, ou None se nenhuma face for detectada. Faz UMA deteccao so
    (eficiente para o loop ao vivo).
    """
    validar_imagem(imagem_bgr, "imagem_bgr")
    h, w = imagem_bgr.shape[:2]
    rgb = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    if landmarker is not None:
        res = landmarker.detect(mp_image)
    else:
        with _criar_landmarker() as own:
            res = own.detect(mp_image)
    if not res.face_landmarks:
        return [], None

    lm = res.face_landmarks[0]
    pontos = np.array([[p.x * w, p.y * h] for p in lm], dtype=np.float64)

    def px(idxs):
        return pontos[list(idxs)]

    olhos: list[Olho] = []
    for lado, idxs, cont_idx in (
        ("direito", _IRIS_RIGHT, _OLHO_DIR_CONTORNO),
        ("esquerdo", _IRIS_LEFT, _OLHO_ESQ_CONTORNO),
    ):
        pts = px(idxs)
        centro, r_iris = _circulo_de_pontos(pts)
        r_pup = max(r_iris * 0.45, 2.0)
        contorno = px(cont_idx).astype(np.int32)
        olhos.append(Olho(lado=lado, centro=centro, raio_iris=r_iris,
                          raio_pupila=r_pup, pontos_iris=pts, contorno=contorno))
    return olhos, pontos
