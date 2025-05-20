import copy

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from matplotlib.path import Path
from pydantic import BaseModel, Field

from fractal_explorer.filters_utils.common import FeatureFrame
from fractal_explorer.utils.ngio_caches import (
    get_ome_zarr_container,
    get_single_label_image,
)
from fractal_explorer.utils.st_components import (
    selectbox_component,
    single_slider_component,
)

import polars as pl


@st.dialog("Cell Preview")
def view_point(point: int, feature_df: pl.DataFrame) -> None:
    """
    View the point in the data frame
    """
    point_dict = feature_df.select("image_url", "label", "reference_label").to_dicts()[
        point
    ]
    container = get_ome_zarr_container(
        point_dict["image_url"],
        token=st.session_state.get("token"),
        mode="image",
    )
    image = container.get_image()

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
        token=st.session_state.get("token"),
    )
    st.image(image, use_container_width=True)

    with st.expander("Infos", expanded=False):
        st.write("Image URL: ", point_dict["image_url"])
        st.write("Label: ", point_dict["label"])
        st.write("Reference Label: ", point_dict["reference_label"])


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
        assert len(self.sel_x) == len(self.sel_y), (
            "X and Y coordinates must be the same length"
        )
        if len(self.sel_x) == 0:
            return feature_frame

        table = feature_frame.table.select(self.column_x, self.column_y).collect()
        x_column = table[self.column_x].to_numpy()
        y_column = table[self.column_y].to_numpy()
        poly_verts = np.column_stack((self.sel_x, self.sel_y))
        polygon = Path(poly_verts)
        pts = np.column_stack((x_column, y_column))
        mask = polygon.contains_points(pts)

        filtered_table = feature_frame.table.filter(mask)
        return FeatureFrame(
            table=filtered_table,
            features=feature_frame.features,
            cathegorical=feature_frame.cathegorical,
            others=feature_frame.others,
        )


def scatter_filter_component(
    key: str,
    feature_frame: FeatureFrame,
) -> FeatureFrame:
    """
    Create a scatter filter for the feature frame
    And return the filtered feature frame
    """

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

    with col2:
        feature_lf = feature_frame.table
        feature_df = feature_lf.select(
            x_column, y_column, "image_url", "label", "reference_label"
        ).collect()

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
            st.write(
                "Number of points to display: ", int(perc_samples * feature_df.height)
            )
        else:
            perc_samples = 1.0
            st.write("Number of points to display: ", feature_df.height)

    if do_sampling:
        feature_df = feature_df.sample(n=int(feature_df.height * perc_samples), seed=0)
    x_series = feature_df[x_column]
    y_series = feature_df[y_column]

    if st.session_state.get(f"{key}:scatter_selected_points", None) is not None:
        selected_points = st.session_state[f"{key}:scatter_selected_points"]
    else:
        selected_points = []

    fig = go.Figure()
    fig.add_trace(
        go.Scattergl(
            x=x_series,
            y=y_series,
            mode="markers",
            marker=dict(
                size=5,
            ),
            name="Points",
        )
    )

    if f"{key}:state" in st.session_state:
        state = ScatterFilter.model_validate_json(st.session_state[f"{key}:state"])
        if len(state.sel_x) > 0:
            sel_x = state.sel_x + [state.sel_x[0]]
            sel_y = state.sel_y + [state.sel_y[0]]
            fig.add_trace(
                go.Scattergl(
                    x=sel_x,
                    y=sel_y,
                    mode="lines+markers",  # Shows both lines and markers
                    line=dict(color="orange", width=2),
                    marker=dict(size=8),
                    name="Current Selection",
                )
            )

    event = st.plotly_chart(fig, key=f"{key}:scatter_plot", on_select="rerun")
    selection = event.get("selection")
    if selection is not None:
        is_event_selection = (
            len(selection.get("box", [])) > 0 or len(selection.get("lasso", [])) > 0
        )
        is_click_selection = len(selection.get("point_indices", [])) > 0
        if is_event_selection:
            new_selected_points = selection.get("point_indices", [])
            new_selected_points = [int(i) for i in new_selected_points]

            if set(new_selected_points) != set(selected_points):
                st.session_state[f"{key}:scatter_selected_points"] = new_selected_points

            if len(selection.get("lasso", [])) > 0:
                scatter_state = ScatterFilter(
                    column_x=x_column,
                    column_y=y_column,
                    sel_x=selection.get("lasso", [])[0].get("x", []),
                    sel_y=selection.get("lasso", [])[0].get("y", []),
                )
                st.session_state[f"{key}:state"] = scatter_state.model_dump_json()
            else:
                if f"{key}:state" in st.session_state:
                    del st.session_state[f"{key}:state"]
                    st.rerun()

        elif is_click_selection:
            view_point(
                point=selection.get("point_indices", [])[0],
                feature_df=feature_df,
            )

    st.session_state[f"{key}:type"] = "scatter"
    if f"{key}:state" in st.session_state:
        scatter_state = ScatterFilter.model_validate_json(
            st.session_state[f"{key}:state"]
        )
        return scatter_state.apply(feature_frame=feature_frame)
    scatter_state = ScatterFilter(
        column_x=x_column,
        column_y=y_column,
    )
    st.session_state[f"{key}:state"] = scatter_state.model_dump_json()
    return feature_frame
