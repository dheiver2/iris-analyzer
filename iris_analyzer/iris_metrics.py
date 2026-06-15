"""Biometria da iris, validacoes avancadas de plausibilidade e comparacao
entre os olhos — para uma saida de nivel profissional.

As medidas em milimetros sao ESTIMATIVAS, calibradas pelo diametro medio
horizontal visivel da iris humana (HVID ~ 11.7 mm). Nada aqui e diagnostico.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

HVID_MM = 11.7          # diametro medio horizontal visivel da iris (mm)


@dataclass
class Biometria:
    diametro_iris_px: float
    diametro_pupila_px: float
    razao_pupilar: float          # pupila/iris (0-1)
    diametro_iris_mm: float       # estimativa (assume HVID medio)
    diametro_pupila_mm: float
    dilatacao: str                # "miose" | "normal" | "midriase"


def medir_biometria(olho, r_pupila) -> Biometria:
    d_iris = 2.0 * float(olho.raio_iris)
    d_pup = 2.0 * float(r_pupila)
    razao = d_pup / d_iris if d_iris > 0 else 0.0
    mm_por_px = HVID_MM / d_iris if d_iris > 0 else 0.0
    if razao < 0.30:
        dil = "miose"
    elif razao > 0.60:
        dil = "midriase"
    else:
        dil = "normal"
    return Biometria(
        diametro_iris_px=round(d_iris, 1),
        diametro_pupila_px=round(d_pup, 1),
        razao_pupilar=round(razao, 3),
        diametro_iris_mm=round(HVID_MM, 1),
        diametro_pupila_mm=round(d_pup * mm_por_px, 2),
        dilatacao=dil,
    )


@dataclass
class Validacao:
    ok: bool
    avisos: list[str]
    confianca: float              # 0-100, confianca global da analise


def validar_plausibilidade(olhos, qualidades, biometrias) -> Validacao:
    """Checagens avancadas alem da validacao de entrada: simetria dos olhos,
    razao pupilar fisiologica, tamanho minimo e qualidade."""
    avisos: list[str] = []

    if len(olhos) < 2:
        avisos.append("Apenas um olho detectado — recomenda-se capturar os dois.")

    # simetria dos raios (olhos do mesmo rosto devem ter iris parecidas)
    if len(olhos) == 2:
        r0, r1 = olhos[0].raio_iris, olhos[1].raio_iris
        if max(r0, r1) > 0 and abs(r0 - r1) / max(r0, r1) > 0.25:
            avisos.append("Tamanhos de íris muito diferentes entre os olhos "
                          "(ângulo da cabeça ou detecção imprecisa).")

    # razao pupilar fora da faixa fisiologica (~0.2 a 0.8)
    for b in biometrias:
        if b.razao_pupilar < 0.18 or b.razao_pupilar > 0.82:
            avisos.append("Razão pupila/íris fora do esperado — verifique foco "
                          "e iluminação.")
            break

    # tamanho minimo
    if olhos and min(o.raio_iris for o in olhos) < 14:
        avisos.append("Íris pequena na imagem — aproxime para mais detalhe.")

    # confianca = media da qualidade penalizada por avisos
    base = float(np.mean([q.score for q in qualidades])) if qualidades else 0.0
    confianca = max(0.0, base - 8.0 * len(avisos))
    ok = confianca >= 60 and not any("Apenas um olho" in a for a in avisos)
    return Validacao(ok=ok, avisos=avisos, confianca=round(confianca, 1))


@dataclass
class Comparacao:
    heterocromia: bool
    delta_cor: float              # diferenca de cor entre os olhos (Lab)
    simetria_raio: float          # 0-1 (1 = iguais)
    nota: str


def _delta_lab(a, b) -> float:
    return float(math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b))))


def comparar_olhos(olhos, feats) -> Comparacao | None:
    """Compara os dois olhos: heterocromia (cor) e simetria de tamanho."""
    if len(olhos) != 2 or len(feats) != 2:
        return None
    dlab = _delta_lab(feats[0].lab_medio, feats[1].lab_medio)
    r0, r1 = olhos[0].raio_iris, olhos[1].raio_iris
    sim = (min(r0, r1) / max(r0, r1)) if max(r0, r1) > 0 else 0.0
    heter = dlab > 18.0
    nota = ("Possível diferença de cor entre os olhos (heterocromia)."
            if heter else "Cor semelhante entre os olhos.")
    return Comparacao(heterocromia=heter, delta_cor=round(dlab, 1),
                      simetria_raio=round(sim, 3), nota=nota)
