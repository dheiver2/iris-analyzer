"""Analise da iris AO VIVO na webcam, com ZOOM e painel de resultados legivel.

Layout:
  [ video da webcam com a iris marcada ]  [ PAINEL LATERAL ]
                                          - zoom ampliado de cada iris
                                          - mapa de Daugman (iris desenrolada)
                                          - metricas explicadas por olho

Teclas:  S = salvar snapshot+relatorio   |   ESC = sair

AVISO: ferramenta EDUCACIONAL. A iridologia NAO tem validacao cientifica
como metodo diagnostico. Nada aqui constitui diagnostico medico.
"""
from __future__ import annotations

import os
import time

import cv2
import numpy as np

from iris_segmentation import segmentar_olhos, criar_landmarker, Olho
from iris_features import extrair_features, normalizar_daugman


PAINEL_W = 460          # largura do painel lateral
ZOOM_W = 200            # largura do recorte ampliado da iris
DAUGMAN_W = 420
DAUGMAN_H = 70


def _texto(img, txt, org, cor=(255, 255, 255), escala=0.5, grossura=1):
    cv2.putText(img, txt, org, cv2.FONT_HERSHEY_SIMPLEX, escala, (0, 0, 0),
                grossura + 2, cv2.LINE_AA)
    cv2.putText(img, txt, org, cv2.FONT_HERSHEY_SIMPLEX, escala, cor,
                grossura, cv2.LINE_AA)


def _recorte_zoom(img, olho: Olho, largura=ZOOM_W):
    """Recorta a regiao da iris com margem e amplia para 'largura' px."""
    cx, cy = olho.centro
    r = olho.raio_iris * 2.2  # margem ao redor
    x0, y0 = int(cx - r), int(cy - r)
    x1, y1 = int(cx + r), int(cy + r)
    h, w = img.shape[:2]
    x0c, y0c = max(0, x0), max(0, y0)
    x1c, y1c = min(w, x1), min(h, y1)
    if x1c <= x0c or y1c <= y0c:
        return None
    crop = img[y0c:y1c, x0c:x1c].copy()
    # marca a iris/pupila no recorte (coordenadas relativas)
    ccx, ccy = int(cx - x0c), int(cy - y0c)
    cv2.circle(crop, (ccx, ccy), int(olho.raio_iris), (0, 255, 0), 1)
    cv2.circle(crop, (ccx, ccy), int(olho.raio_pupila), (0, 0, 255), 1)
    escala = largura / crop.shape[1]
    return cv2.resize(crop, (largura, int(crop.shape[0] * escala)),
                      interpolation=cv2.INTER_CUBIC)


def _marca_no_video(frame, olho: Olho, f):
    c = (int(round(olho.centro[0])), int(round(olho.centro[1])))
    cor = (0, 255, 0) if f.qualidade_ok else (0, 165, 255)
    cv2.circle(frame, c, int(round(olho.raio_iris)), cor, 2)
    cv2.circle(frame, c, 2, (255, 0, 0), 2)
    _texto(frame, olho.lado, (c[0] - 22, c[1] - int(olho.raio_iris) - 6), cor, 0.45)


def _explica(f) -> list[tuple[str, tuple]]:
    """Linhas (texto, cor) explicando as metricas em linguagem simples."""
    L = []
    L.append((f"Cor da iris: {f.cor_predominante}", (0, 255, 255)))
    dens = ("densa (muitas fibras)" if f.densidade_fibras > 0.10
            else "lisa (poucas fibras)")
    L.append((f"Trama: {dens}", (255, 255, 255)))
    homog = ("uniforme" if f.glcm_homogeneidade > 0.5 else "com manchas/variacoes")
    L.append((f"Textura: {homog}", (255, 255, 255)))
    L.append((f"Nitidez do foco: {f.nitidez:.0f}"
              + ("  (boa)" if f.nitidez >= 40 else "  (RUIM-aproxime)"),
              (0, 255, 0) if f.nitidez >= 40 else (0, 165, 255)))
    L.append((f"Reflexo de luz: {f.reflexo_pct:.1f}%"
              + ("" if f.reflexo_pct <= 8 else "  (alto)"),
              (0, 255, 0) if f.reflexo_pct <= 8 else (0, 165, 255)))
    return L


