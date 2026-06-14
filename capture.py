"""Captura de foto pela webcam.

Abre a webcam, mostra o preview e salva uma foto ao pressionar ESPACO.
Pressione ESC para sair sem salvar.
"""
from __future__ import annotations

import os
import time

import cv2


def capturar_foto(saida: str = "foto.jpg", camera: int = 0) -> str | None:
    """Abre a webcam e salva uma foto. Retorna o caminho salvo ou None."""
    cap = cv2.VideoCapture(camera)
    if not cap.isOpened():
        raise RuntimeError(
            "Nao foi possivel acessar a webcam. Verifique permissoes "
            "(no macOS: Ajustes > Privacidade > Camera)."
        )

    print("Webcam aberta. ESPACO = tirar foto | ESC = cancelar")
    caminho = None
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Falha ao ler frame da camera.")
                break

            preview = frame.copy()
            cv2.putText(
                preview,
                "ESPACO: foto | ESC: sair",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )
            cv2.imshow("Webcam - Iris Analyzer", preview)

            tecla = cv2.waitKey(1) & 0xFF
            if tecla == 27:  # ESC
                print("Cancelado.")
                break
            if tecla == 32:  # ESPACO
                os.makedirs(os.path.dirname(saida) or ".", exist_ok=True)
                cv2.imwrite(saida, frame)
                caminho = os.path.abspath(saida)
                print(f"Foto salva em: {caminho}")
                # pequeno flash visual de confirmacao
                time.sleep(0.2)
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

    return caminho


if __name__ == "__main__":
    capturar_foto()
