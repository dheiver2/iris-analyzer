import pytest

from iris_map import analisar_zonas, render_mapa, top_zonas, Zona
from validation import IrisError


def test_analisar_retorna_12_zonas(iris_sintetica):
    d = iris_sintetica
    zonas = analisar_zonas(d["img"], d["centro"], d["r_iris"], d["r_pupila"],
                           d["lado"], contorno=d["contorno"])
    assert len(zonas) == 12
    assert all(isinstance(z, Zona) for z in zonas)
    assert all(0.0 <= z.intensidade <= 1.0 for z in zonas)


def test_iris_limpa_sem_marcas(iris_sintetica):
    d = iris_sintetica
    zonas = analisar_zonas(d["img"], d["centro"], d["r_iris"], d["r_pupila"],
                           d["lado"], contorno=d["contorno"])
    assert top_zonas(zonas) == []          # nenhuma zona marcada numa iris limpa


def test_lacuna_eleva_intensidade(iris_sintetica, iris_com_lacuna):
    z_limpa = analisar_zonas(iris_sintetica["img"], iris_sintetica["centro"],
                             iris_sintetica["r_iris"], iris_sintetica["r_pupila"],
                             "direito", contorno=iris_sintetica["contorno"])
    z_marca = analisar_zonas(iris_com_lacuna["img"], iris_com_lacuna["centro"],
                             iris_com_lacuna["r_iris"], iris_com_lacuna["r_pupila"],
                             "direito", contorno=iris_com_lacuna["contorno"])
    assert max(z.intensidade for z in z_marca) > max(z.intensidade for z in z_limpa)


def test_render_mapa_tamanho(iris_sintetica):
    d = iris_sintetica
    zonas = analisar_zonas(d["img"], d["centro"], d["r_iris"], d["r_pupila"],
                           d["lado"], contorno=d["contorno"])
    img = render_mapa(zonas, 200)
    assert img.shape == (200, 200, 3)


def test_lado_invalido(iris_sintetica):
    d = iris_sintetica
    with pytest.raises(IrisError):
        analisar_zonas(d["img"], d["centro"], d["r_iris"], d["r_pupila"], "norte")
