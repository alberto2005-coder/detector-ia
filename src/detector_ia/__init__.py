"""Detector de texto generado por IA y de copia entre entregas."""

from importlib.metadata import PackageNotFoundError, version

from detector_ia.main import main

try:
    __version__ = version("detector-ia")
except PackageNotFoundError:  # ejecución desde el código sin instalar
    __version__ = "0.0.0"

__all__ = ["main", "__version__"]
