from pathlib import Path
from pydantic import BaseModel,ConfigDict
import toml
import os
from fractal_explorer.utils.common import logger
import streamlit as st

class FractalExplorerConfig(BaseModel):
    """
    Configuration model for the Fractal Explorer.
    """
    model_config = ConfigDict(extra="forbid")

    allow_local_paths: bool = False
    skip_authentication: bool = False
    # FIXME: deduplicate some of the following URLs
    # FIXME: remove trailing slash from `fractal_backend_url`
    fractal_data_domain: str | None = None
    fractal_backend_url: str | None = None
    fractal_login_url: str | None = None
    fractal_cookie_name: str = "fastapiusersauth"


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
            print(config)
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
