"""App V2: captura pela webcam, segmenta a iris com MediaPipe, aplica
normalizacao de Daugman e extrai features (cor Lab, Gabor, LBP, GLCM).

Uso:
    python app_v2.py                  # webcam -> foto -> analise
    python app_v2.py --imagem olho.jpg

AVISO: ferramenta EDUCACIONAL. A iridologia NAO tem validacao cientifica
como metodo diagnostico. Nada aqui constitui diagnostico medico.
"""
from __future__ import annotations

import argparse
import os

import cv2

from capture import capturar_foto
from iris_segmentation import segmentar_olhos, desenhar_olhos
from iris_features import extrair_features, normalizar_daugman


DISCLAIMER = (
    "\n" + "=" * 66 + "\n"
    "AVISO: A iridologia NAO possui validacao cientifica como metodo\n"
    "diagnostico. Esta ferramenta e EDUCACIONAL e extrai apenas\n"
    "caracteristicas de imagem. NAO substitui avaliacao medica.\n"
    + "=" * 66 + "\n"
)


def interpretar(f) -> list[str]:
    """Descricoes objetivas das features (sem alegacao medica)."""
    out = []
    out.append(f"Cor predominante: {f.cor_predominante} (Lab medio {f.lab_medio}).")
    if f.densidade_fibras > 0.10:
        out.append("Trama de fibras densa e marcada (muitas linhas radiais).")
    else:
        out.append("Trama de fibras mais lisa/uniforme.")
    if f.glcm_homogeneidade > 0.5:
        out.append("Textura estatisticamente homogenea (poucas manchas/variacoes).")
    else:
        out.append("Textura heterogenea: variacoes de tom (podem ser marcas, sombra ou reflexo).")
    out.append(
        f"Indices: Gabor={f.gabor_energia} | LBP-unif={f.lbp_uniformidade} | "
        f"GLCM-contraste={f.glcm_contraste}."
    )
    return out


def relatorio(olho, f) -> None:
    print(f"\n----- OLHO {olho.lado.upper()} -----")
    print(f"  Centro (px):      ({olho.centro[0]:.1f}, {olho.centro[1]:.1f})")
    print(f"  Raio iris (px):   {olho.raio_iris:.1f}")
    print(f"  Raio pupila (px): {olho.raio_pupila:.1f}")
    print(f"  Nitidez:          {f.nitidez}  | Reflexo: {f.reflexo_pct}%")
    print(f"  Qualidade OK:     {f.qualidade_ok}")
    for a in f.avisos:
        print(f"   ! {a}")
    print("  Observacoes:")
    for o in interpretar(f):
        print(f"   - {o}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Analisador de iris V2 (MediaPipe + Daugman)")
    ap.add_argument("--imagem", help="Analisar imagem existente")
    ap.add_argument("--saida", default="foto.jpg")
    ap.add_argument("--camera", type=int, default=0)
    args = ap.parse_args()

    print(DISCLAIMER)

    if args.imagem:
        caminho = args.imagem
        if not os.path.exists(caminho):
            print(f"Arquivo nao encontrado: {caminho}")
            return
    else:
        caminho = capturar_foto(saida=args.saida, camera=args.camera)
        if not caminho:
            print("Nenhuma foto capturada.")
            return

    img = cv2.imread(caminho)
    if img is None:
        print(f"Nao foi possivel abrir: {caminho}")
        return

    olhos = segmentar_olhos(img)
    if not olhos:
        print("Nenhum olho detectado pelo MediaPipe. Aproxime o rosto e melhore a luz.")
        return

    base = os.path.splitext(caminho)[0]
    for olho in olhos:
        f = extrair_features(img, olho.centro, olho.raio_iris, olho.raio_pupila)
        relatorio(olho, f)
        polar = normalizar_daugman(img, olho.centro, olho.raio_iris, olho.raio_pupila)
        cv2.imwrite(f"{base}_daugman_{olho.lado}.jpg", polar)

    anotada = desenhar_olhos(img, olhos)
    cv2.imwrite(f"{base}_anotada.jpg", anotada)
    print(f"\nImagem anotada: {os.path.abspath(base + '_anotada.jpg')}")
    print(f"Mapas de Daugman salvos: {base}_daugman_*.jpg")

    cv2.imshow("Iris V2 (qualquer tecla p/ fechar)", anotada)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print(DISCLAIMER)


if __name__ == "__main__":
    main()
