import copy

import plotly.express as px
import streamlit as st

from fractal_feature_explorer.pages.filters_page._common import FeatureFrame
from fractal_feature_explorer.utils.st_components import (
    selectbox_component,
)


def heat_map_component(
    key: str,
    feature_frame: FeatureFrame,
) -> None:
    features_columns = feature_frame.features
    selected_feature = selectbox_component(
        key=f"{key}:scatter_plot_feature",
        label="**Feature**",
        options=features_columns,
    )

    cathegorical_columns = copy.deepcopy(feature_frame.cathegorical)

    if "column" in cathegorical_columns:
        cathegorical_columns.remove("column")
        cathegorical_columns = ["column"] + cathegorical_columns

    x_axis = selectbox_component(
        key=f"{key}:scatter_plot_x_axis",
        label="**X-axis**",
        options=cathegorical_columns,
    )

    x_axis_index = cathegorical_columns.index(x_axis)
    cathegorical_columns.pop(x_axis_index)

    if "row" in cathegorical_columns:
        cathegorical_columns.remove("row")
        cathegorical_columns = ["row"] + cathegorical_columns

    y_axis = selectbox_component(
        key=f"{key}:scatter_plot_y_axis",
        label="**Y-axis**",
        options=cathegorical_columns,
    )

    y_axis_index = cathegorical_columns.index(y_axis)
    cathegorical_columns.pop(y_axis_index)

    aggregation = st.pills(
        label="**Aggregation**",
        options=["Mean", "Sum", "Median", "Counts"],
        default="Mean",
        key=f"{key}:scatter_plot_aggregation",
        selection_mode="single",
        help="Select the type of aggregation to apply.",
    )
    axes_names = [x_axis, y_axis]
    columns_needed = [selected_feature] + axes_names
    feature_df = feature_frame.table.select(columns_needed).collect()
    feature_df = feature_df.to_pandas()

    df_piv = feature_df.groupby(axes_names, as_index=False)
    if aggregation == "Mean":
        df_piv = df_piv.mean(numeric_only=True)
    elif aggregation == "Sum":
        df_piv = df_piv.sum(numeric_only=True)
    elif aggregation == "Median":
        df_piv = df_piv.median(numeric_only=True)
    elif aggregation == "Counts":
        df_piv = df_piv.count()
    else:
        raise ValueError(f"Unknown aggregation: {aggregation}")

    new_feature_name = f"{selected_feature} {aggregation}"
    df_piv = df_piv.rename(columns={selected_feature: new_feature_name})
    df_piv = df_piv.pivot(index=x_axis, columns=y_axis, values=new_feature_name)
    img = df_piv.to_numpy()
    fig = px.imshow(
        img.T,
        x=df_piv.index.to_list(),
        y=df_piv.columns.to_list(),
        labels={"x": x_axis, "y": y_axis, "color": new_feature_name},
    )

    fig.update_xaxes(  # type: ignore
        type="category", showgrid=True, title=x_axis, tickson="boundaries", ticklen=0
    )
    fig.update_yaxes(  # type: ignore
        type="category", showgrid=True, title=y_axis, tickson="boundaries", ticklen=0
    )
    st.plotly_chart(fig)
