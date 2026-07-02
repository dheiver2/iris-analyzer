import numpy as np
import pytest

from iris_analyzer.iris_features import (
    FeaturesIris,
    extrair_features,
    normalizar_daugman,
    remover_reflexo,
)
from iris_analyzer.validation import GeometriaInvalidaError, ImagemInvalidaError


def test_daugman_shape(iris_sintetica):
    d = iris_sintetica
    polar = normalizar_daugman(d["img"], d["centro"], d["r_iris"], d["r_pupila"],
                               altura=64, largura=256)
    assert polar.shape == (64, 256, 3)


def test_daugman_com_contorno_retorna_mascara(iris_sintetica):
    d = iris_sintetica
    polar, ocl = normalizar_daugman(d["img"], d["centro"], d["r_iris"],
                                    d["r_pupila"], contorno=d["contorno"])
    assert polar.shape[:2] == ocl.shape
    assert ocl.dtype == bool


def test_extrair_features_ranges(iris_sintetica):
    d = iris_sintetica
    f = extrair_features(d["img"], d["centro"], d["r_iris"], d["r_pupila"])
    assert isinstance(f, FeaturesIris)
    assert 0.0 <= f.lbp_uniformidade <= 1.0
    assert 0.0 <= f.glcm_homogeneidade <= 1.0
    assert 0.0 <= f.densidade_fibras <= 1.0
    assert f.nitidez >= 0.0
    assert 0.0 <= f.reflexo_pct <= 100.0


def test_remover_reflexo_preserva_shape(iris_sintetica):
    d = iris_sintetica
    out = remover_reflexo(d["img"], d["centro"], d["r_iris"])
    assert out.shape == d["img"].shape


def test_features_valida_entrada():
    with pytest.raises(ImagemInvalidaError):
        extrair_features(None, (10, 10), 5, 2)
    img = np.zeros((50, 50, 3), np.uint8)
    with pytest.raises(GeometriaInvalidaError):
        extrair_features(img, (25, 25), 10, 20)   # pupila > iris
