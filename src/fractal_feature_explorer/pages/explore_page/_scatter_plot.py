import copy

import plotly.express as px
import streamlit as st
from streamlit.logger import get_logger
from fractal_feature_explorer.pages.filters_page._common import FeatureFrame
from fractal_feature_explorer.pages.filters_page._scatter_filter import view_point
from fractal_feature_explorer.utils.st_components import (
    selectbox_component,
    single_slider_component,
)

logger = get_logger(__name__)


def scatter_plot_component(
    key: str,
    feature_frame: FeatureFrame,
) -> None:
    """
    Create a scatter plot for the feature frame
    And return the filtered feature frame
    """
    if len(feature_frame.features) < 2:
        error_msg = (
            "Not enough features found in the feature table. "
            "At least 2 features are required for the scatter filter."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    features_columns = feature_frame.features
    x_column = selectbox_component(
        key=f"{key}:scatter_plot_x_column",
        label="**X-axis**",
        options=features_columns,
    )
    # remove x_column from the list of options
    _features_columns = copy.deepcopy(features_columns)
    _features_columns.remove(x_column)
    y_column = selectbox_component(
        key=f"{key}:scatter_plot_y_column",
        label="**Y-axis**",
        options=_features_columns,
    )
    columns_needed = {x_column, y_column, "image_url", "label", "reference_label"}

    with st.expander("Advanced Options", expanded=False):
        do_sampling = st.toggle(
            key=f"{key}:scatter_plot_advanced_options",
            label="Randomly sample points",
            value=True,
        )

        if do_sampling:
            perc_samples = single_slider_component(
                key=f"{key}:scatter_plot_num_samples",
                label="Percentage of samples to display",
                min_value=0,
                max_value=1,
                default=0.1,
                help="Number of samples to display in the scatter plot.",
            )
        else:
            perc_samples = 1.0

        # color
        possible_color_columns = (
            ["--No Color--"]
            + feature_frame.cathegorical
            + feature_frame.protected
            + feature_frame.features
        )
        possible_color_columns = copy.deepcopy(possible_color_columns)
        for col in columns_needed:
            if col in possible_color_columns:
                possible_color_columns.remove(col)

        color_column = selectbox_component(
            key=f"{key}:scatter_plot_color_column",
            label="**Color**",
            options=possible_color_columns,
            help="Select the column to color the points by.",
        )
        if color_column != "--No Color--":
            columns_needed.add(color_column)
        else:
            color_column = None

        # size
        possible_size_columns = ["--No Size--"] + feature_frame.features
        possible_size_columns = copy.deepcopy(possible_size_columns)
        for col in columns_needed:
            if col in possible_size_columns:
                possible_size_columns.remove(col)
        size_column = selectbox_component(
            key=f"{key}:scatter_plot_size_column",
            label="**Size**",
            options=possible_size_columns,
        )
        if size_column != "--No Size--":
            columns_needed.add(size_column)
        else:
            size_column = None

        # marginal x
        marginal_x = selectbox_component(
            key=f"{key}:scatter_plot_marginal_x",
            label="**Marginal X**",
            options=["--No Marginal--", "histogram", "violin"],
        )
        if marginal_x == "--No Marginal--":
            marginal_x = None

        # marginal y
        marginal_y = selectbox_component(
            key=f"{key}:scatter_plot_marginal_y",
            label="**Marginal Y**",
            options=["--No Marginal--", "histogram", "violin"],
        )
        if marginal_y == "--No Marginal--":
            marginal_y = None

    feature_lf = feature_frame.table
    feature_df = feature_lf.select(columns_needed).collect()
    if do_sampling:
        feature_df = feature_df.sample(
            n=int(perc_samples * feature_df.shape[0]), seed=0
        )

    fig = px.scatter(
        data_frame=feature_df,
        x=x_column,
        y=y_column,
        color=color_column,
        size=size_column,
        marginal_x=marginal_x,
        marginal_y=marginal_y,
    )
    fig.update_xaxes(showgrid=True)  # type: ignore
    fig.update_yaxes(showgrid=True)  # type: ignore

    event = st.plotly_chart(fig, key=f"{key}:scatter_plot", on_select="rerun")
    logger.info("Scatter plot created")
    selection = event.get("selection")
    if selection is not None:
        is_event_selection = (
            len(selection.get("box", [])) > 0 or len(selection.get("lasso", [])) > 0
        )
        is_click_selection = (
            not is_event_selection and len(selection.get("point_indices", [])) > 0
        )
        if is_click_selection:
            view_point(
                point=selection.get("point_indices", [])[0],
                feature_df=feature_df,
            )
