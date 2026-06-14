"""Validacoes de entrada e excecoes do Iris Analyzer.

Centraliza checagens reutilizadas pelos modulos de analise, com mensagens
claras. Lanca IrisError (ou subclasses) em vez de falhar silenciosamente.
"""
from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger("iris_analyzer")


class IrisError(Exception):
    """Erro base do Iris Analyzer."""


class ModeloAusenteError(IrisError):
    """Modelo do MediaPipe nao encontrado."""


class ImagemInvalidaError(IrisError):
    """Imagem ausente ou em formato invalido."""


class GeometriaInvalidaError(IrisError):
    """Parametros de geometria da iris invalidos."""


def validar_imagem(img, nome: str = "imagem") -> np.ndarray:
    """Garante que e um array BGR HxWx3 nao vazio."""
    if img is None:
        raise ImagemInvalidaError(f"{nome} e None.")
    if not isinstance(img, np.ndarray):
        raise ImagemInvalidaError(f"{nome} deve ser numpy.ndarray, recebido {type(img)!r}.")
    if img.ndim != 3 or img.shape[2] != 3:
        raise ImagemInvalidaError(f"{nome} deve ser BGR (HxWx3), shape={img.shape}.")
    if img.size == 0 or img.shape[0] < 2 or img.shape[1] < 2:
        raise ImagemInvalidaError(f"{nome} muito pequena: shape={img.shape}.")
    return img


def validar_geometria(centro, r_iris, r_pupila, shape=None) -> None:
    """Valida centro (x,y), raios > 0 e r_pupila < r_iris (e dentro da imagem)."""
    try:
        cx, cy = float(centro[0]), float(centro[1])
    except (TypeError, IndexError, ValueError):
        raise GeometriaInvalidaError(f"centro invalido: {centro!r}.")
    if not (r_iris > 0):
        raise GeometriaInvalidaError(f"r_iris deve ser > 0, recebido {r_iris!r}.")
    if not (0 < r_pupila < r_iris):
        raise GeometriaInvalidaError(
            f"r_pupila deve estar em (0, r_iris): r_pupila={r_pupila!r}, r_iris={r_iris!r}.")
    if shape is not None:
        h, w = shape[:2]
        if not (0 <= cx < w and 0 <= cy < h):
            raise GeometriaInvalidaError(
                f"centro ({cx:.1f},{cy:.1f}) fora da imagem {w}x{h}.")


def validar_lado(lado: str) -> str:
    if lado not in ("direito", "esquerdo"):
        raise IrisError(f"lado deve ser 'direito' ou 'esquerdo', recebido {lado!r}.")
    return lado
