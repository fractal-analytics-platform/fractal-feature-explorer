from pathlib import Path
from pydantic import BaseModel, ConfigDict, AfterValidator
import toml
import streamlit as st
from typing import Literal
from typing import Annotated

from streamlit.logger import get_logger
import os

logger = get_logger(__name__)

CONFIG_PATH = os.getenv(
    "FRACTAL_FEATURE_EXPLORER_CONFIG",
    (Path.home() / ".fractal_feature_explorer" / "config.toml"),
)

DEFAULT_CONFIG_PATH = Path(__file__).parent / "resources" / "config.toml"


def remove_trailing_slash(value: str) -> str:
    return value.rstrip("/")


class LocalConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_type: Literal["local"]
    fractal_data_urls: list[Annotated[str, AfterValidator(remove_trailing_slash)]]
    allow_local_paths: bool = True


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
    config_path = Path(CONFIG_PATH)
    allow_saving_config = input(
        f"Do you want to create a default configuration file at {config_path.as_posix()}? (y/n): "
    )
    for _ in range(3):
        if allow_saving_config.lower() == "y" or allow_saving_config.lower() == "n":
            break
        else:
            allow_saving_config = input(
                f"{allow_saving_config} is not a valid input. Please enter 'y' or 'n': "
            )
    else:
        raise ValueError(
            "Too many invalid inputs. Exiting without saving the configuration."
        )

    with open(DEFAULT_CONFIG_PATH, "r") as f:
        default_config = toml.load(f)

    local_config = LocalConfig(**default_config)
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
    config_path = Path(CONFIG_PATH)

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
                f"Invalid {key=} in {config_path=}. Expected 'local' or 'production'."
            )
    else:
        logger.warning(
            f"Config file {config_path} does not exist; "
            "using default local configuration."
        )
        config = _init_local_config()
    logger.debug(f"{config=}")
    return config
