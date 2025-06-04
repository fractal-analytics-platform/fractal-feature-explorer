from enum import StrEnum

import streamlit as st
from streamlit.logger import get_logger


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


def get_fractal_token() -> str | None:
    """
    Get the Fractal token from the session state.
    """
    return st.session_state.get(f"{Scope.PRIVATE}:fractal-token", None)
