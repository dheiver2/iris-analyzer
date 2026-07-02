"""Backend web (FastAPI) do Iris Analyzer.

Tecnologia de mercado que elimina a classe de bugs do app desktop em macOS
(permissao de camera/TCC, app nao-assinado, arquitetura, Terminal): a CAMERA
fica no NAVEGADOR (getUserMedia) e o Python so analisa a imagem recebida.
Reaproveita todos os modulos de analise existentes.

Nenhuma imagem ou dado de analise e persistido no servidor: cada requisicao
e processada em memoria/arquivos temporarios que sao apagados antes da
resposta ser enviada. Veja SECURITY.md para detalhes de privacidade.

    python3 run_web.py      # inicia o servidor e abre o navegador
"""
from __future__ import annotations

import base64
import io
import logging
import os
import shutil
import tempfile
import threading
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from . import config
from .iris_advanced import (
    detectar_colarete,
    detectar_pupila,
    detectar_pupila_centro,
    heatmap_iris,
    refinar_iris,
)
from .iris_features import extrair_features
from .iris_map import analisar_zonas, render_mapa, top_zonas
from .iris_metrics import comparar_olhos, medir_biometria, validar_plausibilidade
from .iris_quality import avaliar_qualidade
from .iris_segmentation import criar_landmarker, detectar_face
from .pdf_report import DadosCliente, gerar_pdf

log = logging.getLogger("iris_analyzer.server")

app = FastAPI(title="Iris Analyzer")

if config.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

_WEB = Path(__file__).resolve().parent.parent / "web"
_landmarker = None
_lock = threading.Lock()


@app.exception_handler(Exception)
async def _erro_inesperado(request: Request, exc: Exception):
    """Nunca vaza stack trace/detalhes internos ao cliente; loga no servidor."""
    log.exception("Erro nao tratado em %s", request.url.path)
    return JSONResponse({"ok": False, "erro": "Erro interno ao processar a imagem."}, status_code=500)


def _lm():
    global _landmarker
    if _landmarker is None:
        _landmarker = criar_landmarker()
    return _landmarker


