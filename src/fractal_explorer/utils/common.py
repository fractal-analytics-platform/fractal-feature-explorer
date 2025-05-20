from enum import StrEnum
from typing import Literal

import streamlit as st
from pydantic import BaseModel, Field


class Scope(StrEnum):
    """
    Enum for the different phases of the fractal explorer.
    """

    GLOBAL = "global"
    SETUP = "setup"
    FILTERS = "filters"
    EXPLORE = "explore"


class GlobalConfigs(BaseModel):
    """
    Global configurations for the fractal explorer.
    """

    token: str | None
    dashboard_mode: Literal["Plates", "Images"]
    zarr_urls: list[str] = Field(default_factory=list)

    @classmethod
    def from_state(cls) -> "GlobalConfigs":
        """
        Create a GlobalConfigs object from the Streamlit session state.
        """
        return cls(
            token=st.session_state.get(f"{Scope.GLOBAL}:token", None),
            dashboard_mode=st.session_state.get(
                f"{Scope.GLOBAL}:dashboard_mode", "Plates"
            ),
            zarr_urls=st.session_state.get(f"{Scope.GLOBAL}:zarr_urls", []),
        )


def invalidate_session_state(key_prefix: str) -> None:
    """
    Invalidate the session state for the given key.
    """
    for key in st.session_state.keys():
        _key = str(key)
        if _key.startswith(key_prefix):
            del st.session_state[key]
