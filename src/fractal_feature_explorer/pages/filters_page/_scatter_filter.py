import copy

import numpy as np
import plotly.graph_objects as go
import polars as pl
import streamlit as st
from matplotlib.path import Path
from pydantic import BaseModel, Field

from fractal_feature_explorer.pages.filters_page._common import FeatureFrame
from fractal_feature_explorer.utils.ngio_io_caches import (
    get_ome_zarr_container,
    get_single_label_image,
)
from fractal_feature_explorer.utils.st_components import (
    selectbox_component,
    single_slider_component,
)
from streamlit.logger import get_logger

logger = get_logger(__name__)


def _show_point_info(
    point_dict: dict,
):
    st.write("Image URL: ", point_dict["image_url"])
    st.write("Label: ", point_dict["label"])
    st.write("Reference Label: ", point_dict["reference_label"])
    for key, value in point_dict.items():
        if key not in ["image_url", "label", "reference_label"]:
            st.write(f"{key}: ", value)


@st.dialog("Cell Preview")
def view_point(point: int, feature_df: pl.DataFrame) -> None:
    """
    View the point in the data frame
    """
    point_dict = feature_df.select("image_url", "label", "reference_label").to_dicts()[
        point
    ]
    logger.info(f"Opening point: {point_dict} in dialog")

    try:
        container = get_ome_zarr_container(
            point_dict["image_url"],
            mode="image",
        )
        image = container.get_image()
    except Exception as e:
        logger.error(f"Error opening image: {e}")
        st.error("Error opening image")
        _show_point_info(point_dict)
        return

    channels = container.image_meta.channel_labels
    if len(channels) > 1:
        channel = st.selectbox(
            label="Select channel",
            options=channels,
            index=0,
            help="Select the channel to display",
        )
        channel = channels.index(channel)
    else:
        channel = 0

    if container.is_3d:
        z_slice = st.slider(
            label="Select Z slice",
            min_value=0,
            max_value=image.dimensions.get("z"),
            value=0,
            help="Select the Z slice to display",
        )
    else:
        z_slice = 0

    if container.is_time_series:
        t_slice = st.slider(
            label="Select T slice",
            min_value=0,
            max_value=image.dimensions.get("t"),
            value=0,
            help="Select the T slice to display",
        )
    else:
        t_slice = 0

    show_label = st.toggle(
        label="Show Label", value=True, help="Show the label on the image"
    )

    with st.expander("Advanced Options", expanded=False):
        zoom_factor = st.slider(
            label="Zoom Factor",
            min_value=0.5,
            max_value=10.0,
            value=1.5,
            step=0.1,
            help="Zoom factor for the image",
        )

        level_path = st.selectbox(
            label="Select Level",
            options=container.levels_paths,
            index=0,
            help="Select the level to display",
        )

    try:
        image = get_single_label_image(
            image_url=point_dict["image_url"],
            ref_label=point_dict["reference_label"],
            label=int(point_dict["label"]),
            level_path=level_path,
            channel=channel,
            z_slice=z_slice,
            t_slice=t_slice,
            show_label=show_label,
            zoom_factor=zoom_factor,
        )
        st.image(image, use_container_width=True)
    except Exception as e:
        logger.error(f"Error opening image: {e}")
        st.error("Error opening image")
        _show_point_info(point_dict)
        return

    with st.expander("Infos", expanded=False):
        _show_point_info(point_dict)


