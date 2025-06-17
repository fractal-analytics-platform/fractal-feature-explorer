"""
Fractal Feature Explorer - Setup Page
"""

import streamlit as st
from streamlit.logger import get_logger

from fractal_feature_explorer.pages.setup_page._plate_mode_setup import (
    plate_mode_setup_component,
)
from fractal_feature_explorer.utils import Scope, invalidate_session_state
import polars as pl
from fractal_feature_explorer.config import get_config
from fractal_feature_explorer.authentication import verify_authentication

logger = get_logger(__name__)


def init_global_state():
    if f"{Scope.PRIVATE}:fractal-token" not in st.session_state:
        st.session_state[f"{Scope.PRIVATE}:fractal-token"] = None
    if f"{Scope.SETUP}:setup_mode" not in st.session_state:
        st.session_state[f"{Scope.SETUP}:setup_mode"] = "Plates"
    if f"{Scope.SETUP}:zarr_urls" not in st.session_state:
        st.session_state[f"{Scope.SETUP}:zarr_urls"] = []


def parse_query_params():
    setup_mode = st.query_params.get("setup_mode", None)
    if setup_mode is not None:
        st.session_state[f"{Scope.SETUP}:setup_mode"] = setup_mode
        logger.info(f"setup_mode: {setup_mode} (set url from query params)")

    zarr_urls = st.query_params.get_all("zarr_url")
    if len(zarr_urls) > 0:
        _zarr_urls = st.session_state.get(f"{Scope.SETUP}:zarr_urls", [])
        st.session_state[f"{Scope.SETUP}:zarr_urls"] = _zarr_urls + zarr_urls
        logger.info(f"zarr_urls: {zarr_urls} (set url from query params)")


def setup_global_state():
    """
    Setup the global state for the Streamlit app.
    """
    init_global_state()
    parse_query_params()  # This may be useful e.g. when linking from fractal-web

    default_setup_mode = st.session_state.get(f"{Scope.SETUP}:setup_mode", "Plates")
    setup_mode = st.pills(
        "Setup Mode",
        options=["Plates", "Images"],
        default=default_setup_mode,
        key=f"{Scope.SETUP}:_setup_mode",
        help="Select the mode of the setup.",
    )
    st.session_state[f"{Scope.SETUP}:setup_mode"] = setup_mode
    return setup_mode


def filter_cache_invalidations(
    features_table: pl.LazyFrame, table_name: str
) -> pl.Schema:
    schema = features_table.collect_schema()
    if f"{Scope.DATA}:feature_table" in st.session_state:
        old_table_name = st.session_state[f"{Scope.DATA}:feature_table_name"]
        old_schema = st.session_state[f"{Scope.DATA}:feature_table_schema"]
        if old_table_name != table_name:
            # invalidate the old table
            warn_msg = (
                f"The feature table name has changed. {old_table_name} -> {table_name}. \n"
                "All filters have been reset."
            )
            logger.warning(warn_msg)
            st.warning(warn_msg)
            invalidate_session_state(f"{Scope.FILTERS}")

        elif old_schema != schema:
            # invalidate the old table
            warn_msg = (
                "The feature table schema has changed. The filters have been reset."
            )
            logger.warning(warn_msg)
            st.warning(warn_msg)
            invalidate_session_state(f"{Scope.FILTERS}")
    return schema


def _token_input_widget():
    """
    Input field for the Fractal authentication token.
    """
    config = get_config()
    if config.deployment_type == "production":
        return None
    current_token = st.session_state.get(f"{Scope.PRIVATE}:fractal-token", None)
    current_token = current_token if current_token else ""
    token = st.text_input(
        label="Fractal Authentication Token",
        value=current_token,
        key="_fractal_token",
        type="password",
    )
    if token == "":
        st.session_state[f"{Scope.PRIVATE}:fractal-token"] = None
    else:
        st.session_state[f"{Scope.PRIVATE}:fractal-token"] = token


def main():
    verify_authentication()

    setup_mode = setup_global_state()

    with st.sidebar:
        with st.expander("Advanced Options", expanded=False):
            _token_input_widget()

            st.divider()
            if st.button(
                "Reset Setup",
                key=f"{Scope.SETUP}:reset_setup",
                icon="🔄",
                help="Reset the setup state. This will clear all filters and the feature table.",
            ):
                invalidate_session_state(f"{Scope.SETUP}")
                st.rerun()

    match setup_mode:
        case "Plates":
            features_table, table_name = plate_mode_setup_component()
        case "Images":
            st.error("Image mode is not yet implemented. Please select 'Plates' mode.")
            logger.error("Image mode is not yet implemented.")
            st.stop()
        case _:
            error_msg = f"Invalid setup mode selected. Should be 'Plates' or 'Images' but got {setup_mode}."
            st.error(error_msg)
            logger.error(error_msg)
            st.stop()

    schema = filter_cache_invalidations(features_table, table_name)

    st.session_state[f"{Scope.DATA}:feature_table"] = features_table
    st.session_state[f"{Scope.DATA}:feature_table_name"] = table_name
    st.session_state[f"{Scope.DATA}:feature_table_schema"] = schema
    logger.info(
        f"Feature table {table_name} with schema {schema} has been set in session state."
    )
    logger.info("Setup page loading complete.")


if __name__ == "__main__":
    main()
