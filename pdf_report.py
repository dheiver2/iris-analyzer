"""Geracao de laudo (relatorio) em PDF da analise de iris.

IMPORTANTE: o PDF e identificado como RELATORIO DE BEM-ESTAR / ANALISE DE
IMAGEM, NAO como laudo medico ou diagnostico. Iridologia nao tem validacao
cientifica como metodo diagnostico.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


MARCA = colors.HexColor("#E94A12")   # laranja (identidade visual)
CREME = colors.HexColor("#FBF6EF")
CINZA = colors.HexColor("#555555")


@dataclass
class DadosCliente:
    nome: str = ""
    idade: str = ""
    data: str = ""
    profissional: str = ""
    observacoes: str = ""


def _estilos():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("Titulo", parent=s["Title"], textColor=MARCA, fontSize=20))
    s.add(ParagraphStyle("Sub", parent=s["Normal"], textColor=CINZA, fontSize=9))
    s.add(ParagraphStyle("H2", parent=s["Heading2"], textColor=MARCA, fontSize=13))
    s.add(ParagraphStyle("Disc", parent=s["Normal"], textColor=colors.HexColor("#8a4b00"),
                         fontSize=8, leading=11))
    s.add(ParagraphStyle("Cel", parent=s["Normal"], fontSize=9, leading=12))
    return s


def gerar_pdf(
    caminho_pdf: str,
    cliente: DadosCliente,
    olhos_info: list[dict],
    imagem_anotada: str | None = None,
) -> str:
    """olhos_info: lista de dicts com chaves: lado, cor, trama, textura, nitidez,
    reflexo, qualidade, zoom_path, daugman_path."""
    if not caminho_pdf or not str(caminho_pdf).lower().endswith(".pdf"):
        raise ValueError(f"caminho_pdf deve terminar em .pdf: {caminho_pdf!r}.")
    if not isinstance(olhos_info, list):
        raise TypeError(f"olhos_info deve ser list, recebido {type(olhos_info)!r}.")
    pasta = os.path.dirname(os.path.abspath(caminho_pdf))
    if not os.path.isdir(pasta):
        raise FileNotFoundError(f"Pasta de destino inexistente: {pasta}")
    s = _estilos()
    doc = SimpleDocTemplate(
        caminho_pdf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
    )
    el = []

    el.append(Paragraph("Relatório de Análise de Íris", s["Titulo"]))
    el.append(Paragraph("Análise de imagem para bem-estar e autoconhecimento", s["Sub"]))
    el.append(Spacer(1, 8 * mm))

    # Dados do cliente
    dados = [
        ["Nome:", cliente.nome or "—", "Data:", cliente.data or "—"],
        ["Idade:", cliente.idade or "—", "Profissional:", cliente.profissional or "—"],
    ]
    t = Table(dados, colWidths=[22 * mm, 60 * mm, 30 * mm, 50 * mm])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), MARCA),
        ("TEXTCOLOR", (2, 0), (2, -1), MARCA),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    el.append(t)
    el.append(Spacer(1, 6 * mm))

    if imagem_anotada and os.path.exists(imagem_anotada):
        el.append(Paragraph("Imagem capturada", s["H2"]))
        el.append(Image(imagem_anotada, width=150 * mm, height=84 * mm,
                        kind="proportional"))
        el.append(Spacer(1, 4 * mm))

    # Por olho
    for o in olhos_info:
        el.append(Paragraph(f"Olho {o['lado']}", s["H2"]))
        imgs = []
        row = []
        for chave, rotulo in (("zoom_path", "Íris (zoom)"),
                              ("daugman_path", "Mapa de calor das marcas")):
            p = o.get(chave)
            if p and os.path.exists(p):
                row.append(Image(p, width=70 * mm, height=42 * mm, kind="proportional"))
            else:
                row.append(Paragraph("—", s["Cel"]))
        imgs.append(row)
        ti = Table(imgs, colWidths=[75 * mm, 75 * mm])
        el.append(ti)

        # Mapa de zonas (iridologia) + zonas em destaque
        mp = o.get("mapa_path")
        if mp and os.path.exists(mp):
            el.append(Spacer(1, 2 * mm))
            zonas_txt = "<br/>".join(o.get("zonas", [])) or "—"
            linha = Table(
                [[Image(mp, width=55 * mm, height=55 * mm, kind="proportional"),
                  Paragraph("<b>Zonas em destaque</b> (mapa tradicional de "
                            "iridologia, sem valor diagnóstico):<br/><br/>"
                            + zonas_txt, s["Cel"])]],
                colWidths=[60 * mm, 90 * mm])
            linha.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
            el.append(linha)
            el.append(Spacer(1, 2 * mm))

        carac = [
            ["Cor predominante", o.get("cor", "—")],
            ["Trama de fibras", o.get("trama", "—")],
            ["Textura", o.get("textura", "—")],
            ["Nitidez do foco", str(o.get("nitidez", "—"))],
            ["Reflexo de luz", f"{o.get('reflexo', '—')}%"],
            ["Qualidade da imagem", "Boa" if o.get("qualidade") else "Baixa"],
        ]
        tc = Table(carac, colWidths=[55 * mm, 95 * mm])
        tc.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("BACKGROUND", (0, 0), (0, -1), CREME),
            ("TEXTCOLOR", (0, 0), (0, -1), CINZA),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        el.append(Spacer(1, 2 * mm))
        el.append(tc)
        el.append(Spacer(1, 6 * mm))

    if cliente.observacoes:
        el.append(Paragraph("Observações", s["H2"]))
        el.append(Paragraph(cliente.observacoes.replace("\n", "<br/>"), s["Cel"]))
        el.append(Spacer(1, 6 * mm))

    # Disclaimer obrigatorio
    el.append(Spacer(1, 4 * mm))
    disc = (
        "<b>AVISO IMPORTANTE:</b> Este relatório descreve apenas características "
        "de imagem da íris (cor, textura, padrões) obtidas por visão "
        "computacional. <b>NÃO constitui diagnóstico médico.</b> A iridologia não "
        "possui validação científica como método de diagnóstico de doenças. "
        "Os resultados têm finalidade educacional e de bem-estar e não substituem "
        "avaliação de um profissional de saúde habilitado. Em caso de sintomas ou "
        "preocupações de saúde, procure atendimento médico."
    )
    box = Table([[Paragraph(disc, s["Disc"])]], colWidths=[164 * mm])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF6E6")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#E0A030")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    el.append(box)

    doc.build(el)
    return os.path.abspath(caminho_pdf)