class ScatterFilter(BaseModel):
    column_x: str
    column_y: str
    sel_x: list[float] = Field(default_factory=list)
    sel_y: list[float] = Field(default_factory=list)

    # model_config = ConfigDict(
    #   validate_assignment=True,
    # )

    def apply(self, feature_frame: FeatureFrame) -> FeatureFrame:
        """
        Filter the feature frame using the histogram filter
        """
        table = feature_frame.table.select(self.column_x, self.column_y).collect()
        mask = self.compute_selection_mask(table)
        filtered_table = feature_frame.table.filter(mask)
        return FeatureFrame(
            table=filtered_table,
            features=feature_frame.features,
            cathegorical=feature_frame.cathegorical,
            others=feature_frame.others,
        )

    def compute_selection_mask(self, feature_df: pl.DataFrame) -> np.ndarray:
        """
        Compute the selection mask for the feature frame using the histogram filter
        """
        assert len(self.sel_x) == len(self.sel_y), (
            "X and Y coordinates must be the same length"
        )
        if len(self.sel_x) == 0:
            return np.ones(len(feature_df), dtype=bool)

        x_column = feature_df[self.column_x].to_numpy()
        y_column = feature_df[self.column_y].to_numpy()
        poly_verts = np.column_stack((self.sel_x, self.sel_y))
        polygon = Path(poly_verts)
        pts = np.column_stack((x_column, y_column))
        mask = polygon.contains_points(pts)

        return mask

    def apply_to_df(self, feature_df: pl.DataFrame) -> pl.DataFrame:
        """
        Filter the feature frame using the histogram filter
        """
        mask = self.compute_selection_mask(feature_df)
        filtered_table = feature_df.filter(mask)
        return filtered_table


