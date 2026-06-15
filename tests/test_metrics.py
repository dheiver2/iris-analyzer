import types

from iris_analyzer.iris_metrics import (
    medir_biometria, validar_plausibilidade, comparar_olhos, Biometria,
)


def _olho(cx, cy, r, lado="direito"):
    return types.SimpleNamespace(centro=(cx, cy), raio_iris=r, lado=lado)


def _q(score):
    return types.SimpleNamespace(score=score)


def _feat(lab):
    return types.SimpleNamespace(lab_medio=lab)


def test_biometria_basica():
    b = medir_biometria(_olho(100, 100, 50), 20)
    assert isinstance(b, Biometria)
    assert b.diametro_iris_px == 100.0
    assert abs(b.razao_pupilar - 0.4) < 1e-6
    assert b.dilatacao == "normal"


def test_dilatacao_classes():
    assert medir_biometria(_olho(0, 0, 50), 10).dilatacao == "miose"      # 0.2
    assert medir_biometria(_olho(0, 0, 50), 35).dilatacao == "midriase"   # 0.7


def test_validacao_simetria_e_confianca():
    olhos = [_olho(0, 0, 50, "direito"), _olho(0, 0, 51, "esquerdo")]
    bios = [medir_biometria(o, 20) for o in olhos]
    val = validar_plausibilidade(olhos, [_q(85), _q(85)], bios)
    assert val.ok is True
    assert val.confianca > 60
    assert val.avisos == []


def test_validacao_assimetria_gera_aviso():
    olhos = [_olho(0, 0, 50, "direito"), _olho(0, 0, 80, "esquerdo")]
    bios = [medir_biometria(o, 20) for o in olhos]
    val = validar_plausibilidade(olhos, [_q(85), _q(85)], bios)
    assert any("diferentes" in a for a in val.avisos)


def test_comparar_heterocromia():
    olhos = [_olho(0, 0, 50, "direito"), _olho(0, 0, 50, "esquerdo")]
    # cores Lab bem diferentes -> heterocromia
    comp = comparar_olhos(olhos, [_feat((50, 10, 10)), _feat((50, 60, 60))])
    assert comp.heterocromia is True
    comp2 = comparar_olhos(olhos, [_feat((50, 10, 10)), _feat((52, 12, 11))])
    assert comp2.heterocromia is False
