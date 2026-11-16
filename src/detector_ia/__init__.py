"""Detector de texto generado por IA y de copia entre entregas."""

from importlib.metadata import PackageNotFoundError, version

from detector_ia.main import main

try:
    __version__ = version("detector-ia")
except PackageNotFoundError:  # ejecución desde el código sin instalar
    __version__ = "0.0.0"

__author__ = "Alberto Ortiz Sánchez"
__license__ = "MIT"

__all__ = ["main", "__author__", "__license__", "__version__"]
