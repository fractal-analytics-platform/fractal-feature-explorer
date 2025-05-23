from enum import StrEnum

import streamlit as st


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
    for key in st.session_state.keys():
        _key = str(key)
        if _key.startswith(key_prefix):
            del st.session_state[key]
