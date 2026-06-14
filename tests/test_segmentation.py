"""Teste de integracao da segmentacao (MediaPipe).

Requer o modelo face_landmarker.task e uma imagem de rosto. Sem eles, o teste
e pulado (skip) em vez de falhar — para nao quebrar CI offline.
"""
import os

import cv2
import numpy as np
import pytest

import config
from iris_segmentation import segmentar_olhos, criar_landmarker
from validation import ImagemInvalidaError

ASSET = os.path.join(os.path.dirname(__file__), "assets", "rosto.jpg")


def test_segmentar_valida_entrada():
    with pytest.raises(ImagemInvalidaError):
        segmentar_olhos(None)


@pytest.mark.skipif(not config.MODELO_PATH.exists(),
                    reason="modelo face_landmarker.task ausente")
@pytest.mark.skipif(not os.path.exists(ASSET),
                    reason="imagem de teste tests/assets/rosto.jpg ausente")
def test_segmentar_dois_olhos():
    img = cv2.imread(ASSET)
    lm = criar_landmarker()
    try:
        olhos = segmentar_olhos(img, lm)
    finally:
        lm.close()
    assert len(olhos) == 2
    lados = {o.lado for o in olhos}
    assert lados == {"direito", "esquerdo"}
    for o in olhos:
        assert o.raio_iris > 0
        assert o.contorno is not None and len(o.contorno) >= 4
