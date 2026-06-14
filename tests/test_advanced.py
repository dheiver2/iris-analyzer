import cv2
import numpy as np
import pytest

from iris_analyzer.iris_advanced import (
    detectar_pupila, realcar_clahe, fibras_frangi, detectar_lacunas, heatmap_iris,
)
from iris_analyzer.validation import ImagemInvalidaError, GeometriaInvalidaError


def test_detectar_pupila_plausivel(iris_sintetica):
    d = iris_sintetica
    rp = detectar_pupila(d["img"], d["centro"], d["r_iris"])
    assert d["r_iris"] * 0.15 <= rp <= d["r_iris"] * 0.75


def test_clahe_preserva_shape(iris_sintetica):
    out = realcar_clahe(iris_sintetica["img"])
    assert out.shape == iris_sintetica["img"].shape


def test_frangi_normalizado(iris_sintetica):
    g = cv2.cvtColor(iris_sintetica["img"], cv2.COLOR_BGR2GRAY)
    fr = fibras_frangi(g)
    assert fr.shape == g.shape
    assert 0.0 <= float(fr.min()) and float(fr.max()) <= 1.0


def test_detectar_lacunas_retorna_blobs(iris_com_lacuna):
    g = cv2.cvtColor(iris_com_lacuna["img"], cv2.COLOR_BGR2GRAY)
    mask, blobs = detectar_lacunas(g)
    assert mask.shape == g.shape
    assert isinstance(blobs, list)


def test_heatmap_shape(iris_sintetica):
    d = iris_sintetica
    hm = heatmap_iris(d["img"], d["centro"], d["r_iris"], d["r_pupila"])
    assert hm.ndim == 3 and hm.shape[2] == 3


def test_pupila_valida_entrada():
    with pytest.raises(ImagemInvalidaError):
        detectar_pupila(None, (10, 10), 5)
    img = np.zeros((40, 40, 3), np.uint8)
    with pytest.raises(GeometriaInvalidaError):
        detectar_pupila(img, (20, 20), 0)
