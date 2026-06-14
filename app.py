"""App principal: captura foto pela webcam e analisa a iris.

Uso:
    python app.py                 # abre a webcam, tira foto e analisa
    python app.py --imagem x.jpg  # analisa uma imagem ja existente

AVISO: ferramenta educacional. Iridologia NAO e validada cientificamente.
Nada aqui constitui diagnostico medico.
"""
from __future__ import annotations

import argparse
import os

import cv2

from capture import capturar_foto
from iris_analysis import analisar_iris, desenhar_anotacoes


DISCLAIMER = (
    "\n" + "=" * 64 + "\n"
    "AVISO: A iridologia NAO possui validacao cientifica como metodo\n"
    "diagnostico. Esta ferramenta e EDUCACIONAL/EXPERIMENTAL e descreve\n"
    "apenas caracteristicas de imagem. NAO substitui avaliacao medica.\n"
    + "=" * 64 + "\n"
)


def imprimir_relatorio(res) -> None:
    print("\n----- RELATORIO DE ANALISE DA IRIS -----")
    if not res.olho_detectado:
        for o in res.observacoes:
            print(f"  - {o}")
        return
    print(f"  Centro (px):        {res.centro}")
    print(f"  Raio iris (px):     {res.raio_iris}")
    print(f"  Raio pupila (px):   {res.raio_pupila}")
    print(f"  Cor predominante:   {res.cor_predominante}")
    print(f"  Cor media (BGR):    {res.cor_bgr_media}")
    print(f"  Densidade textura:  {res.textura_densidade}  (0-1)")
    print(f"  Homogeneidade:      {res.homogeneidade}  (0-1)")
    print("\n  Observacoes:")
    for o in res.observacoes:
        print(f"   - {o}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analisador de iris (educacional)")
    parser.add_argument("--imagem", help="Analisar imagem existente em vez da webcam")
    parser.add_argument("--saida", default="foto.jpg", help="Caminho da foto capturada")
    parser.add_argument("--camera", type=int, default=0, help="Indice da webcam")
    args = parser.parse_args()

    print(DISCLAIMER)

    if args.imagem:
        caminho = args.imagem
        if not os.path.exists(caminho):
            print(f"Arquivo nao encontrado: {caminho}")
            return
    else:
        caminho = capturar_foto(saida=args.saida, camera=args.camera)
        if not caminho:
            print("Nenhuma foto capturada. Encerrando.")
            return

    img = cv2.imread(caminho)
    if img is None:
        print(f"Nao foi possivel abrir a imagem: {caminho}")
        return

    res = analisar_iris(img)
    imprimir_relatorio(res)

    anotada = desenhar_anotacoes(img, res)
    saida_anotada = os.path.splitext(caminho)[0] + "_anotada.jpg"
    cv2.imwrite(saida_anotada, anotada)
    print(f"\nImagem anotada salva em: {os.path.abspath(saida_anotada)}")

    # Mostra resultado (fecha em qualquer tecla)
    cv2.imshow("Iris analisada (qualquer tecla p/ fechar)", anotada)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    print(DISCLAIMER)


if __name__ == "__main__":
    main()
