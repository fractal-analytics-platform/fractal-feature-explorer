import numpy as np
import plotly.graph_objects as go
import polars as pl
import streamlit as st
from pydantic import BaseModel, ConfigDict

from fractal_feature_explorer.pages.filters_page._common import FeatureFrame
from fractal_feature_explorer.utils.st_components import (
    double_slider_component,
    number_input_component,
    selectbox_component,
)
from streamlit.logger import get_logger

logger = get_logger(__name__)


class HistogramFilter(BaseModel):
    column: str
    min: float
    max: float

    model_config = ConfigDict(
        validate_assignment=True,
    )

    def apply(self, feature_frame: FeatureFrame) -> FeatureFrame:
        """
        Filter the feature frame using the histogram filter
        """
        filtered_table = feature_frame.table.filter(
            (pl.col(self.column) >= self.min) & (pl.col(self.column) <= self.max)
        )

        return FeatureFrame(
            table=filtered_table,
            features=feature_frame.features,
            cathegorical=feature_frame.cathegorical,
            others=feature_frame.others,
        )


def histogram_filter_component(
    key: str,
    feature_frame: FeatureFrame,
) -> FeatureFrame:
    """
    Create a histogram filter for the feature frame
    And return the filtered feature frame
    """
    if len(feature_frame.features) == 0:
        error_msg = "No features found in the feature table."
        logger.error(error_msg)
        raise ValueError(error_msg)

    col1, col2 = st.columns(2)
    with col1:
        column = selectbox_component(
            key=f"{key}:histogram_filter_column",
            label="Select column to filter",
            options=feature_frame.features,
        )
    with col2:
        num_bins = number_input_component(
            key=f"{key}:histogram_filter_num_bins",
            label="Number of bins",
            min_value=1,
            max_value=1000,
            value=100,
            help="Number of bins for the histogram.",
        )
    values = feature_frame.table.select(column).collect().to_series().to_numpy()
    origin_min = values.min()
    origin_max = values.max()

    min_filter, max_filter = double_slider_component(
        key=f"{key}:histogram_filter_slider",
        label="Select range to filter",
        min_value=origin_min,
        max_value=origin_max,
        help="Select the range to filter the histogram.",
    )
    filtered_values = values[np.logical_and(values >= min_filter, values <= max_filter)]
    # original

    common_bins = dict(
        start=origin_min,
        end=origin_max,
        size=(origin_max - origin_min) / num_bins,
    )

    original_histo = go.Histogram(
        x=values,
        name="Original",
        opacity=0.5,
        xbins=common_bins,
    )
    # filtered
    filtered_histo = go.Histogram(
        x=filtered_values,
        name="Filtered",
        opacity=1,
        xbins=common_bins,
        marker=dict(color="rgba(255, 127, 14, 0.5)", line=dict(color="black", width=1)),
    )
    fig = go.Figure()
    fig.add_trace(original_histo)
    fig.add_trace(filtered_histo)

    fig.update_layout(
        barmode="overlay",
        title="Original vs. Filtered Histogram",
        xaxis_title="Value",
        yaxis_title="Count",
    )
    st.plotly_chart(fig, key=f"{key}:histogram_filter_plot_overlay")
    logger.info("Histogram filter plot created")
    state = HistogramFilter(
        column=column,
        min=min_filter,
        max=max_filter,
    )

    st.session_state[f"{key}:type"] = "histogram"
    st.session_state[f"{key}:state"] = state.model_dump_json()
    feature_frame = state.apply(feature_frame)
    logger.info(f"Histogram filter applied: {state.column} [{state.min}, {state.max}]")
    return feature_frame
