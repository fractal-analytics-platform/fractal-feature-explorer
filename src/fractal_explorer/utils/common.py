from enum import StrEnum

import streamlit as st
from streamlit.logger import get_logger
from pydantic import BaseModel, Field
from pathlib import Path
import toml
import os

logger = get_logger(__name__)


class Scope(StrEnum):
    """
    Enum for the different phases of the fractal explorer.
    """

    PRIVATE = "private"  # User private data (like auth token)
    SETUP = "setup"  # Setup page keys
    FILTERS = "filters"  # Filters page keys
    EXPLORE = "explore"  # Explore page keys
    DATA = "data"  # Non-serializable data (like polars DataFrames)


def invalidate_session_state(key_prefix: str) -> None:
    """
    Invalidate the session state for the given key.
    """
    logger.info(f"Invalidating session state for key prefix: {key_prefix}")
    for key in st.session_state.keys():
        _key = str(key)
        if _key.startswith(key_prefix):
            logger.info(f"Deleting key: {key}")
            del st.session_state[key]


class FractalExplorerConfig(BaseModel):
    """
    Configuration model for the Fractal Explorer.
    """

    allow_local_paths: bool = True
    fractal_token_subdomains: list[str] = Field(
        default_factory=lambda: [
            "https://fractal-bvc.mls.uzh.ch/",
            "https://fractal-beta.mls.uzh.ch/",
            "https://fractal.mls.uzh.ch",
        ]
    )


@st.cache_data
def get_config() -> FractalExplorerConfig:
    """
    Get the configuration for the Fractal Explorer.
    """
    # 1 Check for environment variable
    config_path = os.getenv("FRACTAL_EXPLORER_CONFIG", None)
    if config_path is not None:
        config_path = Path(config_path)
        if config_path.exists():
            config = toml.load(config_path)
            return FractalExplorerConfig(**config)
        else:
            logger.warning(
                "Config path in environment variable "
                f"'FRACTAL_EXPLORER_CONFIG' does not exist: {config_path}"
            )

    # 2 Check for config file in home directory
    config_path = Path.home() / ".fractal_explorer" / "config.toml"

    if config_path.exists():
        config = toml.load(config_path)
        return FractalExplorerConfig(**config)

    # 3 return the default configuration
    return FractalExplorerConfig()


def get_fractal_token() -> str | None:
    """
    Get the Fractal token from the session state.
    """
    return st.session_state.get(f"{Scope.PRIVATE}:token", None)
