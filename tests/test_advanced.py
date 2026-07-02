import cv2
import numpy as np
import pytest

from iris_analyzer.iris_advanced import (
    detectar_colarete,
    detectar_lacunas,
    detectar_pupila,
    detectar_pupila_centro,
    fibras_frangi,
    heatmap_iris,
    realcar_clahe,
    refinar_iris,
)
from iris_analyzer.iris_segmentation import _circulo_de_pontos
from iris_analyzer.validation import GeometriaInvalidaError, ImagemInvalidaError


def test_pupila_centro(iris_sintetica):
    d = iris_sintetica
    cx, cy, r = detectar_pupila_centro(d["img"], d["centro"], d["r_iris"])
    # pupila sintetica centrada -> centro perto do centro da iris
    assert abs(cx - d["centro"][0]) < d["r_iris"] * 0.3
    assert abs(cy - d["centro"][1]) < d["r_iris"] * 0.3
    assert r > 0


def test_colarete_ratio(iris_sintetica):
    d = iris_sintetica
    rc = detectar_colarete(d["img"], d["centro"], d["r_iris"], d["r_pupila"])
    assert 0.0 <= rc < 1.0


def test_circulo_fit_exato():
    cx, cy, R = 100.0, 120.0, 50.0
    pts = np.array([[cx - R, cy], [cx + R, cy], [cx, cy - R], [cx, cy + R]], float)
    (c, r) = _circulo_de_pontos(pts)
    assert abs(c[0] - cx) < 0.5 and abs(c[1] - cy) < 0.5
    assert abs(r - R) < 0.5


def test_refino_borda_converge():
    img = np.full((240, 240, 3), 235, np.uint8)
    cv2.circle(img, (120, 120), 60, (90, 110, 80), -1)
    cv2.circle(img, (120, 120), 24, (15, 15, 15), -1)
    for palpite in (55, 60, 66):
        assert abs(refinar_iris(img, (120, 120), palpite) - 60) < 3.0


def test_refino_valida_entrada():
    with pytest.raises(ImagemInvalidaError):
        refinar_iris(None, (10, 10), 5)
    with pytest.raises(GeometriaInvalidaError):
        refinar_iris(np.zeros((40, 40, 3), np.uint8), (20, 20), 0)


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
