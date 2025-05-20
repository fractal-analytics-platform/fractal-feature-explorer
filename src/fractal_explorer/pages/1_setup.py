from argparse import ArgumentParser

import streamlit as st

from fractal_explorer.setup_utils import plate_mode_setup
from fractal_explorer.utils import Scope, invalidate_session_state


def init_global_state():
    if f"{Scope.GLOBAL}:token" not in st.session_state:
        st.session_state[f"{Scope.GLOBAL}:token"] = None
    if f"{Scope.GLOBAL}:dashboard_mode" not in st.session_state:
        st.session_state[f"{Scope.GLOBAL}:dashboard_mode"] = "Plates"
    if f"{Scope.GLOBAL}:zarr_urls" not in st.session_state:
        st.session_state[f"{Scope.GLOBAL}:zarr_urls"] = []


def parse_cli_args():
    parser = ArgumentParser(description="Fractal Plate Explorer")
    parser.add_argument(
        "--dashboard-mode",
        type=str,
        default=None,
        choices=["Plates", "Images"],
        help="Select the mode of the dashboard.",
    )
    parser.add_argument(
        "--zarr-urls",
        nargs="+",
        type=str,
        default=None,
        help="List of Zarr URLs to add to the DataFrame",
    )
    args = parser.parse_args()
    if args.dashboard_mode is not None:
        st.session_state[f"{Scope.GLOBAL}:dashboard_mode"] = args.dashboard_mode

    if args.zarr_urls is not None:
        zarr_urls = st.session_state.get(f"{Scope.GLOBAL}:zarr_urls", [])
        st.session_state[f"{Scope.GLOBAL}:zarr_urls"] = zarr_urls + args.zarr_urls


def parse_query_params():
    dashboard_mode = st.query_params.get("dashboard_mode", None)
    if dashboard_mode is not None:
        st.session_state[f"{Scope.GLOBAL}:dashboard_mode"] = dashboard_mode

    zarr_urls = st.query_params.get_all("zarr_urls")
    _zarr_urls = st.session_state.get(f"{Scope.GLOBAL}:zarr_urls", [])
    st.session_state[f"{Scope.GLOBAL}:zarr_urls"] = _zarr_urls + zarr_urls


def setup_global_state():
    """
    Setup the global state for the Streamlit app.
    """
    init_global_state()
    parse_cli_args()
    parse_query_params()

    default_dashboard_mode = st.session_state.get(
        f"{Scope.GLOBAL}:dashboard_mode", "Plates"
    )
    dashboard_mode = st.pills(
        "Dashboard Mode",
        options=["Plates", "Images"],
        default=default_dashboard_mode,
        key="_dashboard_mode",
        help="Select the mode of the dashboard.",
    )
    st.session_state[f"{Scope.GLOBAL}:dashboard_mode"] = dashboard_mode
    return dashboard_mode


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

    dashboard_mode = setup_global_state()
    with st.sidebar:
        token = st.text_input(
            label="Fractal Token",
            value=st.session_state.get(f"{Scope.GLOBAL}:token", ""),
            key="_fractal_token",
            type="password",
        )
        st.session_state[f"{Scope.GLOBAL}:token"] = token

    match dashboard_mode:
        case "Plates":
            features_table, table_name = plate_mode_setup()
        case "Images":
            st.error("Image mode is not yet implemented. Please select 'Plates' mode.")
            st.stop()
        case _:
            st.error(
                f"Invalid dashboard mode selected. Should be 'Plates' or 'Images' but got {dashboard_mode}."
            )
            st.stop()

    schema = features_table.collect_schema()
    if f"{Scope.GLOBAL}:feature_table" in st.session_state:
        old_table_name = st.session_state[f"{Scope.GLOBAL}:feature_table_name"]
        old_schema = st.session_state[f"{Scope.GLOBAL}:feature_table_schema"]
        if old_table_name != table_name:
            # invalidate the old table
            st.info(
                "The feature table name has changed. Please reapply the filters."
            )
            invalidate_session_state(f"{Scope.FILTERS}")

        if old_schema != schema:
            # invalidate the old table
            st.info(
                "The schema of the feature table has changed. Please reapply the filters."
            )
            invalidate_session_state(f"{Scope.FILTERS}")

    st.session_state[f"{Scope.GLOBAL}:feature_table"] = features_table
    st.session_state[f"{Scope.GLOBAL}:feature_table_name"] = table_name
    st.session_state[f"{Scope.GLOBAL}:feature_table_schema"] = schema


if __name__ == "__main__":
    main()
