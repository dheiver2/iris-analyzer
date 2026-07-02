"""Tecnicas avancadas de analise de imagem da iris (melhoram a PRECISAO da
extracao de caracteristicas — nao a validade do mapa iridologico).

- detectar_pupila: encontra a pupila real (disco escuro central) em vez de
  estimar um raio fixo. Melhora muito a normalizacao de Daugman.
- realcar_clahe: equalizacao adaptativa de contraste (ilumina\xe7\xe3o irregular).
- fibras_frangi: filtro de Frangi (vesselness) realca a trama de fibras.
- detectar_lacunas: lacunas/criptas como blobs (componentes conexos filtrados
  por area e forma), nao apenas pixels escuros.
- heatmap_iris: mapa de calor continuo das marcas sobre a propria iris.
"""
from __future__ import annotations

import cv2
import numpy as np
from skimage.filters import frangi

from .iris_features import remover_reflexo
from .validation import GeometriaInvalidaError, validar_geometria, validar_imagem


def refinar_iris(imagem_bgr, centro, r_iris, busca=0.16, n_amostras=180) -> float:
    """Refina o raio da iris pelo operador integro-diferencial (Daugman).

    Procura o raio que maximiza |d/dr| da integral de contorno circular da
    intensidade — i.e., a borda real iris/esclera detectada pelo gradiente da
    imagem, com precisao sub-pixel. Amostra apenas os arcos laterais (onde a
    esclera e visivel), evitando palpebra/cilio em cima e embaixo.
    """
    validar_imagem(imagem_bgr, "imagem_bgr")
    if not (r_iris > 0):
        raise GeometriaInvalidaError(f"r_iris deve ser > 0, recebido {r_iris!r}.")
    gray = cv2.GaussianBlur(cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2GRAY), (3, 3), 0)
    gray = gray.astype(np.float32)
    h, w = gray.shape
    cx, cy = float(centro[0]), float(centro[1])

    base = np.linspace(-np.deg2rad(35), np.deg2rad(35), max(n_amostras // 2, 8))
    thetas = np.concatenate([base, base + np.pi])
    cos_t, sin_t = np.cos(thetas), np.sin(thetas)

    r0 = max(3.0, r_iris * (1 - busca))
    r1 = r_iris * (1 + busca)
    raios = np.arange(r0, r1, 0.5)
    if len(raios) < 5:
        return float(r_iris)

    integrais = []
    for r in raios:
        xs = np.clip(np.round(cx + r * cos_t).astype(int), 0, w - 1)
        ys = np.clip(np.round(cy + r * sin_t).astype(int), 0, h - 1)
        integrais.append(float(gray[ys, xs].mean()))
    integrais = np.array(integrais)

    k = np.array([1, 4, 6, 4, 1], np.float32); k /= k.sum()
    # padding por replicacao (evita gradiente espurio nas bordas do sinal)
    pad = len(k) // 2
    ext = np.pad(integrais, pad, mode="edge")
    suave = np.convolve(ext, k, mode="valid")
    deriv = np.abs(np.gradient(suave))
    deriv[:2] = 0.0; deriv[-2:] = 0.0          # ignora extremos da busca
    if not np.any(deriv > 0):
        return float(r_iris)
    r_ref = float(raios[int(np.argmax(deriv))])
    if abs(r_ref - r_iris) <= r_iris * busca:
        return r_ref
    return float(r_iris)


def detectar_pupila(imagem_bgr, centro, r_iris) -> float:
    """Estima o raio real da pupila (disco escuro central). Fallback: 0.45*r."""
    validar_imagem(imagem_bgr, "imagem_bgr")
    if not (r_iris > 0):
        raise GeometriaInvalidaError(f"r_iris deve ser > 0, recebido {r_iris!r}.")
    cx, cy = int(round(centro[0])), int(round(centro[1]))
    r = int(round(r_iris))
    h, w = imagem_bgr.shape[:2]
    x0, y0 = max(0, cx - r), max(0, cy - r)
    x1, y1 = min(w, cx + r), min(h, cy + r)
    roi = imagem_bgr[y0:y1, x0:x1]
    if roi.size == 0:
        return max(r_iris * 0.45, 2.0)

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    # pupila = regiao mais escura; limiar pelo percentil baixo
    thr = np.percentile(gray, 12)
    escuro = (gray <= thr).astype(np.uint8) * 255
    escuro = cv2.morphologyEx(escuro, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    escuro = cv2.morphologyEx(escuro, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

    cnts, _ = cv2.findContours(escuro, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cxr, cyr = cx - x0, cy - y0
    melhor = None
    for c in cnts:
        (px, py), pr = cv2.minEnclosingCircle(c)
        area = cv2.contourArea(c)
        if pr < r * 0.12 or pr > r * 0.75:
            continue
        circ = area / (np.pi * pr * pr + 1e-6)        # circularidade
        dist = np.hypot(px - cxr, py - cyr)
        if circ > 0.55 and dist < r * 0.5:
            if melhor is None or pr > melhor[0]:
                melhor = (pr, px + x0, py + y0)
    if melhor is None:
        return max(r_iris * 0.45, 2.0)
    return float(np.clip(melhor[0], r_iris * 0.15, r_iris * 0.75))


def detectar_pupila_centro(imagem_bgr, centro, r_iris):
    """Como detectar_pupila, mas retorna (cx, cy, raio) do disco da pupila.

    Centro cai para o centro da iris se a pupila nao for localizada — util
    para checar concentricidade pupila/iris.
    """
    validar_imagem(imagem_bgr, "imagem_bgr")
    if not (r_iris > 0):
        raise GeometriaInvalidaError(f"r_iris deve ser > 0, recebido {r_iris!r}.")
    cx, cy = int(round(centro[0])), int(round(centro[1]))
    r = int(round(r_iris))
    h, w = imagem_bgr.shape[:2]
    x0, y0 = max(0, cx - r), max(0, cy - r)
    x1, y1 = min(w, cx + r), min(h, cy + r)
    roi = imagem_bgr[y0:y1, x0:x1]
    if roi.size == 0:
        return (float(centro[0]), float(centro[1]), max(r_iris * 0.45, 2.0))
    gray = cv2.GaussianBlur(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    thr = np.percentile(gray, 12)
    escuro = (gray <= thr).astype(np.uint8) * 255
    escuro = cv2.morphologyEx(escuro, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    escuro = cv2.morphologyEx(escuro, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    cnts, _ = cv2.findContours(escuro, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cxr, cyr = cx - x0, cy - y0
    melhor = None
    for c in cnts:
        (px, py), pr = cv2.minEnclosingCircle(c)
        area = cv2.contourArea(c)
        if pr < r * 0.12 or pr > r * 0.75:
            continue
        circ = area / (np.pi * pr * pr + 1e-6)
        if circ > 0.55 and np.hypot(px - cxr, py - cyr) < r * 0.5:
            if melhor is None or pr > melhor[0]:
                melhor = (pr, px + x0, py + y0)
    if melhor is None:
        return (float(centro[0]), float(centro[1]), max(r_iris * 0.45, 2.0))
    pr = float(np.clip(melhor[0], r_iris * 0.15, r_iris * 0.75))
    return (float(melhor[1]), float(melhor[2]), pr)


def detectar_colarete(imagem_bgr, centro, r_iris, r_pupila) -> float:
    """Estima o raio do anel de colarete (fronteira zona pupilar/ciliar).

    Amostra o perfil radial medio de intensidade entre a pupila e ~60% da iris
    e retorna o raio (em px) do gradiente mais forte — onde a textura muda.
    Retorna a razao colarete/iris util para descricao. 0 se nao detectado.
    """
    validar_imagem(imagem_bgr, "imagem_bgr")
    img = remover_reflexo(imagem_bgr, centro, r_iris)
    gray = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (3, 3), 0).astype(np.float32)
    h, w = gray.shape
    cx, cy = float(centro[0]), float(centro[1])
    r0, r1 = r_pupila * 1.05, r_iris * 0.62
    if r1 <= r0:
        return 0.0
    raios = np.arange(r0, r1, 0.5)
    thetas = np.linspace(0, 2 * np.pi, 180, endpoint=False)
    cos_t, sin_t = np.cos(thetas), np.sin(thetas)
    perfil = []
    for r in raios:
        xs = np.clip(np.round(cx + r * cos_t).astype(int), 0, w - 1)
        ys = np.clip(np.round(cy + r * sin_t).astype(int), 0, h - 1)
        perfil.append(float(gray[ys, xs].mean()))
    perfil = np.array(perfil)
    k = np.array([1, 4, 6, 4, 1], np.float32); k /= k.sum()
    suave = np.convolve(np.pad(perfil, 2, mode="edge"), k, mode="valid")
    deriv = np.abs(np.gradient(suave))
    deriv[:2] = 0; deriv[-2:] = 0
    if not np.any(deriv > 0):
        return 0.0
    return float(raios[int(np.argmax(deriv))] / r_iris)


def realcar_clahe(imagem_bgr) -> np.ndarray:
    """Equaliza contraste de forma adaptativa (CLAHE) no canal L (Lab)."""
    lab = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l = clahe.apply(l)
    return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)


def fibras_frangi(gray) -> np.ndarray:
    """Resposta de Frangi (0-1): realca fibras/estruturas finas da iris."""
    g = gray.astype(np.float32) / 255.0
    resp = frangi(g, sigmas=range(1, 4), black_ridges=False)
    m = resp.max()
    return (resp / m) if m > 1e-9 else resp


def detectar_lacunas(gray, mask=None):
    """Detecta lacunas/criptas como blobs escuros. Retorna (mascara, lista).

    lista = [(x, y, raio), ...] de cada lacuna detectada.
    """
    g = cv2.GaussianBlur(gray, (3, 3), 0)
    # realca regioes mais escuras que a vizinhanca
    fundo = cv2.GaussianBlur(g, (0, 0), max(3.0, gray.shape[1] / 24.0))
    contraste = cv2.subtract(fundo, g)
    _, binm = cv2.threshold(contraste, 18, 255, cv2.THRESH_BINARY)
    if mask is not None:
        binm = cv2.bitwise_and(binm, mask)
    binm = cv2.morphologyEx(binm, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    num, lbl, stats, cent = cv2.connectedComponentsWithStats(binm, 8)
    out_mask = np.zeros_like(binm)
    blobs = []
    area_min = max(8, (gray.shape[0] * gray.shape[1]) // 4000)
    for i in range(1, num):
        area = stats[i, cv2.CC_STAT_AREA]
        wlb, hlb = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
        if area < area_min:
            continue
        aspecto = wlb / (hlb + 1e-6)
        if aspecto < 0.35 or aspecto > 2.8:   # descarta riscos finos (cilio)
            continue
        out_mask[lbl == i] = 255
        x, y = cent[i]
        blobs.append((float(x), float(y), float(np.sqrt(area / np.pi))))
    return out_mask, blobs


def heatmap_iris(imagem_bgr, centro, r_iris, r_pupila):
    """Mapa de calor continuo das marcas (lacunas+fibras) sobre a iris."""
    validar_imagem(imagem_bgr, "imagem_bgr")
    validar_geometria(centro, r_iris, r_pupila, imagem_bgr.shape)
    cx, cy = int(round(centro[0])), int(round(centro[1]))
    r = int(round(r_iris))
    h, w = imagem_bgr.shape[:2]
    x0, y0 = max(0, cx - r), max(0, cy - r)
    x1, y1 = min(w, cx + r), min(h, cy + r)
    roi = imagem_bgr[y0:y1, x0:x1]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    mask = np.zeros(gray.shape, np.uint8)
    cv2.circle(mask, (cx - x0, cy - y0), r, 255, -1)
    cv2.circle(mask, (cx - x0, cy - y0), int(r_pupila), 0, -1)

    lac, _ = detectar_lacunas(gray, mask)
    fib = (fibras_frangi(gray) * 255).astype(np.uint8)
    energia = cv2.addWeighted(lac, 0.6, fib, 0.4, 0)
    energia = cv2.GaussianBlur(energia, (0, 0), 3)
    energia = cv2.bitwise_and(energia, mask)

    cor = cv2.applyColorMap(energia, cv2.COLORMAP_JET)
    out = roi.copy()
    m3 = mask > 0
    out[m3] = cv2.addWeighted(roi, 0.55, cor, 0.45, 0)[m3]
    return out
