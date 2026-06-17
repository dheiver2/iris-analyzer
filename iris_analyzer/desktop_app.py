"""Iris Analyzer - Aplicativo desktop profissional (PyQt6).

Ferramenta de ANALISE DE IMAGEM DA IRIS para BEM-ESTAR e autoconhecimento.
NAO e dispositivo medico e NAO faz diagnostico. A iridologia nao tem validacao
cientifica como metodo diagnostico.

Recursos:
  - Camera ao vivo com deteccao da iris (MediaPipe)
  - Captura e analise (cor Lab, Gabor, LBP, GLCM, Daugman, qualidade)
  - Cadastro do cliente e geracao de laudo em PDF com a marca
"""
from __future__ import annotations

import os
import sys
import time

import cv2
import numpy as np
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QLineEdit, QTextEdit, QFrame, QScrollArea,
    QFileDialog, QMessageBox, QSizePolicy, QCheckBox,
)

import logging

from . import config
from .iris_segmentation import detectar_face, criar_landmarker, Olho
from .iris_features import extrair_features
from .iris_map import analisar_zonas, render_mapa, top_zonas, resumo_qualidade
from .captura_guiada import avaliar, desenhar_guia, desenhar_malha, FRAMES_ESTAVEL
from .iris_advanced import (
    detectar_pupila, detectar_pupila_centro, detectar_colarete,
    heatmap_iris, refinar_iris,
)
from .iris_quality import avaliar_qualidade
from .iris_metrics import (
    medir_biometria, validar_plausibilidade, comparar_olhos,
)
from .pdf_report import gerar_pdf, DadosCliente

# Paleta
# Paleta minimalista — preto real, monocromatica, acento branco.
BG = "#0b0b0c"        # fundo principal
CARD = "#121214"      # cartoes / painel
BORDER = "#222226"    # bordas sutis
TEXTO = "#ededed"     # texto primario
MUTED = "#7a7a7e"     # texto secundario
ACCENT = "#ffffff"    # acento (branco)
# compat com nomes antigos usados no codigo
LARANJA = ACCENT
ESCURO = "#141416"
PAINEL = CARD


def bgr_para_qpixmap(frame: np.ndarray) -> QPixmap:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, _ = rgb.shape
    img = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(img.copy())


def _interp(origem: int, destino: int) -> int:
    """INTER_AREA ao reduzir (mais nitido), INTER_CUBIC ao ampliar."""
    return cv2.INTER_AREA if origem >= destino else cv2.INTER_CUBIC


_CAP = f"color:{MUTED};font-size:10px;letter-spacing:0.3px;"


def _campo(label_txt):
    box = QVBoxLayout(); box.setSpacing(4)
    lab = QLabel(label_txt.upper())
    lab.setStyleSheet(f"color:{MUTED};font-size:10px;letter-spacing:0.5px;")
    inp = QLineEdit()
    inp.setStyleSheet(
        f"background:{ESCURO};color:{TEXTO};border:1px solid {BORDER};"
        f"border-radius:8px;padding:8px;selection-background-color:#333;")
    box.addWidget(lab)
    box.addWidget(inp)
    return box, inp