def scatter_filter_component(
    key: str,
    feature_frame: FeatureFrame,
) -> FeatureFrame:
    """
    Create a scatter filter for the feature frame
    And return the filtered feature frame
    """
    if len(feature_frame.features) < 2:
        error_msg = (
            "Not enough features found in the feature table. "
            "At least 2 features are required for the scatter filter."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    col1, col2 = st.columns(2)
    features_columns = feature_frame.features
    with col1:
        x_column = selectbox_component(
            key=f"{key}:scatter_filter_x_column",
            label="Select **X-axis**",
            options=features_columns,
        )
        # remove x_column from the list of options
        _features_columns = copy.deepcopy(features_columns)
        _features_columns.remove(x_column)
        y_column = selectbox_component(
            key=f"{key}:scatter_filter_y_column",
            label="Select **Y-axis**",
            options=_features_columns,
        )
        feature_lf = feature_frame.table
        feature_df = feature_lf.select(
            x_column, y_column, "image_url", "label", "reference_label"
        ).collect()

    with col2:
        do_sampling = st.toggle(
            key=f"{key}:scatter_filter_sampling",
            label="Do sampling",
            value=True,
            help="If the number of points is too high, we will sample the points to display",
        )
        if do_sampling:
            if feature_df.height > 50000:
                default = 50000 / feature_df.height
            else:
                default = 1.0
            perc_samples = single_slider_component(
                key=f"{key}:scatter_filter_num_samples",
                label="Percentage of samples to display",
                min_value=0,
                max_value=1,
                default=default,
                help="Number of samples to display in the scatter plot.",
            )
        else:
            perc_samples = 1.0
            st.write("Number of points to display: ", feature_df.height)

        show_advanced_options = st.toggle(
            key=f"{key}:scatter_filter_advanced_options",
            label="Show advanced options",
            value=False,
            help="Show advanced options for the scatter plot",
        )
        if show_advanced_options:
            point_size = single_slider_component(
                key=f"{key}:scatter_filter_point_size",
                label="Point size",
                min_value=1,
                max_value=20,
                default=4,
                help="Size of the points in the scatter plot.",
            )
            point_size = int(point_size)
            opacity = single_slider_component(
                key=f"{key}:scatter_filter_opacity",
                label="Opacity",
                min_value=0.0,
                max_value=1.0,
                default=0.9,
                help="Opacity of the points in the scatter plot.",
            )
            opacity = float(opacity)
        else:
            point_size = 5
            opacity = 1.0

    if do_sampling:
        feature_df = feature_df.sample(n=int(feature_df.height * perc_samples), seed=0)

    fig = go.Figure()
    fig.update_layout(
        title="Scatter Plot",
        xaxis_title=x_column,
        yaxis_title=y_column,
        showlegend=True,
    )

    if f"{key}:state" in st.session_state:
        state = ScatterFilter.model_validate_json(st.session_state[f"{key}:state"])
        if len(state.sel_x) > 0:
            opacity_factor = 0.2
        else:
            opacity_factor = 1.0
    else:
        state = ScatterFilter(
            column_x=x_column,
            column_y=y_column,
        )
        opacity_factor = 1.0

    fig.add_trace(
        go.Scattergl(
            x=feature_df[x_column],
            y=feature_df[y_column],
            mode="markers",
            marker=dict(
                size=point_size,
                color="#1f77b4",
                opacity=opacity * opacity_factor,
            ),
            name="All Points",
        )
    )

    if len(state.sel_x) > 0:
        logger.info("Adding filtered points to the scatter plot")
        filtered_df = state.apply_to_df(feature_df)
        fig.add_trace(
            go.Scattergl(
                x=filtered_df[x_column],
                y=filtered_df[y_column],
                mode="markers",
                marker=dict(
                    size=point_size,
                    opacity=opacity,
                    color="#1f77b4",
                ),
                name="Selected Points",
            )
        )

        sel_x = state.sel_x + [state.sel_x[0]]
        sel_y = state.sel_y + [state.sel_y[0]]
        fig.add_trace(
            go.Scattergl(
                x=sel_x,
                y=sel_y,
                mode="lines+markers",  # Shows both lines and markers
                line=dict(color="#ff7f0e", width=2),
                marker=dict(size=8, opacity=1),
                name="Current Selection",
            )
        )
    fig.update_xaxes(showgrid=True)  # type: ignore
    fig.update_yaxes(showgrid=True)  # type: ignore

    event = st.plotly_chart(
        fig,
        key=f"{key}:scatter_plot",
        on_select="rerun",
        selection_mode=["points", "lasso"],
    )
    logger.info("Scatter plot created")
    selection = event.get("selection")
    if selection is not None:
        is_event_selection = (
            len(selection.get("box", [])) > 0 or len(selection.get("lasso", [])) > 0
        )
        is_click_selection = len(selection.get("point_indices", [])) > 0
        if is_event_selection:
            if len(selection.get("lasso", [])) > 0:
                if st.button(
                    "Confirm selection", key=f"{key}:confirm_selection", icon="✅"
                ):
                    scatter_state = ScatterFilter(
                        column_x=x_column,
                        column_y=y_column,
                        sel_x=selection.get("lasso", [])[0].get("x", []),
                        sel_y=selection.get("lasso", [])[0].get("y", []),
                    )
                    st.session_state[f"{key}:state"] = scatter_state.model_dump_json()
                    logger.info(f"Adding scatter filter state: {scatter_state}")
                    st.rerun()
            else:
                if f"{key}:state" in st.session_state:
                    logger.info("Removing scatter filter state")
                    del st.session_state[f"{key}:state"]
                    st.rerun()

        elif is_click_selection:
            logger.info("Click selection on the scatter plot")
            view_point(
                point=selection.get("point_indices", [])[0],
                feature_df=feature_df,
            )

    st.session_state[f"{key}:type"] = "scatter"
    if f"{key}:state" in st.session_state:
        scatter_state = ScatterFilter.model_validate_json(
            st.session_state[f"{key}:state"]
        )
        feature_frame = scatter_state.apply(feature_frame=feature_frame)
        logger.info(
            f"Scatter filter applied: {scatter_state.column_x} [{scatter_state.sel_x}, {scatter_state.sel_y}]"
        )
        return feature_frame
    scatter_state = ScatterFilter(
        column_x=x_column,
        column_y=y_column,
    )
    st.session_state[f"{key}:state"] = scatter_state.model_dump_json()
    return feature_frame
