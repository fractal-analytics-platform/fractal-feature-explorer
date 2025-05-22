from argparse import ArgumentParser

import streamlit as st
from streamlit.logger import get_logger

from fractal_explorer.setup_page._plate_mode_setup import plate_mode_setup_component
from fractal_explorer.utils import Scope, invalidate_session_state

logger = get_logger(__name__)


def init_global_state():
    if f"{Scope.GLOBAL}:token" not in st.session_state:
        st.session_state[f"{Scope.GLOBAL}:token"] = None
    if f"{Scope.GLOBAL}:setup_mode" not in st.session_state:
        st.session_state[f"{Scope.GLOBAL}:setup_mode"] = "Plates"
    if f"{Scope.GLOBAL}:zarr_urls" not in st.session_state:
        st.session_state[f"{Scope.GLOBAL}:zarr_urls"] = []


def parse_cli_args():
    parser = ArgumentParser(description="Fractal Plate Explorer")
    parser.add_argument(
        "--setup-mode",
        type=str,
        default=None,
        choices=["Plates", "Images"],
        help="Select the mode of the setup.",
    )
    parser.add_argument(
        "--zarr-urls",
        nargs="+",
        type=str,
        default=None,
        help="List of Zarr URLs to add to the DataFrame",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Fractal token to use for authentication.",
    )

    args = parser.parse_args()
    if args.setup_mode is not None:
        st.session_state[f"{Scope.GLOBAL}:setup_mode"] = args.setup_mode
        logger.debug(
            f"setup_mode: {args.setup_mode} (set from CLI args)"
        )

    if args.token is not None:
        st.session_state[f"{Scope.GLOBAL}:token"] = args.token
        logger.debug("token: *** (set from CLI args)")

    if args.zarr_urls is not None:
        zarr_urls = st.session_state.get(f"{Scope.GLOBAL}:zarr_urls", [])
        st.session_state[f"{Scope.GLOBAL}:zarr_urls"] = zarr_urls + args.zarr_urls
        logger.debug(
            f"zarr_urls: {args.zarr_urls} (set from CLI args)"
        )


def parse_query_params():
    setup_mode = st.query_params.get("setup_mode", None)
    if setup_mode is not None:
        st.session_state[f"{Scope.GLOBAL}:setup_mode"] = setup_mode
        logger.debug(
            f"setup_mode: {setup_mode} (set url from query params)"
        )

    zarr_urls = st.query_params.get_all("zarr_url")
    if len(zarr_urls) > 0:
        _zarr_urls = st.session_state.get(f"{Scope.GLOBAL}:zarr_urls", [])
        st.session_state[f"{Scope.GLOBAL}:zarr_urls"] = _zarr_urls + zarr_urls
        logger.debug(
            f"zarr_urls: {zarr_urls} (set url from query params)"
        )

def setup_global_state():
    """
    Setup the global state for the Streamlit app.
    """
    init_global_state()
    parse_cli_args()
    parse_query_params()

    default_setup_mode = st.session_state.get(f"{Scope.GLOBAL}:setup_mode", "Plates")
    setup_mode = st.pills(
        "Setup Mode",
        options=["Plates", "Images"],
        default=default_setup_mode,
        key="_setup_mode",
        help="Select the mode of the setup.",
    )
    st.session_state[f"{Scope.GLOBAL}:setup_mode"] = setup_mode
    return setup_mode


def main():
    st.set_page_config(
        layout="wide",
        page_title="Fractal Plate Explorer",
        page_icon="https://raw.githubusercontent.com/fractal-analytics-platform/fractal-logos/main/common/fractal_favicon.png",
    )
    t_col1, t_col2 = st.columns([1, 5])
    with t_col1:
        st.image(
            "https://raw.githubusercontent.com/fractal-analytics-platform/fractal-logos/main/common/fractal_logo.png",
            width=100,
        )
    with t_col2:
        st.title("Fractal Plate Explorer")

    st.divider()

    setup_mode = setup_global_state()
    with st.sidebar:
        token = st.text_input(
            label="Fractal Token",
            value=st.session_state.get(f"{Scope.GLOBAL}:token", ""),
            key="_fractal_token",
            type="password",
        )
        st.session_state[f"{Scope.GLOBAL}:token"] = token

    match setup_mode:
        case "Plates":
            features_table, table_name = plate_mode_setup_component()
        case "Images":
            st.error("Image mode is not yet implemented. Please select 'Plates' mode.")
            logger.error("Image mode is not yet implemented.")
            st.stop()
        case _:
            error_msg = (
                f"Invalid setup mode selected. Should be 'Plates' or 'Images' but got {setup_mode}."
            )
            st.error(error_msg)
            logger.error(error_msg)
            st.stop()

    schema = features_table.collect_schema()
    if f"{Scope.GLOBAL}:feature_table" in st.session_state:
        old_table_name = st.session_state[f"{Scope.GLOBAL}:feature_table_name"]
        old_schema = st.session_state[f"{Scope.GLOBAL}:feature_table_schema"]
        if old_table_name != table_name:
            # invalidate the old table
            warn_msg = (
                f"The feature table name has changed. {old_table_name} -> {table_name}. \n"
                "All filters have been reset."
            )
            logger.warning(warn_msg)
            st.warning(warn_msg)

        elif old_schema != schema:
            # invalidate the old table
            warn_msg = (
                "The feature table schema has changed. The filters have been reset."
            )
            logger.warning(warn_msg)
            st.warning(warn_msg)
            invalidate_session_state(f"{Scope.FILTERS}")

    st.session_state[f"{Scope.GLOBAL}:feature_table"] = features_table
    st.session_state[f"{Scope.GLOBAL}:feature_table_name"] = table_name
    st.session_state[f"{Scope.GLOBAL}:feature_table_schema"] = schema


if __name__ == "__main__":
    main()
