"""Fixtures compartilhadas dos testes."""
from __future__ import annotations

import numpy as np
import cv2
import pytest


@pytest.fixture
def iris_sintetica():
    """Imagem BGR com uma iris limpa + geometria + contorno do olho.

    Retorna dict: img, centro, r_iris, r_pupila, contorno, lado.
    """
    img = np.full((240, 240, 3), 200, np.uint8)
    centro = (120.0, 120.0)
    r_iris, r_pupila = 80.0, 30.0
    cv2.circle(img, (120, 120), int(r_iris), (110, 150, 90), -1)
    for ang in range(0, 360, 4):
        a = np.deg2rad(ang)
        cv2.line(img, (120, 120),
                 (int(120 + r_iris * np.cos(a)), int(120 + r_iris * np.sin(a))),
                 (100, 140, 80), 1)
    cv2.circle(img, (120, 120), int(r_pupila), (15, 15, 15), -1)
    contorno = np.array([[40, 120], [120, 60], [200, 120], [120, 180]], np.int32)
    return {
        "img": img, "centro": centro, "r_iris": r_iris,
        "r_pupila": r_pupila, "contorno": contorno, "lado": "direito",
    }


@pytest.fixture
def iris_com_lacuna(iris_sintetica):
    """Igual a iris_sintetica, mas com uma mancha escura (lacuna) num setor."""
    d = dict(iris_sintetica)
    img = d["img"].copy()
    cv2.circle(img, (120, 65), 12, (20, 20, 20), -1)   # mancha no topo
    d["img"] = img
    return d
