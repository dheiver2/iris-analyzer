"""Testes do backend web (FastAPI). Usam TestClient (offline)."""
import cv2
import numpy as np
import pytest

try:
    from fastapi.testclient import TestClient

    from iris_analyzer.server import _b64, _decodificar, app
    _OK = True
except Exception:
    _OK = False

pytestmark = pytest.mark.skipif(not _OK, reason="FastAPI/cliente indisponível")


def test_b64_e_decodificar_roundtrip():
    img = np.full((20, 20, 3), 128, np.uint8)
    s = _b64(img)
    assert s.startswith("data:image/jpeg;base64,")
    ok, buf = cv2.imencode(".jpg", img)
    assert _decodificar(buf.tobytes()) is not None


def test_index_serve_html():
    c = TestClient(app)
    r = c.get("/")
    assert r.status_code == 200
    assert "IRIS ANALYZER" in r.text


def test_analisar_imagem_invalida():
    c = TestClient(app)
    r = c.post("/analisar", files={"imagem": ("x.jpg", b"naoeimagem", "image/jpeg")})
    assert r.status_code == 400


def test_analisar_sem_olho():
    c = TestClient(app)
    img = np.full((120, 120, 3), 200, np.uint8)
    ok, buf = cv2.imencode(".jpg", img)
    r = c.post("/analisar", files={"imagem": ("x.jpg", buf.tobytes(), "image/jpeg")})
    assert r.status_code == 200
    assert r.json()["ok"] is False
