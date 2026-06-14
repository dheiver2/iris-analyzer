"""Iris Analyzer — análise de imagem da íris para bem-estar.

Não é dispositivo médico e não realiza diagnóstico. A iridologia não tem
validação científica como método de diagnóstico.
"""
__version__ = "1.0.0"


def main():
    """Ponto de entrada do aplicativo desktop."""
    from .desktop_app import main as _main
    _main()
