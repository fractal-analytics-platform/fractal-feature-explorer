from pathlib import Path
from pydantic import BaseModel, ConfigDict, AfterValidator
import toml
import os
import streamlit as st
from typing import Literal
from typing import Annotated

from streamlit.logger import get_logger


logger = get_logger(__name__)


class BaseConfig(BaseModel):
    deployment_type: Literal["local", "production"]


class LocalConfig(BaseConfig):
    model_config = ConfigDict(extra="forbid")
    deployment_type: Literal["local"]
    allow_local_paths: bool = True


def remove_trailing_slash(value: str) -> str:
    return value.rstrip("/")


class ProductionConfig(BaseConfig):
    model_config = ConfigDict(extra="forbid")
    deployment_type: Literal["production"]
    allow_local_paths: Literal[False] = False
    fractal_data_url: Annotated[str, AfterValidator(remove_trailing_slash)]
    fractal_backend_url: Annotated[str, AfterValidator(remove_trailing_slash)]
    fractal_frontend_url: Annotated[str, AfterValidator(remove_trailing_slash)]
    fractal_cookie_name: str = "fastapiusersauth"


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
        else:
            config = ProductionConfig(**config_data)
            logger.info(f"Production configuration read from {config_path.as_posix()}.")
    else:
        logger.warning(
            f"Config file {config_path} does not exist; "
            "using default local configuration."
        )
        config = LocalConfig(
            deployment_type="local",
            allow_local_paths=False,
        )
    logger.debug(f"{config=}")
    return config