def _montar_painel(altura, olhos, feats, img):
    painel = np.full((altura, PAINEL_W, 3), 30, np.uint8)
    _texto(painel, "ANALISE DA IRIS", (12, 28), (255, 255, 255), 0.7, 2)
    if not olhos:
        _texto(painel, "Nenhum olho detectado.", (12, 70), (0, 165, 255), 0.55)
        _texto(painel, "Aproxime o rosto da camera", (12, 96), (200, 200, 200), 0.5)
        _texto(painel, "e melhore a iluminacao.", (12, 118), (200, 200, 200), 0.5)
        return painel

    y = 50
    for olho, f in zip(olhos, feats):
        cor_q = (0, 255, 0) if f.qualidade_ok else (0, 165, 255)
        _texto(painel, f"OLHO {olho.lado.upper()}", (12, y), cor_q, 0.6, 2)
        y += 12

        zoom = _recorte_zoom(img, olho)
        daug = cv2.resize(
            normalizar_daugman(img, olho.centro, olho.raio_iris, olho.raio_pupila,
                               altura=40, largura=DAUGMAN_W - ZOOM_W - 24),
            (DAUGMAN_W - ZOOM_W - 24, 80), interpolation=cv2.INTER_CUBIC)

        if zoom is not None:
            zh = min(zoom.shape[0], altura - y - 4)
            painel[y:y + zh, 12:12 + ZOOM_W] = zoom[:zh]
            _texto(painel, "zoom", (14, y + 14), (0, 255, 0), 0.4)
            # Daugman ao lado do zoom
            dx = 12 + ZOOM_W + 12
            dh = min(daug.shape[0], altura - y - 4)
            painel[y:y + dh, dx:dx + daug.shape[1]] = daug[:dh]
            _texto(painel, "Daugman (iris desenrolada)", (dx, y + 12),
                   (255, 255, 0), 0.38)
            y += max(zh, dh) + 8

        for txt, cor in _explica(f):
            _texto(painel, txt, (14, y + 14), cor, 0.48)
            y += 22
        y += 10
        cv2.line(painel, (10, y), (PAINEL_W - 10, y), (80, 80, 80), 1)
        y += 18

    return painel


def main(camera: int = 0) -> None:
    cap = cv2.VideoCapture(camera)
    if not cap.isOpened():
        raise RuntimeError(
            "Nao foi possivel acessar a webcam. No macOS, autorize a camera em "
            "Ajustes > Privacidade e Seguranca > Camera."
        )

    print("Analise ao vivo. S = salvar snapshot | ESC = sair")
    landmarker = criar_landmarker()
    ultimo = 0.0
    olhos: list[Olho] = []
    feats = []
    fps = 0.0
    t_prev = time.time()

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            H = frame.shape[0]

            agora = time.time()
            if agora - ultimo > 0.12:
                ultimo = agora
                try:
                    olhos = segmentar_olhos(frame, landmarker)
                    feats = [extrair_features(frame, o.centro, o.raio_iris, o.raio_pupila)
                             for o in olhos]
                except Exception:
                    olhos, feats = [], []

            for o, f in zip(olhos, feats):
                _marca_no_video(frame, o, f)

            # barra inferior no video
            cv2.rectangle(frame, (0, H - 30), (frame.shape[1], H), (0, 0, 0), -1)
            _texto(frame, f"S=salvar  ESC=sair   |   {fps:4.1f} fps   |   "
                          "NAO e diagnostico medico", (8, H - 10),
                   (200, 200, 200), 0.5)

            painel = _montar_painel(H, olhos, feats, frame)
            combo = np.hstack([frame, painel])

            dt = agora - t_prev
            t_prev = agora
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt)

            cv2.imshow("Iris ao vivo - Iris Analyzer", combo)
            tecla = cv2.waitKey(1) & 0xFF
            if tecla == 27:
                break
            if tecla in (ord("s"), ord("S")):
                ts = time.strftime("%Y%m%d_%H%M%S")
                nome = f"snapshot_{ts}.jpg"
                cv2.imwrite(nome, combo)
                print(f"\nSnapshot salvo: {os.path.abspath(nome)}")
                for o, f in zip(olhos, feats):
                    print(f"  {o.lado}: cor={f.cor_predominante} "
                          f"dens={f.densidade_fibras} nitidez={f.nitidez} "
                          f"reflexo={f.reflexo_pct}% qual_ok={f.qualidade_ok}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        landmarker.close()


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Analise da iris ao vivo (zoom + painel)")
    ap.add_argument("--camera", type=int, default=0)
    main(ap.parse_args().camera)
