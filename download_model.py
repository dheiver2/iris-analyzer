"""Baixa o modelo face_landmarker.task do MediaPipe, se ausente.

Uso:
    python3 download_model.py
"""
from __future__ import annotations

import sys
import urllib.request

import config


def baixar(force: bool = False) -> str:
    destino = config.MODELO_PATH
    if destino.exists() and not force:
        print(f"Modelo ja existe: {destino}")
        return str(destino)
    print(f"Baixando modelo de {config.MODELO_URL} ...")
    destino.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(config.MODELO_URL, destino)
    tam = destino.stat().st_size
    if tam < 100_000:
        destino.unlink(missing_ok=True)
        raise RuntimeError(f"Download falhou (arquivo muito pequeno: {tam} bytes).")
    print(f"OK: {destino} ({tam/1e6:.1f} MB)")
    return str(destino)


if __name__ == "__main__":
    try:
        baixar(force="--force" in sys.argv)
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
