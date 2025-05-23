import polars as pl
import streamlit as st

from fractal_explorer.explore_utils.heat_map import heat_map_component
from fractal_explorer.explore_utils.scatter_plot import scatter_plot_component
from fractal_explorer.filters_page import apply_filters, build_feature_frame
from fractal_explorer.filters_page._common import FeatureFrame
from fractal_explorer.utils import Scope, invalidate_session_state


def _find_unique_name(keys: list[str], prefix: str) -> str:
    """
    Find a unique name for the filter
    """
    i = 1
    while True:
        name = f"{prefix} {i}"
        if name not in keys:
            return name
        i += 1


def add_plot() -> None:
    """
    Dynamically add a plot to the explorer page
    """
    if f"{Scope.EXPLORE}:plots_dict" not in st.session_state:
        st.session_state[f"{Scope.EXPLORE}:plots_dict"] = {}

    plot_type = st.pills(
        label="Plot Type",
        options=["Scatter Plot", "Heat Map"],
        default="Scatter Plot",
        key=f"{Scope.EXPLORE}:plot_type",
        selection_mode="single",
        help="Select the type of plot to add.",
    )

    if st.button("Add New Plot", key=f"{Scope.EXPLORE}:add_plot_button"):
        if plot_type == "Scatter Plot":
            name = _find_unique_name(
                st.session_state[f"{Scope.EXPLORE}:plots_dict"].keys(),
                "Scatter Plot",
            )
            key = f"{Scope.EXPLORE}:{name}_scatter_plot"
            st.session_state[f"{Scope.EXPLORE}:plots_dict"][name] = (
                key,
                scatter_plot_component,
            )
            st.rerun()
        elif plot_type == "Heat Map":
            name = _find_unique_name(
                st.session_state[f"{Scope.EXPLORE}:plots_dict"].keys(),
                "Heat Map",
            )
            key = f"{Scope.EXPLORE}:{name}_heat_map"
            st.session_state[f"{Scope.EXPLORE}:plots_dict"][name] = (
                key,
                heat_map_component,
            )
            st.rerun()

    return None


def display_plots(feature_frame: FeatureFrame) -> FeatureFrame:
    """
    Display the plots in the feature table
    """
    plot_list = st.session_state[f"{Scope.EXPLORE}:plots_dict"]

    for name, (plot_key, plot_component) in plot_list.items():
        st.markdown(
            f"""
            ### {name}
            """
        )
        plot_component(
            key=plot_key,
            feature_frame=feature_frame,
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Reset Plot", key=f"{plot_key}:reset_plot_button", icon="🔄"):
                invalidate_session_state(plot_key)
                st.rerun()
        with col2:
            if st.button(
                "Delete Plot", key=f"{plot_key}:delete_plot_button", icon="🚮"
            ):
                invalidate_session_state(plot_key)
                del plot_list[name]
                st.session_state[f"{Scope.EXPLORE}:plots_dict"] = plot_list
                st.rerun()

    return feature_frame


def feature_explore_setup(feature_table: pl.LazyFrame, table_name: str) -> FeatureFrame:
    """
    Setup the feature table for the dashboard.
    """
    st.markdown(
        f"""
        ## Explore the feature table
        
        Table Name: **{table_name}**
        """
    )
    feature_frame = build_feature_frame(feature_table)
    feature_frame = apply_filters(feature_frame)

    col1, _ = st.columns(2)
    with col1:
        add_plot()

    feature_frame = display_plots(feature_frame)
    return feature_frame
