"""Normalizacao de Daugman e extracao de features da iris.

- Daugman rubber-sheet: desenrola o anel da iris (pupila->limbo) em uma
  imagem polar normalizada (theta x rho), tornando textura/cor comparaveis.
- Features: cor (Lab), textura via filtros de Gabor, LBP e GLCM.
- Qualidade da imagem: nitidez (Laplaciano) e reflexos especulares.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np
from skimage.feature import local_binary_pattern, graycomatrix, graycoprops

from validation import validar_imagem, validar_geometria


@dataclass
class FeaturesIris:
    cor_predominante: str
    lab_medio: tuple[float, float, float]
    gabor_energia: float          # forca/contraste das fibras orientadas
    lbp_uniformidade: float       # 0-1, regularidade da micro-textura
    glcm_contraste: float
    glcm_homogeneidade: float
    densidade_fibras: float       # 0-1
    nitidez: float                # variancia do Laplaciano (maior=mais nitido)
    reflexo_pct: float            # % de pixels com reflexo especular
    qualidade_ok: bool
    avisos: list[str] = field(default_factory=list)


def remover_reflexo(imagem_bgr, centro, r_iris) -> np.ndarray:
    """Inpainting dos reflexos especulares (pontos brancos) na regiao da iris."""
    h, w = imagem_bgr.shape[:2]
    c = (int(round(centro[0])), int(round(centro[1])))
    roi = np.zeros((h, w), np.uint8)
    cv2.circle(roi, c, int(round(r_iris)), 255, -1)
    gray = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2GRAY)
    brilho = ((gray > 230).astype(np.uint8) * 255) & roi
    if np.count_nonzero(brilho) == 0:
        return imagem_bgr
    brilho = cv2.dilate(brilho, np.ones((3, 3), np.uint8), iterations=1)
    return cv2.inpaint(imagem_bgr, brilho, 3, cv2.INPAINT_TELEA)


def _mascara_olho(shape, contorno):
    m = np.zeros(shape[:2], np.uint8)
    if contorno is not None:
        cv2.fillPoly(m, [contorno.astype(np.int32)], 255)
    else:
        m[:] = 255
    return m


def normalizar_daugman(
    imagem_bgr: np.ndarray,
    centro: tuple[float, float],
    r_iris: float,
    r_pupila: float,
    altura: int = 64,
    largura: int = 256,
    contorno=None,
):
    """Desenrola o anel da iris em imagem polar (altura=rho, largura=theta).

    Se ``contorno`` (poligono da abertura do olho) for dado, tambem retorna uma
    mascara de oclusao (True onde o ponto cai fora do olho = palpebra/cilio).
    Sem contorno, retorna apenas a imagem polar (compatibilidade).
    """
    validar_imagem(imagem_bgr, "imagem_bgr")
    validar_geometria(centro, r_iris, r_pupila, imagem_bgr.shape)
    if altura < 2 or largura < 2:
        raise ValueError(f"altura/largura do mapa polar invalidas: {altura}x{largura}.")
    cx, cy = centro
    h_img, w_img = imagem_bgr.shape[:2]
    out = np.zeros((altura, largura, 3), dtype=np.uint8)
    ocl = np.zeros((altura, largura), dtype=bool)
    olho_mask = _mascara_olho(imagem_bgr.shape, contorno) if contorno is not None else None

    thetas = np.linspace(0.0, 2.0 * np.pi, largura, endpoint=False)
    rhos = np.linspace(0.0, 1.0, altura)
    cos_t, sin_t = np.cos(thetas), np.sin(thetas)
    for i, rho in enumerate(rhos):
        r = r_pupila + (r_iris - r_pupila) * rho
        xs = cx + r * cos_t
        ys = cy + r * sin_t
        xs_i = np.clip(np.round(xs).astype(int), 0, w_img - 1)
        ys_i = np.clip(np.round(ys).astype(int), 0, h_img - 1)
        out[i] = imagem_bgr[ys_i, xs_i]
        if olho_mask is not None:
            ocl[i] = olho_mask[ys_i, xs_i] == 0

    if contorno is not None:
        return out, ocl
    return out


def _nome_cor_lab(lab: tuple[float, float, float], bgr_medio) -> str:
    hsv = cv2.cvtColor(np.uint8([[bgr_medio]]), cv2.COLOR_BGR2HSV)[0][0]
    h, s, v = int(hsv[0]), int(hsv[1]), int(hsv[2])
    if v < 60:
        return "castanho muito escuro"
    if s < 35:
        return "cinza / azul-acinzentado"
    if h < 15 or h >= 160:
        return "castanho avermelhado"
    if 15 <= h < 35:
        return "castanho / mel"
    if 35 <= h < 85:
        return "esverdeado / avela"
    if 85 <= h < 130:
        return "azul"
    return "indefinido"


def _gabor_energia(gray: np.ndarray) -> float:
    energia = 0.0
    for theta in np.arange(0, np.pi, np.pi / 4):
        kern = cv2.getGaborKernel((15, 15), 4.0, theta, 8.0, 0.5, 0, ktype=cv2.CV_32F)
        filt = cv2.filter2D(gray.astype(np.float32), cv2.CV_32F, kern)
        energia += float(np.mean(filt ** 2))
    return energia / 4.0


def _qualidade(gray_iris: np.ndarray, mask: np.ndarray):
    nitidez = float(cv2.Laplacian(gray_iris, cv2.CV_64F).var())
    reflexo = float(np.count_nonzero((gray_iris > 240) & (mask > 0)))
    total = float(np.count_nonzero(mask)) or 1.0
    reflexo_pct = 100.0 * reflexo / total
    return nitidez, reflexo_pct


def extrair_features(
    imagem_bgr: np.ndarray,
    centro: tuple[float, float],
    r_iris: float,
    r_pupila: float,
) -> FeaturesIris:
    validar_imagem(imagem_bgr, "imagem_bgr")
    validar_geometria(centro, r_iris, r_pupila, imagem_bgr.shape)
    h, w = imagem_bgr.shape[:2]
    c = (int(round(centro[0])), int(round(centro[1])))

    # Mascara do anel da iris (exclui pupila).
    mask = np.zeros((h, w), np.uint8)
    cv2.circle(mask, c, int(round(r_iris)), 255, -1)
    cv2.circle(mask, c, int(round(r_pupila)), 0, -1)

    gray = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2GRAY)

    # ----- Cor (no anel) -----
    bgr_medio = cv2.mean(imagem_bgr, mask=mask)[:3]
    lab_img = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2LAB)
    lab_medio = cv2.mean(lab_img, mask=mask)[:3]
    cor = _nome_cor_lab(lab_medio, bgr_medio)

    # ----- Daugman + textura na faixa normalizada -----
    polar = normalizar_daugman(imagem_bgr, centro, r_iris, r_pupila)
    polar_gray = cv2.cvtColor(polar, cv2.COLOR_BGR2GRAY)

    gabor = _gabor_energia(polar_gray)

    lbp = local_binary_pattern(polar_gray, P=8, R=1, method="uniform")
    hist, _ = np.histogram(lbp, bins=np.arange(0, 11), density=True)
    lbp_unif = float(hist[:9].sum())  # padroes uniformes = regularidade

    glcm = graycomatrix(
        polar_gray, distances=[1], angles=[0], levels=256, symmetric=True, normed=True
    )
    contraste = float(graycoprops(glcm, "contrast")[0, 0])
    homog = float(graycoprops(glcm, "homogeneity")[0, 0])

    bordas = cv2.Canny(polar_gray, 50, 150)
    densidade = float(np.count_nonzero(bordas)) / bordas.size

    # ----- Qualidade -----
    nitidez, reflexo_pct = _qualidade(gray, mask)
    avisos: list[str] = []
    qualidade_ok = True
    if nitidez < 40:
        qualidade_ok = False
        avisos.append("Imagem pouco nitida (foco/movimento). Refaca mais proximo e firme.")
    if reflexo_pct > 8:
        qualidade_ok = False
        avisos.append(
            f"Muito reflexo na iris ({reflexo_pct:.1f}%). Evite luz direta/flash."
        )

    return FeaturesIris(
        cor_predominante=cor,
        lab_medio=tuple(round(float(x), 1) for x in lab_medio),
        gabor_energia=round(gabor, 2),
        lbp_uniformidade=round(lbp_unif, 4),
        glcm_contraste=round(contraste, 2),
        glcm_homogeneidade=round(homog, 4),
        densidade_fibras=round(densidade, 4),
        nitidez=round(nitidez, 1),
        reflexo_pct=round(reflexo_pct, 2),
        qualidade_ok=qualidade_ok,
        avisos=avisos,
    )