class CardOlho(QFrame):
    """Cartao de resultado de um olho: zoom + Daugman + metricas."""
    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            f"CardOlho{{background:{CARD};border:1px solid {BORDER};border-radius:14px;}}")
        lay = QVBoxLayout(self); lay.setContentsMargins(18, 16, 18, 16); lay.setSpacing(12)
        self.titulo = QLabel("—")
        self.titulo.setStyleSheet(
            f"color:{TEXTO};font-size:13px;font-weight:600;letter-spacing:1px;")
        lay.addWidget(self.titulo)

        imgs = QHBoxLayout(); imgs.setSpacing(14)
        self.zoom = QLabel(); self.zoom.setFixedSize(150, 150)
        self.zoom.setStyleSheet(f"background:#000;border:1px solid {BORDER};border-radius:8px;")
        self.zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Mapa de zonas (iridologia)
        self.mapa = QLabel(); self.mapa.setFixedSize(170, 170)
        self.mapa.setStyleSheet(f"background:#000;border:1px solid {BORDER};border-radius:8px;")
        self.mapa.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col = QVBoxLayout(); col.setSpacing(5)
        cap_z = QLabel("ÍRIS (ZOOM)"); cap_z.setStyleSheet(_CAP)
        col.addWidget(self.zoom); col.addWidget(cap_z)
        self.heat = QLabel(); self.heat.setFixedSize(150, 150)
        self.heat.setStyleSheet(f"background:#000;border:1px solid {BORDER};border-radius:8px;")
        self.heat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cap_h = QLabel("MAPA DE CALOR"); cap_h.setStyleSheet(_CAP)
        colh = QVBoxLayout(); colh.setSpacing(5)
        colh.addWidget(self.heat); colh.addWidget(cap_h)
        colm = QVBoxLayout(); colm.setSpacing(5)
        cap_m = QLabel("MAPA DE ZONAS"); cap_m.setStyleSheet(_CAP)
        colm.addWidget(self.mapa); colm.addWidget(cap_m)
        imgs.addLayout(col); imgs.addLayout(colh); imgs.addLayout(colm); imgs.addStretch()
        lay.addLayout(imgs)

        # Zonas mais marcadas (referencia tradicional)
        self.zonas_lbl = QLabel("Aguardando captura…")
        self.zonas_lbl.setStyleSheet(f"color:{TEXTO};font-size:12px;")
        self.zonas_lbl.setWordWrap(True)
        lay.addWidget(self.zonas_lbl)

        self.metricas = QLabel("")
        self.metricas.setStyleSheet(f"color:{MUTED};font-size:11px;")
        self.metricas.setWordWrap(True)
        lay.addWidget(self.metricas)

    def atualizar(self, olho: Olho, f, frame, rp, q, bio):
        self.titulo.setText(f"OLHO {olho.lado.upper()}")
        # zoom apertado na iris (1.35x do raio)
        cx, cy = olho.centro
        r = olho.raio_iris * 1.35
        h, w = frame.shape[:2]
        x0, y0 = max(0, int(cx - r)), max(0, int(cy - r))
        x1, y1 = min(w, int(cx + r)), min(h, int(cy + r))
        crop = frame[y0:y1, x0:x1]
        if crop.size:
            crop = cv2.resize(crop, (150, 150), interpolation=_interp(crop.shape[0], 150))
            self.zoom.setPixmap(bgr_para_qpixmap(crop))

        # mapa de calor das marcas (lacunas + fibras)
        hm = heatmap_iris(frame, olho.centro, olho.raio_iris, rp)
        hm = cv2.resize(hm, (150, 150), interpolation=_interp(hm.shape[0], 150))
        self.heat.setPixmap(bgr_para_qpixmap(hm))

        # mapa de zonas (iridologia)
        zonas = analisar_zonas(frame, olho.centro, olho.raio_iris,
                               rp, olho.lado, contorno=olho.contorno)
        mapa = render_mapa(zonas, 170)
        self.mapa.setPixmap(bgr_para_qpixmap(mapa))

        tops = top_zonas(zonas, 4)
        if tops:
            linhas = "".join(
                f"<tr><td>●</td><td>&nbsp;<b>{t.indice+1}</b>&nbsp;</td>"
                f"<td>{t.nome}</td><td>&nbsp;<i>({t.nivel})</i></td></tr>"
                for t in tops
            )
            corpo = f"<table>{linhas}</table>"
        else:
            corpo = "<br>✔ Nenhuma zona com marca significativa."
        aviso = resumo_qualidade(zonas)
        if aviso:
            corpo += f"<br><span style='color:#f0c060'>⚠ {aviso}</span>"
        self.zonas_lbl.setText(
            "<b>Zonas em destaque</b> (mapa tradicional, sem valor diagnóstico)."
            "<br><span style='color:#888;font-size:10px'>verde=limpo · "
            "amarelo/vermelho=marca · cinza=coberto</span>"
            + corpo
        )

        trama = "densa" if f.densidade_fibras > 0.10 else "lisa"
        textura = "uniforme" if f.glcm_homogeneidade > 0.5 else "com variações"
        constituicao = "tensa" if f.densidade_fibras > 0.10 else "relaxada"
        try:
            colarete = detectar_colarete(frame, olho.centro, olho.raio_iris, rp)
        except Exception:
            colarete = 0.0
        col_txt = (f" · colarete ~{colarete*100:.0f}% do raio" if colarete > 0 else "")
        cor_q = {"ruim": "#c25", "regular": "#c84", "boa": "#7a9",
                 "excelente": "#5b8"}.get(q.nivel, MUTED)
        self.metricas.setText(
            f"<span style='color:{cor_q};font-weight:600'>Qualidade {q.score:.0f}/100 "
            f"({q.nivel})</span><br>"
            f"<span style='color:{MUTED};font-size:10px'>foco {q.foco:.2f} · "
            f"oclusão {q.oclusao*100:.0f}% · reflexo {q.reflexo*100:.1f}% · "
            f"ângulo {q.angulo:.2f} · abertura {q.abertura:.2f}</span><br>"
            f"<b>Biometria:</b> íris ~{bio.diametro_iris_mm:.1f} mm · "
            f"pupila ~{bio.diametro_pupila_mm:.1f} mm · razão {bio.razao_pupilar:.2f} "
            f"({bio.dilatacao}){col_txt}<br>"
            f"<b>Cor:</b> {f.cor_predominante} · <b>Trama:</b> {trama} · "
            f"<b>Constituição:</b> {constituicao} · <b>Textura:</b> {textura}"
        )
        self._f, self._olho, self._zonas = f, olho, zonas


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Iris Analyzer — Análise de Íris (Bem-estar)")
        self.resize(1280, 820)
        self.setStyleSheet(f"QMainWindow,QWidget{{background:{BG};}}")

        self._frame_atual = None
        self._olhos = []
        self._feats = []
        self._pontos = None
        self._capturado = None  # (frame, olhos, feats)

        central = QWidget(); self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        # ---- Header ----
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet(
            f"background:{BG};border-bottom:1px solid {BORDER};")
        hl = QHBoxLayout(header); hl.setContentsMargins(28, 0, 28, 0)
        logo = QLabel("●  IRIS ANALYZER")
        logo.setStyleSheet(
            f"color:{TEXTO};font-size:16px;font-weight:700;letter-spacing:2px;")
        sub = QLabel("análise de imagem da íris · bem-estar")
        sub.setStyleSheet(f"color:{MUTED};font-size:11px;letter-spacing:0.5px;")
        hl.addWidget(logo); hl.addSpacing(14); hl.addWidget(sub); hl.addStretch()
        root.addWidget(header)

        # ---- Corpo ----
        corpo = QHBoxLayout()
        corpo.setContentsMargins(28, 24, 28, 16); corpo.setSpacing(28)
        root.addLayout(corpo, 1)

        # Esquerda: camera + botoes + formulario
        esq = QVBoxLayout(); esq.setSpacing(14)
        self.video = QLabel("Iniciando câmera…")
        self.video.setFixedSize(config.PREVIEW_W, config.PREVIEW_H)
        self.video.setStyleSheet(
            f"background:#000;border:1px solid {BORDER};border-radius:12px;color:{MUTED};")
        self.video.setAlignment(Qt.AlignmentFlag.AlignCenter)
        esq.addWidget(self.video)

        botoes = QHBoxLayout(); botoes.setSpacing(12)
        self.btn_capt = QPushButton("Capturar e analisar")
        self.btn_capt.clicked.connect(self.capturar)
        self.btn_pdf = QPushButton("Gerar laudo PDF")
        self.btn_pdf.clicked.connect(self.gerar_laudo)
        self.btn_pdf.setEnabled(False)
        # primario = branco preenchido; secundario = contorno
        self.btn_capt.setStyleSheet(
            f"QPushButton{{background:{ACCENT};color:#000;font-weight:600;font-size:13px;"
            f"border:none;border-radius:10px;padding:12px;}}"
            f"QPushButton:hover{{background:#d8d8d8;}}")
        self.btn_pdf.setStyleSheet(
            f"QPushButton{{background:transparent;color:{TEXTO};font-weight:600;font-size:13px;"
            f"border:1px solid {BORDER};border-radius:10px;padding:12px;}}"
            f"QPushButton:hover{{border-color:#444;}}"
            f"QPushButton:disabled{{color:#444;border-color:#1a1a1c;}}")
        for b in (self.btn_capt, self.btn_pdf):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
        botoes.addWidget(self.btn_capt); botoes.addWidget(self.btn_pdf)
        esq.addLayout(botoes)

        self.chk_auto = QCheckBox("Captura guiada · auto-disparo quando a imagem está boa")
        self.chk_auto.setChecked(True)
        self.chk_auto.setStyleSheet(
            f"QCheckBox{{color:{MUTED};font-size:12px;padding:2px;}}"
            f"QCheckBox::indicator{{width:16px;height:16px;border:1px solid {BORDER};"
            f"border-radius:4px;background:{ESCURO};}}"
            f"QCheckBox::indicator:checked{{background:{ACCENT};border-color:{ACCENT};}}")
        esq.addWidget(self.chk_auto)

        form = QGridLayout(); form.setHorizontalSpacing(14); form.setVerticalSpacing(12)
        (b1, self.in_nome) = _campo("Nome do cliente")
        (b2, self.in_idade) = _campo("Idade")
        (b3, self.in_prof) = _campo("Profissional responsável")
        (b4, self.in_data) = _campo("Data")
        self.in_data.setText(time.strftime("%d/%m/%Y"))
        form.addLayout(b1, 0, 0); form.addLayout(b2, 0, 1)
        form.addLayout(b3, 1, 0); form.addLayout(b4, 1, 1)
        esq.addLayout(form)
        lab_obs = QLabel("OBSERVAÇÕES")
        lab_obs.setStyleSheet(f"color:{MUTED};font-size:10px;letter-spacing:0.5px;")
        esq.addWidget(lab_obs)
        self.in_obs = QTextEdit(); self.in_obs.setFixedHeight(60)
        self.in_obs.setStyleSheet(
            f"background:{ESCURO};color:{TEXTO};border:1px solid {BORDER};border-radius:8px;"
            f"padding:4px;")
        esq.addWidget(self.in_obs)
        esq.addStretch()
        corpo.addLayout(esq)

        # Direita: resultados
        dir_box = QVBoxLayout(); dir_box.setSpacing(14)
        titdir = QLabel("RESULTADOS")
        titdir.setStyleSheet(
            f"color:{TEXTO};font-size:12px;font-weight:600;letter-spacing:2px;")
        dir_box.addWidget(titdir)

        self.resumo_lbl = QLabel("Capture para ver o resumo da análise.")
        self.resumo_lbl.setWordWrap(True)
        self.resumo_lbl.setStyleSheet(
            f"background:{CARD};border:1px solid {BORDER};border-radius:12px;"
            f"padding:12px;color:{TEXTO};font-size:12px;")
        dir_box.addWidget(self.resumo_lbl)
        self.card_dir = CardOlho()
        self.card_esq = CardOlho()
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            f"QScrollArea{{border:none;background:transparent;}}"
            f"QScrollBar:vertical{{background:transparent;width:8px;margin:0;}}"
            f"QScrollBar::handle:vertical{{background:{BORDER};border-radius:4px;min-height:30px;}}"
            f"QScrollBar::add-line,QScrollBar::sub-line{{height:0;}}")
        cont = QWidget(); cont.setStyleSheet("background:transparent;")
        cl = QVBoxLayout(cont); cl.setSpacing(16); cl.setContentsMargins(0, 0, 6, 0)
        cl.addWidget(self.card_dir); cl.addWidget(self.card_esq); cl.addStretch()
        scroll.setWidget(cont)
        dir_box.addWidget(scroll, 1)
        corpo.addLayout(dir_box, 1)

        # ---- Rodape disclaimer (minimalista) ----
        disc = QLabel(
            "Ferramenta de bem-estar e análise de imagem. Não é diagnóstico médico — "
            "a iridologia não tem validação científica para diagnóstico.")
        disc.setWordWrap(True)
        disc.setStyleSheet(
            f"background:{BG};color:{MUTED};font-size:10px;padding:10px 28px;"
            f"border-top:1px solid {BORDER};letter-spacing:0.3px;")
        root.addWidget(disc)

        # Camera (na main thread via QTimer — necessario no macOS).
        # Abertura preguicosa no 1o tick, com o event loop ja rodando, para a
        # autorizacao do AVFoundation funcionar.
        self._landmarker = criar_landmarker()
        self._ultimo_analise = 0.0
        self._estavel = 0           # frames consecutivos com qualidade boa
        self._cooldown = 0          # bloqueia auto-disparo apos capturar
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)  # ~30 fps de exibicao

    # ---- Loop de camera ----
    def _tick(self):
        # Blindagem: PyQt6 encerra o app a qualquer excecao nao tratada num
        # slot/timer. Capturamos tudo aqui para o app nunca fechar sozinho.
        try:
            self._tick_inner()
        except Exception:
            logging.getLogger("iris_analyzer").exception("Erro no loop de camera")

    def _tick_inner(self):
        # (Re)abre a camera periodicamente enquanto nao estiver pronta. Isso
        # cobre o caso em que a 1a tentativa falha porque a permissao de camera
        # ainda esta pendente — assim que o usuario autoriza, conecta sozinho.
        if self.cap is None or not self.cap.isOpened():
            agora0 = time.time()
            if agora0 - getattr(self, "_ultimo_open", 0) < 1.2:
                return
            self._ultimo_open = agora0
            if self.cap is not None:
                self.cap.release()
            # No macOS, usa o backend nativo (AVFoundation) diretamente —
            # evita a tentativa de FFMPEG e lida melhor com a permissao.
            if sys.platform == "darwin":
                self.cap = cv2.VideoCapture(config.CAMERA_INDEX, cv2.CAP_AVFOUNDATION)
            else:
                self.cap = cv2.VideoCapture(config.CAMERA_INDEX)
            if not self.cap.isOpened():
                self.video.setText(
                    "Conectando à câmera…\n\nSe pedir permissão, autorize.\n"
                    "Ou habilite em Ajustes › Privacidade e Segurança › Câmera.")
                return
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
            w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            logging.getLogger("iris_analyzer").info("Câmera em %dx%d", int(w), int(h))
        ok, frame = self.cap.read()
        if not ok:
            # Frame perdido e NORMAL — apenas ignora. So reabre se falhar muitas
            # vezes seguidas (camera realmente caiu).
            self._falhas = getattr(self, "_falhas", 0) + 1
            if self._falhas > 30:
                self._falhas = 0
                self.cap.release()
            return
        self._falhas = 0
        frame = cv2.flip(frame, 1)
        agora = time.time()
        if agora - self._ultimo_analise > 0.12:  # analisa ~8 fps
            self._ultimo_analise = agora
            try:
                olhos, pontos = detectar_face(frame, self._landmarker)
                feats = [extrair_features(frame, o.centro, o.raio_iris,
                                          o.raio_pupila) for o in olhos]
            except Exception:
                olhos, feats, pontos = [], [], None
            self._olhos, self._feats, self._pontos = olhos, feats, pontos
        self._mostrar(frame, self._olhos, self._feats)

    def _mostrar(self, frame, olhos, feats):
        self._frame_atual = frame
        disp = frame.copy()
        # malha facial (face mesh)
        desenhar_malha(disp, self._pontos)
        for o, f in zip(olhos, feats):
            c = (int(o.centro[0]), int(o.centro[1]))
            cor = (0, 255, 0) if f.qualidade_ok else (0, 165, 255)
            cv2.circle(disp, c, int(o.raio_iris), cor, 2)
            cv2.circle(disp, c, 2, (255, 0, 0), 2)

        # Captura guiada
        if self._cooldown > 0:
            self._cooldown -= 1
        if self.chk_auto.isChecked():
            criterios, ok = avaliar(frame, olhos, feats)
            if ok and self._cooldown == 0:
                self._estavel += 1
            else:
                self._estavel = 0
            desenhar_guia(disp, criterios, ok, self._estavel / FRAMES_ESTAVEL)
            if self._estavel >= FRAMES_ESTAVEL:
                self._estavel = 0
                self._cooldown = 60
                self.capturar()

        self.video.setPixmap(bgr_para_qpixmap(disp).scaled(
            config.PREVIEW_W, config.PREVIEW_H, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))

    def capturar(self):
        if self._frame_atual is None or not self._olhos:
            QMessageBox.warning(self, "Sem olhos detectados",
                                "Aproxime o rosto da câmera e tente novamente.")
            return
        try:
            self._capturado = (self._frame_atual.copy(), self._olhos, self._feats)
            frame, olhos, feats = self._capturado
            # Refino sub-pixel da borda da iris (Daugman) — so na captura
            for o in olhos:
                try:
                    o.raio_iris = refinar_iris(frame, o.centro, o.raio_iris)
                except Exception:
                    pass
            # Metricas por olho (pupila real, qualidade, biometria, concentricidade)
            rps, qs, bios, concentr = [], [], [], []
            for o in olhos:
                rp = detectar_pupila(frame, o.centro, o.raio_iris)
                rps.append(rp)
                qs.append(avaliar_qualidade(frame, o, rp))
                bios.append(medir_biometria(o, rp))
                try:
                    pcx, pcy, _ = detectar_pupila_centro(frame, o.centro, o.raio_iris)
                    off = ((pcx - o.centro[0]) ** 2 + (pcy - o.centro[1]) ** 2) ** 0.5
                    concentr.append(off / o.raio_iris if o.raio_iris else 0.0)
                except Exception:
                    concentr.append(0.0)
            cards = {"direito": self.card_dir, "esquerdo": self.card_esq}
            for o, f, rp, q, bio in zip(olhos, feats, rps, qs, bios):
                cards[o.lado].atualizar(o, f, frame, rp, q, bio)
            # Validacoes avancadas + comparacao entre olhos
            val = validar_plausibilidade(olhos, qs, bios, concentr)
            comp = comparar_olhos(olhos, feats)
            self._atualizar_resumo(val, comp, bios)
            self.btn_pdf.setEnabled(True)
        except Exception:
            logging.getLogger("iris_analyzer").exception("Erro ao capturar/analisar")
            QMessageBox.warning(self, "Falha na análise",
                                "Não foi possível analisar esta captura. Tente novamente.")

    def _atualizar_resumo(self, val, comp, bios):
        cor = "#5b8" if val.confianca >= 80 else "#7a9" if val.confianca >= 60 else "#c84"
        html = (f"<b>Índice de confiança da análise: "
                f"<span style='color:{cor}'>{val.confianca:.0f}/100</span></b>")
        if comp is not None:
            html += (f"<br><span style='color:{MUTED};font-size:11px'>"
                     f"Simetria das íris: {comp.simetria_raio*100:.0f}% · {comp.nota}</span>")
        if val.avisos:
            itens = "".join(f"<li>{a}</li>" for a in val.avisos)
            html += (f"<br><span style='color:#f0c060;font-size:11px'>"
                     f"Atenção:</span><ul style='margin:2px 0'>{itens}</ul>")
        else:
            html += "<br><span style='color:#5b8;font-size:11px'>✔ Sem alertas de plausibilidade.</span>"
        self.resumo_lbl.setText(html)

    def gerar_laudo(self):
        if not self._capturado:
            return
        frame, olhos, feats = self._capturado
        destino, _ = QFileDialog.getSaveFileName(
            self, "Salvar laudo", f"laudo_{time.strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF (*.pdf)")
        if not destino:
            return
        try:
            self._gerar_laudo_impl(destino, frame, olhos, feats)
        except Exception as e:
            logging.getLogger("iris_analyzer").exception("Erro ao gerar laudo")
            QMessageBox.critical(self, "Erro", f"Falha ao gerar o laudo:\n{e}")

    def _gerar_laudo_impl(self, destino, frame, olhos, feats):
        base = os.path.splitext(destino)[0]
        anot = frame.copy()
        olhos_info = []
        qs, bios = [], []
        for o, f in zip(olhos, feats):
            c = (int(o.centro[0]), int(o.centro[1]))
            cv2.circle(anot, c, int(o.raio_iris), (0, 255, 0), 2)
            # zoom (alta resolucao -> recorte grande, downscale nitido)
            r = o.raio_iris * 1.6
            h, w = frame.shape[:2]
            x0, y0 = max(0, int(c[0] - r)), max(0, int(c[1] - r))
            x1, y1 = min(w, int(c[0] + r)), min(h, int(c[1] + r))
            zoom_p = f"{base}_zoom_{o.lado}.jpg"
            zc = frame[y0:y1, x0:x1]
            cv2.imwrite(zoom_p, cv2.resize(zc, (400, 400), interpolation=_interp(zc.shape[0], 400)))
            rp = detectar_pupila(frame, o.centro, o.raio_iris)
            q = avaliar_qualidade(frame, o, rp)
            bio = medir_biometria(o, rp)
            qs.append(q); bios.append(bio)
            daug_p = f"{base}_daugman_{o.lado}.jpg"
            cv2.imwrite(daug_p, heatmap_iris(frame, o.centro, o.raio_iris, rp))
            zonas = analisar_zonas(frame, o.centro, o.raio_iris, rp,
                                   o.lado, contorno=o.contorno)
            mapa_p = f"{base}_mapa_{o.lado}.jpg"
            cv2.imwrite(mapa_p, render_mapa(zonas, 360, f"Olho {o.lado}"))
            _tops = top_zonas(zonas, 5)
            tops = ([f"{t.indice+1}. {t.nome} ({t.nivel})" for t in _tops]
                    if _tops else ["Nenhuma zona com marca significativa."])
            olhos_info.append({
                "lado": o.lado, "cor": f.cor_predominante,
                "trama": "densa" if f.densidade_fibras > 0.10 else "lisa",
                "textura": "uniforme" if f.glcm_homogeneidade > 0.5 else "com variações",
                "nitidez": f"{f.nitidez:.0f}", "reflexo": f.reflexo_pct,
                "qualidade": f.qualidade_ok, "zoom_path": zoom_p, "daugman_path": daug_p,
                "mapa_path": mapa_p, "zonas": tops,
                "qualidade_score": f"{q.score:.0f}/100 ({q.nivel})",
                "biometria": (f"íris ~{bio.diametro_iris_mm:.1f} mm · "
                              f"pupila ~{bio.diametro_pupila_mm:.1f} mm · "
                              f"razão {bio.razao_pupilar:.2f} ({bio.dilatacao})"),
                "constituicao": "tensa" if f.densidade_fibras > 0.10 else "relaxada",
            })
        anot_p = f"{base}_captura.jpg"
        cv2.imwrite(anot_p, anot)
        val = validar_plausibilidade(olhos, qs, bios)
        comp = comparar_olhos(olhos, feats)
        resumo = {
            "confianca": f"{val.confianca:.0f}/100",
            "avisos": val.avisos,
            "comparacao": (f"Simetria das íris {comp.simetria_raio*100:.0f}% · {comp.nota}"
                           if comp else ""),
        }
        cliente = DadosCliente(
            nome=self.in_nome.text(), idade=self.in_idade.text(),
            data=self.in_data.text(), profissional=self.in_prof.text(),
            observacoes=self.in_obs.toPlainText())
        try:
            caminho = gerar_pdf(destino, cliente, olhos_info, anot_p, resumo)
            QMessageBox.information(self, "Laudo gerado",
                                    f"PDF salvo em:\n{caminho}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao gerar PDF:\n{e}")

    def closeEvent(self, ev):
        self.timer.stop()
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        self._landmarker.close()
        ev.accept()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    log = logging.getLogger("iris_analyzer")

    # Rede de seguranca: nenhuma excecao nao tratada deve encerrar o app.
    import sys

    def _hook(exc_type, exc, tb):
        log.error("Excecao nao tratada", exc_info=(exc_type, exc, tb))
    sys.excepthook = _hook

    # macOS: quando o app e iniciado por um script dentro do .app, o processo
    # nasce em segundo plano e a JANELA NAO APARECE. Promove a app de primeiro
    # plano (Dock + janela visivel) via ApplicationServices (sem depender de
    # pyobjc, que pode nao estar instalado).
    if sys.platform == "darwin":
        try:
            import ctypes
            class _PSN(ctypes.Structure):
                _fields_ = [("hi", ctypes.c_uint32), ("lo", ctypes.c_uint32)]
            _svc = ctypes.cdll.LoadLibrary(
                "/System/Library/Frameworks/ApplicationServices.framework/"
                "ApplicationServices")
            _psn = _PSN(0, 2)  # kCurrentProcess
            _svc.TransformProcessType(ctypes.byref(_psn), 1)  # -> foreground app
        except Exception:
            log.warning("Nao foi possivel promover a app a primeiro plano.")

    app = QApplication([])
    app.setStyle("Fusion")
    app.setFont(QFont("Helvetica Neue", 10))
    app.setStyleSheet(
        f"QWidget{{background:{BG};color:{TEXTO};}}"
        f"QMessageBox{{background:{CARD};}}"
        f"QMessageBox QLabel{{color:{TEXTO};}}"
        f"QPushButton{{background:{ESCURO};color:{TEXTO};border:1px solid {BORDER};"
        f"border-radius:8px;padding:6px 14px;}}"
        f"QPushButton:hover{{border-color:#444;}}"
        f"QToolTip{{background:{CARD};color:{TEXTO};border:1px solid {BORDER};}}")

    # Checagem de ambiente: modelo do MediaPipe presente?
    if not config.MODELO_PATH.exists():
        log.error("Modelo ausente: %s", config.MODELO_PATH)
        QMessageBox.critical(
            None, "Modelo ausente",
            "O modelo do MediaPipe nao foi encontrado.\n\n"
            "Baixe executando no terminal:\n    python3 download_model.py\n\n"
            f"Esperado em: {config.MODELO_PATH}")
        return

    win = MainWindow()
    win.show()
    win.raise_()
    win.activateWindow()
    if sys.platform == "darwin":
        try:
            app.setActiveWindow(win)
        except Exception:
            pass
    log.info("Iris Analyzer iniciado.")
    app.exec()


if __name__ == "__main__":
    main()