def _b64(img_bgr) -> str:
    ok, buf = cv2.imencode(".jpg", img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return "data:image/jpeg;base64," + base64.b64encode(buf).decode() if ok else ""


def _decodificar(dados: bytes):
    arr = np.frombuffer(dados, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


async def _ler_imagem(imagem: UploadFile) -> bytes | None:
    """Le o upload aplicando limite de tamanho e validando o tipo declarado.

    Retorna None (e o caller deve responder 400) se invalido/grande demais.
    """
    if imagem.content_type and not imagem.content_type.startswith("image/"):
        return None
    dados = await imagem.read(config.MAX_UPLOAD_BYTES + 1)
    if len(dados) > config.MAX_UPLOAD_BYTES:
        return None
    return dados


def _analisar(frame):
    """Roda toda a analise sobre um frame BGR e retorna (dict, olhos, feats, frame)."""
    with _lock:
        olhos, pontos = detectar_face(frame, _lm())
    if not olhos:
        return {"ok": False, "erro": "Nenhum olho detectado."}, [], [], frame

    feats = [extrair_features(frame, o.centro, o.raio_iris, o.raio_pupila) for o in olhos]
    for o in olhos:
        try:
            o.raio_iris = refinar_iris(frame, o.centro, o.raio_iris)
        except Exception:
            log.warning("Falha ao refinar borda da iris (Daugman); usando raio original.", exc_info=True)

    olhos_json, qs, bios, concentr = [], [], [], []
    for o, f in zip(olhos, feats):
        rp = detectar_pupila(frame, o.centro, o.raio_iris)
        q = avaliar_qualidade(frame, o, rp)
        bio = medir_biometria(o, rp)
        qs.append(q); bios.append(bio)
        try:
            pcx, pcy, _ = detectar_pupila_centro(frame, o.centro, o.raio_iris)
            off = ((pcx - o.centro[0]) ** 2 + (pcy - o.centro[1]) ** 2) ** 0.5
            concentr.append(off / o.raio_iris if o.raio_iris else 0.0)
        except Exception:
            log.warning("Falha ao estimar concentricidade da pupila.", exc_info=True)
            concentr.append(0.0)
        try:
            colarete = detectar_colarete(frame, o.centro, o.raio_iris, rp)
        except Exception:
            log.warning("Falha ao detectar colarete.", exc_info=True)
            colarete = 0.0

        zonas = analisar_zonas(frame, o.centro, o.raio_iris, rp, o.lado, contorno=o.contorno)
        # recorte da iris
        r = o.raio_iris * 1.35
        h, w = frame.shape[:2]
        x0, y0 = max(0, int(o.centro[0] - r)), max(0, int(o.centro[1] - r))
        x1, y1 = min(w, int(o.centro[0] + r)), min(h, int(o.centro[1] + r))
        zoom = cv2.resize(frame[y0:y1, x0:x1], (220, 220)) if (x1 > x0 and y1 > y0) else frame
        tops = top_zonas(zonas, 5)
        olhos_json.append({
            "lado": o.lado,
            "cor": f.cor_predominante,
            "trama": "densa" if f.densidade_fibras > 0.10 else "lisa",
            "constituicao": "tensa" if f.densidade_fibras > 0.10 else "relaxada",
            "textura": "uniforme" if f.glcm_homogeneidade > 0.5 else "com variações",
            "qualidade": f"{q.score:.0f}/100 ({q.nivel})",
            "fatores": (f"foco {q.foco:.2f} · oclusão {q.oclusao*100:.0f}% · "
                        f"reflexo {q.reflexo*100:.1f}% · ângulo {q.angulo:.2f} · "
                        f"abertura {q.abertura:.2f}"),
            "biometria": (f"íris ~{bio.diametro_iris_mm:.1f} mm · pupila "
                          f"~{bio.diametro_pupila_mm:.1f} mm · razão {bio.razao_pupilar:.2f} "
                          f"({bio.dilatacao})"
                          + (f" · colarete ~{colarete*100:.0f}%" if colarete > 0 else "")),
            "zonas": [f"{t.indice+1}. {t.nome} ({t.nivel})" for t in tops] or
                     ["Nenhuma zona com marca significativa."],
            "zoom": _b64(zoom),
            "heatmap": _b64(cv2.resize(heatmap_iris(frame, o.centro, o.raio_iris, rp), (220, 220))),
            "mapa": _b64(render_mapa(zonas, 220, f"Olho {o.lado}")),
        })

    val = validar_plausibilidade(olhos, qs, bios, concentr)
    comp = comparar_olhos(olhos, feats)
    return ({
        "ok": True,
        "confianca": f"{val.confianca:.0f}",
        "avisos": val.avisos,
        "comparacao": (f"Simetria das íris {comp.simetria_raio*100:.0f}% · {comp.nota}"
                       if comp else ""),
        "olhos": olhos_json,
    }, olhos, feats, frame)


@app.get("/", response_class=HTMLResponse)
def index():
    return (_WEB / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health():
    return {"ok": True, "version": __import__("iris_analyzer").__version__}


@app.post("/analisar")
async def analisar(imagem: UploadFile = File(...)):
    dados = await _ler_imagem(imagem)
    if dados is None:
        return JSONResponse({"ok": False, "erro": "Imagem invalida ou maior que o limite permitido."},
                             status_code=400)
    frame = _decodificar(dados)
    if frame is None:
        return JSONResponse({"ok": False, "erro": "Imagem inválida."}, status_code=400)
    resultado, *_ = _analisar(frame)
    return JSONResponse(resultado)


@app.post("/laudo")
async def laudo(imagem: UploadFile = File(...), nome: str = Form(""),
                idade: str = Form(""), profissional: str = Form(""),
                data: str = Form(""), observacoes: str = Form("")):
    dados = await _ler_imagem(imagem)
    if dados is None:
        return JSONResponse({"erro": "Imagem invalida ou maior que o limite permitido."}, status_code=400)
    frame = _decodificar(dados)
    if frame is None:
        return JSONResponse({"erro": "Imagem inválida."}, status_code=400)
    res, olhos, feats, frame = _analisar(frame)
    if not res.get("ok"):
        return JSONResponse(res, status_code=400)

    base = tempfile.mkdtemp(prefix="iris_laudo_")
    try:
        olhos_info = []
        for o, _f, oj in zip(olhos, feats, res["olhos"]):
            rp = detectar_pupila(frame, o.centro, o.raio_iris)
            zoom_p = os.path.join(base, f"zoom_{o.lado}.jpg")
            r = o.raio_iris * 1.6
            h, w = frame.shape[:2]
            x0, y0 = max(0, int(o.centro[0]-r)), max(0, int(o.centro[1]-r))
            x1, y1 = min(w, int(o.centro[0]+r)), min(h, int(o.centro[1]+r))
            cv2.imwrite(zoom_p, cv2.resize(frame[y0:y1, x0:x1], (400, 400)))
            heat_p = os.path.join(base, f"heat_{o.lado}.jpg")
            cv2.imwrite(heat_p, heatmap_iris(frame, o.centro, o.raio_iris, rp))
            zonas = analisar_zonas(frame, o.centro, o.raio_iris, rp, o.lado, contorno=o.contorno)
            mapa_p = os.path.join(base, f"mapa_{o.lado}.jpg")
            cv2.imwrite(mapa_p, render_mapa(zonas, 360, f"Olho {o.lado}"))
            olhos_info.append({
                "lado": o.lado, "cor": oj["cor"], "trama": oj["trama"],
                "textura": oj["textura"], "nitidez": "—", "reflexo": "—",
                "qualidade": True, "zoom_path": zoom_p, "daugman_path": heat_p,
                "mapa_path": mapa_p, "zonas": oj["zonas"],
                "qualidade_score": oj["qualidade"], "biometria": oj["biometria"],
                "constituicao": oj["constituicao"],
            })
        resumo = {"confianca": f"{res['confianca']}/100", "avisos": res["avisos"],
                  "comparacao": res["comparacao"]}
        pdf_p = os.path.join(base, "laudo.pdf")
        gerar_pdf(pdf_p, DadosCliente(nome=nome, idade=idade, data=data,
                                      profissional=profissional, observacoes=observacoes),
                  olhos_info, None, resumo)
        pdf_bytes = Path(pdf_p).read_bytes()
    finally:
        # Nenhum arquivo do laudo/imagem fica retido no servidor apos a resposta.
        shutil.rmtree(base, ignore_errors=True)

    return StreamingResponse(io.BytesIO(pdf_bytes),
                             media_type="application/pdf",
                             headers={"Content-Disposition": "attachment; filename=laudo.pdf"})
