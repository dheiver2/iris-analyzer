"""Analise de imagem da iris com tecnicas de visao computacional.

AVISO IMPORTANTE
----------------
A IRIDOLOGIA NAO E RECONHECIDA PELA CIENCIA como metodo diagnostico.
Revisoes sistematicas (p.ex. Ernst, 2000) concluiram que ela nao identifica
doencas de forma confiavel. Este modulo e EDUCACIONAL/EXPERIMENTAL: ele extrai
caracteristicas objetivas da imagem (cor, textura, padroes) e as descreve.
NADA AQUI E DIAGNOSTICO MEDICO. Consulte sempre um profissional de saude.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np


@dataclass
class ResultadoIris:
    olho_detectado: bool
    centro: tuple[int, int] | None = None
    raio_iris: int | None = None
    raio_pupila: int | None = None
    cor_predominante: str = ""
    cor_bgr_media: tuple[int, int, int] | None = None
    textura_densidade: float = 0.0  # 0-1, fibras/linhas detectadas
    homogeneidade: float = 0.0       # 0-1, uniformidade da textura
    observacoes: list[str] = field(default_factory=list)


def _detectar_iris(gray: np.ndarray) -> tuple[int, int, int] | None:
    """Detecta a iris como um circulo via Hough. Retorna (x, y, r)."""
    blur = cv2.medianBlur(gray, 5)
    h, w = gray.shape
    minr = int(min(h, w) * 0.10)
    maxr = int(min(h, w) * 0.48)
    # Tenta com sensibilidade crescente (param2 menor = mais permissivo)
    for param2 in (45, 35, 25, 18):
        circ = cv2.HoughCircles(
            blur,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=h,
            param1=100,
            param2=param2,
            minRadius=minr,
            maxRadius=maxr,
        )
        if circ is not None:
            circ = np.uint16(np.around(circ))
            x, y, r = circ[0][0]
            return int(x), int(y), int(r)
    return None


def _nome_cor(bgr: tuple[float, float, float]) -> str:
    b, g, r = bgr
    hsv = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0][0]
    h, s, v = int(hsv[0]), int(hsv[1]), int(hsv[2])
    if v < 60:
        return "castanho muito escuro / preto"
    if s < 40:
        return "cinza / azul-acinzentado claro"
    if h < 15 or h >= 160:
        return "castanho avermelhado"
    if 15 <= h < 35:
        return "castanho / mel"
    if 35 <= h < 85:
        return "esverdeado / avela"
    if 85 <= h < 130:
        return "azul"
    return "indefinido"


def _mascara_anel(shape, centro, r_iris, r_pupila):
    mask = np.zeros(shape[:2], dtype=np.uint8)
    cv2.circle(mask, centro, r_iris, 255, -1)
    cv2.circle(mask, centro, r_pupila, 0, -1)
    return mask


def analisar_iris(imagem_bgr: np.ndarray) -> ResultadoIris:
    """Recebe um frame BGR (OpenCV) e retorna caracteristicas da iris."""
    gray = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2GRAY)
    det = _detectar_iris(gray)

    if det is None:
        return ResultadoIris(
            olho_detectado=False,
            observacoes=[
                "Iris nao detectada. Aproxime o olho da camera, melhore a "
                "iluminacao e mantenha o olho centralizado e bem aberto."
            ],
        )

    x, y, r = det
    centro = (x, y)
    r_pupila = max(int(r * 0.30), 3)  # estimativa da pupila

    # Cor predominante no anel da iris (excluindo pupila)
    mask = _mascara_anel(imagem_bgr.shape, centro, r, r_pupila)
    media = cv2.mean(imagem_bgr, mask=mask)[:3]  # BGR
    cor_bgr = tuple(int(c) for c in media)
    cor = _nome_cor(media)

    # Textura: densidade de bordas (fibras) dentro da iris
    bordas = cv2.Canny(gray, 50, 150)
    bordas_iris = cv2.bitwise_and(bordas, bordas, mask=mask)
    n_pix = int(np.count_nonzero(mask))
    densidade = float(np.count_nonzero(bordas_iris)) / n_pix if n_pix else 0.0

    # Homogeneidade: 1 - desvio padrao normalizado da intensidade
    vals = gray[mask > 0].astype(np.float32)
    homog = float(1.0 - min(vals.std() / 128.0, 1.0)) if vals.size else 0.0

    obs: list[str] = []
    obs.append(f"Cor predominante observada: {cor}.")
    if densidade > 0.12:
        obs.append(
            "Trama de fibras densa/marcada (muitas linhas). "
            "Na iridologia tradicional associa-se a constituicao 'tensa' "
            "(SEM valor diagnostico)."
        )
    else:
        obs.append(
            "Trama de fibras mais lisa/uniforme. "
            "Na iridologia associa-se a constituicao 'relaxada' "
            "(SEM valor diagnostico)."
        )
    if homog < 0.5:
        obs.append(
            "Textura heterogenea: presenca de manchas/variacoes de tom "
            "(pode ser apenas reflexo, sombra ou foco)."
        )
    obs.append(
        "LEMBRETE: iridologia nao e validada cientificamente. "
        "Isto NAO e diagnostico medico."
    )

    return ResultadoIris(
        olho_detectado=True,
        centro=centro,
        raio_iris=r,
        raio_pupila=r_pupila,
        cor_predominante=cor,
        cor_bgr_media=cor_bgr,
        textura_densidade=round(densidade, 4),
        homogeneidade=round(homog, 4),
        observacoes=obs,
    )


def desenhar_anotacoes(imagem_bgr: np.ndarray, res: ResultadoIris) -> np.ndarray:
    """Retorna copia da imagem com a iris/pupila marcadas."""
    out = imagem_bgr.copy()
    if res.olho_detectado and res.centro:
        cv2.circle(out, res.centro, res.raio_iris, (0, 255, 0), 2)
        cv2.circle(out, res.centro, res.raio_pupila, (0, 0, 255), 2)
        cv2.circle(out, res.centro, 2, (255, 0, 0), 3)
    return out
