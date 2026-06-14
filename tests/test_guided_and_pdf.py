import os
import types

import numpy as np
import pytest

from captura_guiada import avaliar
from pdf_report import gerar_pdf, DadosCliente


def _olho(cx, cy, r):
    return types.SimpleNamespace(centro=(cx, cy), raio_iris=r, lado="direito")


def _feat(nitidez, reflexo):
    return types.SimpleNamespace(nitidez=nitidez, reflexo_pct=reflexo)


def test_avaliar_criterios():
    frame = np.zeros((480, 640, 3), np.uint8)
    crit, ok = avaliar(frame, [], [])
    assert len(crit) == 6
    assert ok is False                  # sem olhos -> nao ok


def test_avaliar_imagem_boa():
    frame = np.zeros((480, 640, 3), np.uint8)
    olhos = [_olho(300, 220, 20), _olho(360, 220, 20)]
    feats = [_feat(80, 0.0), _feat(80, 0.0)]
    crit, ok = avaliar(frame, olhos, feats)
    assert ok is True


def test_gerar_pdf_cria_arquivo(tmp_path):
    destino = str(tmp_path / "laudo.pdf")
    info = [{"lado": "direito", "cor": "azul", "trama": "lisa",
             "textura": "uniforme", "nitidez": "60", "reflexo": 0.0,
             "qualidade": True, "zonas": ["Nenhuma marca."]}]
    caminho = gerar_pdf(destino, DadosCliente(nome="Teste"), info)
    assert os.path.exists(caminho)
    assert os.path.getsize(caminho) > 1000


def test_gerar_pdf_caminho_invalido(tmp_path):
    with pytest.raises(ValueError):
        gerar_pdf(str(tmp_path / "x.txt"), DadosCliente(), [])
