"""Fractal Explorer Dashboard"""

from importlib.metadata import PackageNotFoundError, version
import os
from pathlib import Path

try:
    __version__ = version("fractal-feature-explorer")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "uninstalled"
__author__ = "Lorenzo Cerrone"
__email__ = "lorenzo.cerrone@uzh.ch"

CONFIG_PATH = config_path = os.getenv(
    "FRACTAL_FEATURE_EXPLORER_CONFIG",
    (Path.home() / ".fractal_feature_explorer" / "config.toml"),
)

DEFAULT_CONFIG_PATH = Path(__file__).parent / "resources" / "config.toml"
