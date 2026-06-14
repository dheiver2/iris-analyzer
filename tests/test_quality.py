import types

import cv2
import numpy as np

from iris_analyzer.iris_quality import avaliar_qualidade, Qualidade, _foco_alta_frequencia


def _olho_de(d):
    pts = np.array([[d["centro"][0] - d["r_iris"], d["centro"][1]],
                    [d["centro"][0] + d["r_iris"], d["centro"][1]],
                    [d["centro"][0], d["centro"][1] - d["r_iris"]],
                    [d["centro"][0], d["centro"][1] + d["r_iris"]]], np.float64)
    return types.SimpleNamespace(
        centro=d["centro"], raio_iris=d["r_iris"], lado=d["lado"],
        contorno=d["contorno"], pontos_iris=pts)


def test_qualidade_retorna_score(iris_sintetica):
    d = iris_sintetica
    q = avaliar_qualidade(d["img"], _olho_de(d), d["r_pupila"])
    assert isinstance(q, Qualidade)
    assert 0.0 <= q.score <= 100.0
    assert 0.0 <= q.foco <= 1.0
    assert 0.0 <= q.oclusao <= 1.0
    assert 0.0 <= q.angulo <= 1.0
    assert q.nivel in ("ruim", "regular", "boa", "excelente")


def test_foco_nitido_maior_que_borrado(iris_sintetica):
    g = cv2.cvtColor(iris_sintetica["img"], cv2.COLOR_BGR2GRAY)
    nitido = _foco_alta_frequencia(g)
    borrado = _foco_alta_frequencia(cv2.GaussianBlur(g, (0, 0), 4))
    assert nitido > borrado


def test_frontal_melhor_angulo_que_off(iris_sintetica):
    d = iris_sintetica
    frontal = _olho_de(d)
    q_frontal = avaliar_qualidade(d["img"], frontal, d["r_pupila"])
    # simula off-angle: comprime a iris na horizontal (elipse)
    off = _olho_de(d)
    off.pontos_iris = off.pontos_iris.copy()
    off.pontos_iris[0, 0] = d["centro"][0] - d["r_iris"] * 0.4
    off.pontos_iris[1, 0] = d["centro"][0] + d["r_iris"] * 0.4
    q_off = avaliar_qualidade(d["img"], off, d["r_pupila"])
    assert q_frontal.angulo > q_off.angulo
