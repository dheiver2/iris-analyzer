"""Avaliacao de qualidade para captura guiada da iris.

Calcula, por frame, se a foto esta boa o suficiente para analise:
tamanho da iris, foco, reflexo, centralizacao e deteccao dos dois olhos.
Tambem desenha o guia (alvo + checklist + anel de progresso) sobre o video.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

# Limiares de qualidade
RAIO_MIN = 16.0        # px — iris grande o bastante (aproxime o rosto)
NITIDEZ_MIN = 40.0
REFLEXO_MAX = 8.0
FRAMES_ESTAVEL = 18    # frames consecutivos bons p/ auto-disparo


@dataclass
class Criterio:
    nome: str
    ok: bool
    dica: str = ""


def avaliar(frame, olhos, feats) -> tuple[list[Criterio], bool]:
    h, w = frame.shape[:2]
    crit: list[Criterio] = []

    dois = len(olhos) == 2
    crit.append(Criterio("Dois olhos visiveis", dois, "Encare a camera"))

    raio = min((o.raio_iris for o in olhos), default=0.0)
    crit.append(Criterio("Distancia", raio >= RAIO_MIN,
                         "Aproxime o rosto" if raio < RAIO_MIN else ""))

    nit = min((f.nitidez for f in feats), default=0.0)
    crit.append(Criterio("Foco nitido", nit >= NITIDEZ_MIN,
                         "Segure firme / aproxime"))

    refl = max((f.reflexo_pct for f in feats), default=100.0)
    crit.append(Criterio("Sem reflexo", refl <= REFLEXO_MAX,
                         "Evite luz direta/flash"))

    # Angulo (off-angle): iris frontal e ~circular; de lado vira elipse.
    ang_ok = True
    for o in olhos:
        pts = getattr(o, "pontos_iris", None)
        if pts is not None and len(pts) >= 4:
            ex = float(pts[:, 0].max() - pts[:, 0].min())
            ey = float(pts[:, 1].max() - pts[:, 1].min())
            if max(ex, ey) > 1e-6 and min(ex, ey) / max(ex, ey) < 0.72:
                ang_ok = False
    crit.append(Criterio("Olhe de frente", ang_ok and len(olhos) > 0,
                         "Encare a camera de frente"))

    centralizado = False
    if olhos:
        cx = np.mean([o.centro[0] for o in olhos]) / w
        cy = np.mean([o.centro[1] for o in olhos]) / h
        centralizado = 0.30 <= cx <= 0.70 and 0.22 <= cy <= 0.72
    crit.append(Criterio("Centralizado", centralizado, "Centralize o rosto"))

    ok = all(c.ok for c in crit)
    return crit, ok


def desenhar_malha(frame, pontos, cor=(80, 200, 120)):
    """Desenha a malha facial (face mesh) por triangulacao de Delaunay dos
    478 landmarks do MediaPipe. ``pontos`` e um array Nx2 (px)."""
    if pontos is None or len(pontos) < 3:
        return frame
    h, w = frame.shape[:2]
    subdiv = cv2.Subdiv2D((0, 0, w, h))
    idx_de = {}
    for i, (x, y) in enumerate(pontos):
        if 0 <= x < w and 0 <= y < h:
            subdiv.insert((float(x), float(y)))
            idx_de[(round(float(x), 1), round(float(y), 1))] = i
    for t in subdiv.getTriangleList():
        p = [(t[0], t[1]), (t[2], t[3]), (t[4], t[5])]
        if all(0 <= px < w and 0 <= py < h for px, py in p):
            ip = [(int(px), int(py)) for px, py in p]
            cv2.line(frame, ip[0], ip[1], cor, 1, cv2.LINE_AA)
            cv2.line(frame, ip[1], ip[2], cor, 1, cv2.LINE_AA)
            cv2.line(frame, ip[2], ip[0], cor, 1, cv2.LINE_AA)
    return frame


def desenhar_guia(frame, criterios, ok, progresso: float):
    """Desenha apenas o checklist de qualidade e o progresso do auto-disparo
    (sem guia de posicionamento do rosto)."""
    h, w = frame.shape[:2]

    # checklist (canto inferior esquerdo)
    n = len(criterios)
    base_y = h - 24 * n - 14
    cv2.rectangle(frame, (8, base_y - 18), (300, h - 8), (0, 0, 0), -1)
    y = base_y
    for c in criterios:
        cor = (0, 230, 0) if c.ok else (0, 165, 255)
        marca = "OK" if c.ok else "X"
        txt = c.nome if c.ok else f"{c.nome}: {c.dica}"
        cv2.putText(frame, f"[{marca}] {txt}", (14, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, cor, 1, cv2.LINE_AA)
        y += 24

    # barra de progresso do auto-disparo (topo)
    if progresso > 0:
        bw = int(w * min(progresso, 1.0))
        cv2.rectangle(frame, (0, 0), (bw, 6), (0, 230, 0), -1)
        if progresso >= 1.0:
            cv2.putText(frame, "CAPTURANDO...", (w // 2 - 90, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 230, 0), 2, cv2.LINE_AA)
    return frame
