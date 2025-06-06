"""Fractal Explorer Dashboard"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fractal-feature-explorer")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "uninstalled"
__author__ = "Lorenzo Cerrone"
__email__ = "lorenzo.cerrone@uzh.ch"
