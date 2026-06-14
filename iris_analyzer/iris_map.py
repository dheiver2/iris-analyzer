"""Mapa topografico (setorizado) da iris no estilo iridologia.

Divide a iris em 12 setores ("horas do relogio"). Em cada setor mede, de forma
ABSOLUTA (nao relativa ao proprio olho), a presenca de marcas reais:
  - lacunas / manchas escuras (pixels nitidamente mais escuros que a iris)
  - rupturas na trama de fibras (densidade de bordas acima do normal)
Setores cobertos por palpebra/cilio sao marcados como "nao avaliavel" (cinza),
em vez de gerar falso-positivo. Reflexos especulares sao removidos antes.

AVISO: o mapa zona->orgao da iridologia NAO tem comprovacao cientifica. E
referencia tradicional/educacional, NAO diagnostico.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .iris_features import normalizar_daugman, remover_reflexo
from .iris_advanced import realcar_clahe, fibras_frangi
from .validation import validar_imagem, validar_geometria, validar_lado


ZONAS_DIREITO = [
    "Cérebro / mente", "Seios da face", "Garganta e pescoço",
    "Pulmão e peito (dir.)", "Rim direito", "Cólon ascendente",
    "Órgãos pélvicos / bexiga", "Intestino delgado", "Fígado e vesícula",
    "Estômago", "Pâncreas / baço", "Tireoide",
]
ZONAS_ESQUERDO = [
    "Cérebro / mente", "Seios da face", "Garganta e pescoço",
    "Pulmão e peito (esq.)", "Coração", "Cólon descendente",
    "Órgãos pélvicos / bexiga", "Intestino delgado", "Baço",
    "Estômago", "Rim esquerdo", "Tireoide",
]

# Limiares por CONTRASTE LOCAL (robusto a cor da iris e a resolucao).
_CONTRASTE = 22           # pixel >22 niveis mais escuro que a vizinhanca = lacuna
_EDGE_BASE = 0.16         # densidade de borda "normal"; excesso vira marca
_OCL_MAX = 0.55           # >55% ocluido = nao avaliavel
_MARCA_MIN = 0.40         # intensidade minima para considerar zona "marcada"


@dataclass
class Zona:
    indice: int            # 0..11 (0 = topo / 12h)
    nome: str
    intensidade: float     # 0-1
    nivel: str             # "limpa" | "leve" | "moderada" | "acentuada" | "n/d"
    avaliavel: bool


def _nivel(v: float, avaliavel: bool) -> str:
    if not avaliavel:
        return "n/d"
    if v < _MARCA_MIN:
        return "limpa" if v < 0.20 else "leve"
    if v < 0.65:
        return "moderada"
    return "acentuada"


def analisar_zonas(img, centro, r_iris, r_pupila, lado: str, contorno=None) -> list[Zona]:
    validar_imagem(img, "img")
    validar_lado(lado)
    validar_geometria(centro, r_iris, r_pupila, img.shape)
    # Pre-processamento: remove reflexo + equaliza contraste (CLAHE).
    img = realcar_clahe(remover_reflexo(img, centro, r_iris))
    # Resolucao do mapa proporcional ao tamanho real da iris (evita ruido de
    # super-amostragem em iris pequenas/distantes).
    largura = int(np.clip(r_iris * 6, 96, 360))
    largura = (largura // 12) * 12
    altura = int(np.clip(r_iris * 0.9, 16, 64))
    polar, ocl = normalizar_daugman(img, centro, r_iris, r_pupila,
                                    altura=altura, largura=largura, contorno=contorno)
    gray = cv2.cvtColor(polar, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # Lacunas = contraste local: pixel bem mais escuro que sua vizinhanca.
    sigma = max(2.0, largura / 36.0)
    fundo = cv2.GaussianBlur(gray, (0, 0), sigma)
    contraste = fundo.astype(np.int16) - gray.astype(np.int16)   # >0 = mais escuro
    lacuna = contraste > _CONTRASTE
    # Fibras via Frangi (estruturas finas) — mede ruptura/densidade da trama.
    fib = fibras_frangi(gray)                                    # 0-1 por pixel

    visivel = ~ocl
    nomes = ZONAS_DIREITO if lado == "direito" else ZONAS_ESQUERDO
    n, larg = 12, polar.shape[1] // 12
    zonas = []
    for i in range(n):
        c0, c1 = i * larg, (i + 1) * larg
        vis = visivel[:, c0:c1]
        nvis = int(vis.sum())
        ocl_frac = 1.0 - nvis / vis.size
        avaliavel = ocl_frac <= _OCL_MAX and nvis > 20

        if avaliavel:
            lac_frac = float((lacuna[:, c0:c1] & vis).sum()) / nvis
            fib_frac = float(fib[:, c0:c1][vis].mean())
            fib_exc = max(0.0, fib_frac - _EDGE_BASE)
            intens = float(np.clip(3.2 * lac_frac + 1.2 * fib_exc, 0.0, 1.0))
        else:
            intens = 0.0

        idx_zona = (i + 3) % n
        zonas.append(Zona(i, nomes[idx_zona], intens, _nivel(intens, avaliavel), avaliavel))
    return zonas


def _cor_intensidade(z: Zona):
    if not z.avaliavel:
        return (90, 90, 90)          # cinza = nao avaliavel
    v = z.intensidade
    if v < 0.5:
        t = v / 0.5
        return (0, 200, int(60 + 195 * t))     # verde -> amarelo
    t = (v - 0.5) / 0.5
    return (0, int(200 * (1 - t)), 230)         # amarelo -> vermelho


def render_mapa(zonas: list[Zona], tamanho: int = 320, titulo: str = "") -> np.ndarray:
    canvas = np.full((tamanho, tamanho, 3), 26, np.uint8)
    c = tamanho // 2
    R = int(tamanho * 0.42)
    rp = int(R * 0.30)
    n = len(zonas)
    for z in zonas:
        ang0 = -90 + z.indice * (360 / n)
        ang1 = ang0 + (360 / n)
        cv2.ellipse(canvas, (c, c), (R, R), 0, ang0, ang1, _cor_intensidade(z), -1)
        am = np.deg2rad((ang0 + ang1) / 2)
        tx = int(c + (R * 0.72) * np.cos(am))
        ty = int(c + (R * 0.72) * np.sin(am))
        cv2.putText(canvas, str(z.indice + 1), (tx - 6, ty + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 20, 20), 2, cv2.LINE_AA)
    for i in range(n):
        a = np.deg2rad(-90 + i * (360 / n))
        cv2.line(canvas, (c, c), (int(c + R * np.cos(a)), int(c + R * np.sin(a))),
                 (40, 40, 40), 1)
    cv2.circle(canvas, (c, c), rp, (15, 15, 15), -1)
    cv2.circle(canvas, (c, c), R, (200, 200, 200), 1)
    if titulo:
        cv2.putText(canvas, titulo, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (255, 255, 255), 1, cv2.LINE_AA)
    return canvas


def top_zonas(zonas: list[Zona], k: int = 4) -> list[Zona]:
    """Apenas zonas avaliaveis e realmente marcadas (>= _MARCA_MIN)."""
    marcadas = [z for z in zonas if z.avaliavel and z.intensidade >= _MARCA_MIN]
    return sorted(marcadas, key=lambda z: z.intensidade, reverse=True)[:k]


def resumo_qualidade(zonas: list[Zona]) -> str:
    n_ocl = sum(1 for z in zonas if not z.avaliavel)
    if n_ocl >= 6:
        return "Boa parte da íris está coberta (pálpebra/cílio). Abra bem o olho."
    return ""
