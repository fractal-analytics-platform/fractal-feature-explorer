import functools
import os
from datetime import timedelta
from pathlib import Path
from typing import Annotated, Literal

import streamlit as st
import toml
from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from streamlit.logger import get_logger

logger = get_logger(__name__)


def remove_trailing_slash(value: str) -> str:
    return value.rstrip("/")


class BaseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_type: Literal["local", "production"]
    allow_local_paths: bool
    cache_ttl: float | timedelta | str | None = None
    cache_max_entries: int | None = None


class LocalConfig(BaseConfig):
    deployment_type: Literal["local"]  # type: ignore override type
    fractal_data_urls: list[Annotated[str, AfterValidator(remove_trailing_slash)]] = (
        Field(default_factory=list)
    )
    allow_local_paths: bool = True


class ProductionConfig(BaseConfig):
    deployment_type: Literal["production"]  # type: ignore override type
    allow_local_paths: Literal[False] = False  # type: ignore override type
    allow_http: bool = False
    fractal_data_url: Annotated[str, AfterValidator(remove_trailing_slash)]
    fractal_backend_url: Annotated[str, AfterValidator(remove_trailing_slash)]
    fractal_frontend_url: Annotated[str, AfterValidator(remove_trailing_slash)]
    fractal_cookie_name: str = "fastapiusersauth"


@st.cache_data
def get_config() -> LocalConfig | ProductionConfig:
    """Get the configuration for the Fractal Explorer."""
    config_path = Path(
        os.getenv(
            "FRACTAL_FEATURE_EXPLORER_CONFIG",
            (Path.home() / ".config/fractal_feature_explorer.toml"),
        )
    )

    if config_path.exists():
        config_data = toml.load(config_path)
        deployment_type = config_data.get("deployment_type", None)
        if deployment_type == "local":
            config = LocalConfig(**config_data)
            logger.info(f"Local configuration read from {config_path.as_posix()}.")
        elif deployment_type == "production":
            config = ProductionConfig(**config_data)
            logger.info(f"Production configuration read from {config_path.as_posix()}.")
        else:
            logger.error(f"Invalid configuration file {config_path}.")
            raise ValueError(
                f"Invalid {deployment_type=} in {config_path=}. "
                "Expected 'local' or 'production'."
            )
    else:
        logger.warning(f"Configuration file {config_path} does not exist.")
        logger.warning("Creating configuration file with default local configuration.")
        config = LocalConfig(deployment_type="local", allow_local_paths=True)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with config_path.open("w") as f:
            toml.dump(config.model_dump(), f)
        logger.info(f"Default configuration saved to {config_path.as_posix()}.")

    logger.debug(f"{config=}")
    logger.info(f"Streamlit version: {st.__version__}")
    return config


def st_cache_data_wrapper(func):
    """Wrapper around st.cache_data to set a default ttl.

    Supports per-user cache busting via the 'setup:cache_buster' session state key.
    Incrementing that value in a user's session invalidates their cached entries
    without affecting other users.
    """
    config = get_config()

    @st.cache_data(ttl=config.cache_ttl, max_entries=config.cache_max_entries)
    @functools.wraps(func)
    def _cached(*args, cache_buster: int = 0, **kwargs):
        return func(*args, **kwargs)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        cb = st.session_state.get("setup:cache_buster", 0)
        return _cached(*args, cache_buster=cb, **kwargs)

    return wrapper


def st_cache_resource_wrapper(func):
    """Wrapper around st.cache_resource to set a default ttl."""
    config = get_config()
    return st.cache_resource(
        ttl=config.cache_ttl, max_entries=config.cache_max_entries
    )(func)
