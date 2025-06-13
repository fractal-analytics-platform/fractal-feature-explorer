from pathlib import Path
from pydantic import BaseModel, ConfigDict, AfterValidator, Field
import toml
import os
import streamlit as st
from typing import Literal
from typing import Annotated

from streamlit.logger import get_logger


logger = get_logger(__name__)

def get_config_path() -> Path:
    config_path = os.getenv(
        "FRACTAL_FEATURE_EXPLORER_CONFIG",
        (Path.home() / ".fractal_feature_explorer" / "config.toml")
    )
    return Path(config_path)

def remove_trailing_slash(value: str) -> str:
    return value.rstrip("/")

def default_fractal_data_urls() -> list[str]:
    """
    Returns a default list of Fractal data URLs.
    This can be used to initialize the configuration with default values.
    """
    return [
        "https://fractal-bvc.mls.uzh.ch/",
        "https://fractal-beta.mls.uzh.ch/",
        "https://fractal.mls.uzh.ch/",
    ]

class LocalConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_type: Literal["local"]
    allow_local_paths: bool = True
    fractal_data_urls: list[Annotated[str, AfterValidator(remove_trailing_slash)]] = Field(
        default_factory=default_fractal_data_urls)

class ProductionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_type: Literal["production"]
    allow_local_paths: Literal[False] = False
    fractal_data_url: Annotated[str, AfterValidator(remove_trailing_slash)]
    fractal_backend_url: Annotated[str, AfterValidator(remove_trailing_slash)]
    fractal_frontend_url: Annotated[str, AfterValidator(remove_trailing_slash)]
    fractal_cookie_name: str = "fastapiusersauth"


def _init_local_config() -> LocalConfig:
    """
    Initialize the local configuration with default values.
    """
    config_path = get_config_path()
    allow_saving_config = input(
        f"Do you want to create a default configuration file at {config_path.as_posix()}? (y/n): "
    )
    for _ in range(3):
        if allow_saving_config.lower() == "y" or allow_saving_config.lower() == "n":
            break
        else:
            allow_saving_config = input(f"{allow_saving_config} is not a valid input. Please enter 'y' or 'n': ")

    fractal_data_urls = input(
        f"(Optional) Enter the Fractal server URLs to allow authenticated streaming (default: {default_fractal_data_urls()}): "
    )

    if not fractal_data_urls.strip():
        fractal_data_urls = default_fractal_data_urls()
    else:
        fractal_data_urls = [fractal_data_urls]
    
    local_config = LocalConfig(
        deployment_type="local",
        allow_local_paths=True,
        fractal_data_urls=fractal_data_urls,
    )
    if allow_saving_config.lower() == "y":
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            toml.dump(local_config.model_dump(), f)
        logger.info(f"Default configuration saved to {config_path.as_posix()}.")
    
    return local_config


@st.cache_data
def get_config() -> LocalConfig | ProductionConfig:
    """
    Get the configuration for the Fractal Explorer.
    """

    # Define expected config path
    config_path = os.getenv(
        "FRACTAL_FEATURE_EXPLORER_CONFIG",
        (Path.home() / ".fractal_feature_explorer" / "config.toml").as_posix(),
    )
    config_path = Path(config_path)

    if config_path.exists():
        config_data = toml.load(config_path)
        key = "deployment_type"
        if key not in config_data.keys():
            raise ValueError(f"Missing {key=} in {config_path=}.")
        elif config_data[key] == "local":
            config = LocalConfig(**config_data)
            logger.info(f"Local configuration read from {config_path.as_posix()}.")
        elif config_data[key] == "production":
            config = ProductionConfig(**config_data)
            logger.info(f"Production configuration read from {config_path.as_posix()}.")
        else:
            raise ValueError(
                f"Invalid {key=} in {config_path=}. "
                "Expected 'local' or 'production'."
            )
    else:
        logger.warning(
            f"Config file {config_path} does not exist; "
            "using default local configuration."
        )
        config = _init_local_config()
    logger.debug(f"{config=}")
    return config
