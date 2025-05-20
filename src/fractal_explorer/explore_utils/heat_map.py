import copy

import numpy as np
import plotly.express as px
import polars as pl
import streamlit as st

from fractal_explorer.filters_utils.common import FeatureFrame
from fractal_explorer.filters_utils.scatter_filter import view_point
from fractal_explorer.utils.st_components import (
    selectbox_component,
)


def heat_map_component(
    key: str,
    feature_frame: FeatureFrame,
) -> None:
    features_columns = feature_frame.features
    column = selectbox_component(
        key=f"{key}:scatter_plot_x_column",
        label="Select **X-axis**",
        options=features_columns,
    )

    cathegorical_columns = copy.deepcopy(feature_frame.cathegorical)

    if "row" in cathegorical_columns:
        cathegorical_columns.remove("row")
        cathegorical_columns = ["row"] + cathegorical_columns

    x_axis = selectbox_component(
        key=f"{key}:scatter_plot_x_axis",
        label="Select **X-axis**",
        options=cathegorical_columns,
    )

    x_axis_index = feature_frame.cathegorical.index(x_axis)
    cathegorical_columns.pop(x_axis_index)

    if "column" in cathegorical_columns:
        cathegorical_columns.remove("column")
        cathegorical_columns = ["column"] + cathegorical_columns

    y_axis = selectbox_component(
        key=f"{key}:scatter_plot_y_axis",
        label="Select **Y-axis**",
        options=cathegorical_columns,
    )

    aggregation = st.pills(
        label="Aggregation",
        options=["Mean", "Sum", "Median", "Counts"],
        default="Mean",
        key=f"{key}:scatter_plot_aggregation",
        selection_mode="single",
        help="Select the type of aggregation to apply.",
    )
    columns_neeed = [column, x_axis, y_axis]
    feature_df = feature_frame.table.select(columns_neeed).collect()
    feature_df = feature_df.to_pandas()
    df_piv = feature_df.groupby([x_axis, y_axis], as_index=False)
    if aggregation == "Mean":
        df_piv = df_piv.mean(numeric_only=True)
    elif aggregation == "Sum":
        df_piv = df_piv.sum(numeric_only=True)
    elif aggregation == "Median":
        df_piv = df_piv.median(numeric_only=True)
    elif aggregation == "Counts":
        df_piv = df_piv.count()
    else:
        st.stop()

    df_piv = df_piv.pivot(index=x_axis, columns=y_axis, values=column)
    fig = px.imshow(df_piv)
    st.plotly_chart(fig)
