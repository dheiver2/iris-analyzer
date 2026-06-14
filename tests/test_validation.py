import numpy as np
import pytest

from validation import (
    validar_imagem, validar_geometria, validar_lado,
    ImagemInvalidaError, GeometriaInvalidaError, IrisError,
)


def test_validar_imagem_ok():
    img = np.zeros((10, 10, 3), np.uint8)
    assert validar_imagem(img) is img


@pytest.mark.parametrize("bad", [None, "x", np.zeros((10, 10), np.uint8),
                                 np.zeros((1, 1, 3), np.uint8)])
def test_validar_imagem_falha(bad):
    with pytest.raises(ImagemInvalidaError):
        validar_imagem(bad)


def test_validar_geometria_ok():
    validar_geometria((50, 50), 40, 18, (100, 100, 3))


@pytest.mark.parametrize("centro,ri,rp", [
    ((50, 50), 0, 10),       # raio iris zero
    ((50, 50), 40, 0),       # pupila zero
    ((50, 50), 40, 50),      # pupila >= iris
    ((999, 999), 40, 18),    # centro fora
])
def test_validar_geometria_falha(centro, ri, rp):
    with pytest.raises(GeometriaInvalidaError):
        validar_geometria(centro, ri, rp, (100, 100, 3))


def test_validar_lado():
    assert validar_lado("direito") == "direito"
    with pytest.raises(IrisError):
        validar_lado("cima")
