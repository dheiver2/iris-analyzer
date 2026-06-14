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


def desenhar_guia(frame, criterios, ok, progresso: float):
    """Desenha o contorno do rosto, marcas dos olhos, checklist e progresso."""
    h, w = frame.shape[:2]
    cx, cy = w // 2, int(h * 0.44)
    rx, ry = int(w * 0.20), int(h * 0.30)   # tamanho do rosto-alvo
    cor_alvo = (0, 220, 0) if ok else (0, 180, 255)

    # escurece fora do oval do rosto (vinheta) para guiar o olhar
    overlay = frame.copy()
    mask = overlay.copy()
    cv2.ellipse(mask, (cx, cy), (rx, ry), 0, 0, 360, (0, 0, 0), -1)
    escuro = cv2.addWeighted(frame, 0.5, frame * 0, 0.5, 0)
    fora = frame.copy()
    m = (mask.sum(axis=2) == 0)
    fora[m] = escuro[m]
    frame[:] = fora

    # contorno do rosto
    cv2.ellipse(frame, (cx, cy), (rx, ry), 0, 0, 360, cor_alvo, 3)
    cv2.putText(frame, "Encaixe seu rosto aqui", (cx - 120, cy - ry - 14),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor_alvo, 2, cv2.LINE_AA)

    # marcas onde os olhos devem ficar (linha dos olhos ~ 12% acima do centro)
    ey = cy - int(ry * 0.18)
    for ex in (cx - int(rx * 0.42), cx + int(rx * 0.42)):
        cv2.circle(frame, (ex, ey), int(w * 0.025), cor_alvo, 2)
        cv2.line(frame, (ex - 6, ey), (ex + 6, ey), cor_alvo, 1)
        cv2.line(frame, (ex, ey - 6), (ex, ey + 6), cor_alvo, 1)
    cv2.putText(frame, "olhos", (cx - 22, ey - int(w * 0.03)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, cor_alvo, 1, cv2.LINE_AA)

    # checklist (canto inferior esquerdo, p/ nao cobrir o titulo)
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

    # anel de progresso do auto-disparo
    if progresso > 0:
        ang = int(360 * min(progresso, 1.0))
        cv2.ellipse(frame, (cx, cy), (int(w * 0.20), int(h * 0.29)), -90, 0, ang,
                    (0, 230, 0), 4)
        if progresso >= 1.0:
            cv2.putText(frame, "CAPTURANDO...", (cx - 90, cy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 230, 0), 2, cv2.LINE_AA)
    return frame
