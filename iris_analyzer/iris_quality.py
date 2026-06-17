"""Avaliacao de qualidade da imagem da iris por multiplos fatores.

Baseado na literatura de qualidade de imagem para reconhecimento de iris, que
identifica como fatores mais relevantes: desfoco (defocus), oclusao por
palpebra/cilio, reflexo especular, angulo (off-angle), dilatacao pupilar e
contagem de pixels (tamanho). Referencias:
  - Daugman, "How Iris Recognition Works" (2004) — foco por alta frequencia.
  - Kalka et al., "Estimating and Fusing Quality Factors for Iris Biometric
    Images" (fusao de fatores de qualidade).
  - Wei et al., quality metrics (defocus/occlusion/specular).
Cada fator e estimado de forma objetiva e fundido num score 0-100.

NB: melhora a PRECISAO da imagem; nao torna a iridologia validada.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class Qualidade:
    foco: float          # 0-1 (1 = nitido)
    oclusao: float       # 0-1 (0 = sem oclusao)
    reflexo: float       # 0-1 (0 = sem reflexo)
    angulo: float        # 0-1 (1 = frontal)
    dilatacao: float     # 0-1 (1 = ideal ~0.4)
    tamanho: float       # 0-1 (1 = iris grande o bastante)
    abertura: float      # 0-1 (1 = olho bem aberto; baixo = semicerrado)
    score: float         # 0-100 (fusao ponderada)
    nivel: str           # "ruim" | "regular" | "boa" | "excelente"


def _abertura_olho(contorno) -> float:
    """Eye Aspect Ratio simplificado: altura/largura do contorno do olho.
    Olho bem aberto ~0.30-0.50; semicerrado/piscando < 0.15."""
    if contorno is None or len(contorno) < 4:
        return 1.0
    pts = np.asarray(contorno, dtype=np.float64)
    larg = pts[:, 0].max() - pts[:, 0].min()
    alt = pts[:, 1].max() - pts[:, 1].min()
    if larg <= 1e-6:
        return 1.0
    ear = alt / larg
    return float(np.clip(ear / 0.32, 0.0, 1.0))


def _foco_alta_frequencia(gray_roi: np.ndarray) -> float:
    """Razao de energia de alta frequencia (FFT). Robusto a desfoco/movimento."""
    if gray_roi.size < 64:
        return 0.0
    g = gray_roi.astype(np.float32)
    f = np.fft.fftshift(np.fft.fft2(g))
    mag = np.abs(f)
    h, w = mag.shape
    cy, cx = h // 2, w // 2
    yy, xx = np.ogrid[:h, :w]
    raio = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    alta = raio > 0.25 * min(h, w)        # banda de alta frequencia
    total = mag.sum() + 1e-9
    razao = mag[alta].sum() / total
    # mapeia para 0-1 (calibrado empiricamente; >0.45 ~ nitido)
    return float(np.clip(razao / 0.45, 0.0, 1.0))


def _roi_iris(img, centro, r_iris):
    cx, cy = int(round(centro[0])), int(round(centro[1]))
    r = int(round(r_iris))
    h, w = img.shape[:2]
    x0, y0 = max(0, cx - r), max(0, cy - r)
    x1, y1 = min(w, cx + r), min(h, cy + r)
    return img[y0:y1, x0:x1], (x0, y0)


def _mascara_anel(shape, centro, off, r_iris, r_pupila):
    m = np.zeros(shape[:2], np.uint8)
    c = (int(round(centro[0])) - off[0], int(round(centro[1])) - off[1])
    cv2.circle(m, c, int(round(r_iris)), 255, -1)
    cv2.circle(m, c, int(round(r_pupila)), 0, -1)
    return m


def _nivel(score: float) -> str:
    if score < 40:
        return "ruim"
    if score < 60:
        return "regular"
    if score < 80:
        return "boa"
    return "excelente"


def avaliar_qualidade(img, olho, r_pupila, raio_min=16.0) -> Qualidade:
    """Calcula os fatores de qualidade e o score 0-100 para um olho."""
    centro, r_iris = olho.centro, olho.raio_iris
    roi, off = _roi_iris(img, centro, r_iris)
    if roi.size == 0:
        return Qualidade(0, 1, 1, 0, 0, 0, 0.0, "ruim")
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    mask = _mascara_anel(roi.shape, centro, off, r_iris, r_pupila)

    # --- Foco (alta frequencia) ---
    foco = _foco_alta_frequencia(gray)

    # --- Reflexo especular (adaptativo) ---
    if mask.any():
        p99 = np.percentile(gray[mask > 0], 99)
        limiar = float(np.clip(p99, 210, 250))
        refl_pix = int(((gray > limiar) & (mask > 0)).sum())
        reflexo = refl_pix / max(int((mask > 0).sum()), 1)
    else:
        reflexo = 1.0

    # --- Oclusao (palpebra/cilio via contorno do olho) ---
    oclusao = 0.0
    if olho.contorno is not None:
        olho_mask = np.zeros(img.shape[:2], np.uint8)
        cv2.fillPoly(olho_mask, [olho.contorno.astype(np.int32)], 255)
        anel = np.zeros(img.shape[:2], np.uint8)
        c = (int(round(centro[0])), int(round(centro[1])))
        cv2.circle(anel, c, int(round(r_iris)), 255, -1)
        cv2.circle(anel, c, int(round(r_pupila)), 0, -1)
        total = int((anel > 0).sum())
        visivel = int(((anel > 0) & (olho_mask > 0)).sum())
        oclusao = 1.0 - (visivel / total if total else 0.0)

    # --- Angulo (off-angle): circulo visto de lado vira elipse ---
    pts = olho.pontos_iris
    ext_x = float(pts[:, 0].max() - pts[:, 0].min())
    ext_y = float(pts[:, 1].max() - pts[:, 1].min())
    angulo = (min(ext_x, ext_y) / max(ext_x, ext_y)) if max(ext_x, ext_y) > 1e-6 else 0.0

    # --- Dilatacao pupilar (ideal ~0.4; penaliza extremos) ---
    ratio = r_pupila / r_iris if r_iris > 0 else 0.0
    dilatacao = float(np.clip(1.0 - abs(ratio - 0.4) / 0.4, 0.0, 1.0))

    # --- Tamanho (contagem de pixels) ---
    tamanho = float(np.clip(r_iris / (raio_min * 2.5), 0.0, 1.0))

    # --- Abertura do olho (EAR) ---
    abertura = _abertura_olho(olho.contorno)

    # --- Fusao ponderada -> 0-100 ---
    score = 100.0 * (
        0.28 * foco +
        0.18 * (1.0 - oclusao) +
        0.14 * (1.0 - min(reflexo / 0.08, 1.0)) +
        0.14 * angulo +
        0.08 * dilatacao +
        0.08 * tamanho +
        0.10 * abertura
    )
    score = float(np.clip(score, 0, 100))
    return Qualidade(
        foco=round(foco, 3), oclusao=round(oclusao, 3), reflexo=round(reflexo, 4),
        angulo=round(angulo, 3), dilatacao=round(dilatacao, 3),
        tamanho=round(tamanho, 3), abertura=round(abertura, 3),
        score=round(score, 1), nivel=_nivel(score),
    )
