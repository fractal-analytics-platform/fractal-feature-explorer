import polars as pl
import streamlit as st

from fractal_feature_explorer.pages.filters_page._column_filter import (
    ColumnsFilter,
    columns_filter_component,
)
from fractal_feature_explorer.pages.filters_page._common import FeatureFrame
from fractal_feature_explorer.pages.filters_page._histogram_filter import (
    HistogramFilter,
    histogram_filter_component,
)
from fractal_feature_explorer.pages.filters_page._scatter_filter import (
    ScatterFilter,
    scatter_filter_component,
)
from fractal_feature_explorer.utils import Scope, invalidate_session_state
from streamlit.logger import get_logger
from fractal_feature_explorer.authentication import verify_authentication

logger = get_logger(__name__)


def build_feature_frame(feature_table: pl.LazyFrame) -> FeatureFrame:
    schema = feature_table.collect_schema()

    feature = []
    cathegorical = []
    others = []
    for name, dtype in schema.items():
        if name in [
            "image_url",
            "reference_label",
            "label",
            "row",
            "column",
            "path_in_well",
            "plate_name",
            "image_name",
        ]:
            cathegorical.append(name)
        elif dtype == pl.UInt8() or dtype == pl.String() or dtype == pl.Categorical():
            cathegorical.append(name)
        elif dtype == pl.Boolean():
            cathegorical.append(name)
        elif dtype.is_numeric():
            feature.append(name)
        else:
            others.append(name)

    return FeatureFrame(
        table=feature_table,
        features=feature,
        cathegorical=cathegorical,
        others=others,
    )


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


def add_filters() -> None:
    """
    Dynamically add filters to the feature table
    """
    if f"{Scope.FILTERS}:filters_dict" not in st.session_state:
        st.session_state[f"{Scope.FILTERS}:filters_dict"] = {
            "Columns Filter": (
                f"{Scope.FILTERS}:columns_filter",
                columns_filter_component,
            ),
        }

    filter_type = st.pills(
        label="Filter Type",
        options=["Histogram Filter", "Scatter Filter"],
        default="Histogram Filter",
        key=f"{Scope.FILTERS}:filter_type",
        selection_mode="single",
        help="Select the type of filter to add.",
    )

    if st.button("Add New Filter", key=f"{Scope.FILTERS}:add_filter_button"):
        if filter_type == "Histogram Filter":
            name = _find_unique_name(
                st.session_state[f"{Scope.FILTERS}:filters_dict"].keys(),
                "Histogram Filter",
            )
            key = f"{Scope.FILTERS}:{name}_histogram_filter"
            st.session_state[f"{Scope.FILTERS}:filters_dict"][name] = (
                key,
                histogram_filter_component,
            )
            logger.info(f"New Histogram Filter added: {name}")
            st.rerun()
        elif filter_type == "Scatter Filter":
            name = _find_unique_name(
                st.session_state[f"{Scope.FILTERS}:filters_dict"].keys(),
                "Scatter Filter",
            )
            key = f"{Scope.FILTERS}:{name}_scatter_filter"
            st.session_state[f"{Scope.FILTERS}:filters_dict"][name] = (
                key,
                scatter_filter_component,
            )
            logger.info(f"New Scatter Filter added: {name}")
            st.rerun()

    return None


def display_filters(feature_frame: FeatureFrame) -> FeatureFrame:
    """
    Display the filters in the feature table
    """
    filter_list = st.session_state[f"{Scope.FILTERS}:filters_dict"]

    for name, (filter_key, filter_component) in filter_list.items():
        if "Columns Filter" in name:
            expanded = False
        else:
            expanded = True
        with st.expander(f"{name}", expanded=expanded):
            st.markdown(
                f"""
                ### {name}
                """
            )
            try:
                feature_frame = filter_component(
                    key=filter_key,
                    feature_frame=feature_frame,
                )
            except Exception as e:
                error_msg = (
                    f"Error applying filter {name}: {e}. "
                    "Please check the filter parameters and try again."
                )
                st.error(error_msg)
                logger.error(error_msg)

            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "Reset Filter", key=f"{filter_key}:reset_filter_button", icon="🔄"
                ):
                    invalidate_session_state(filter_key)
                    st.rerun()
            with col2:
                if "Columns Filter" in name:
                    continue
                if st.button(
                    "Delete Filter", key=f"{filter_key}:delete_filter_button", icon="🚮"
                ):
                    invalidate_session_state(filter_key)
                    del filter_list[name]
                    st.session_state[f"{Scope.FILTERS}:filters_dict"] = filter_list
                    st.rerun()

    return feature_frame


def apply_filters(feature_frame: FeatureFrame) -> FeatureFrame:
    """
    Apply the filters to the feature table
    """
    if f"{Scope.FILTERS}:filters_dict" not in st.session_state:
        return feature_frame
    filters_dict = st.session_state[f"{Scope.FILTERS}:filters_dict"]

    for name, (filter_key, filter_component) in filters_dict.items():
        status_key = f"{filter_key}:state"
        type_key = f"{filter_key}:type"

        status_json = st.session_state.get(status_key, None)
        if status_json is None:
            warn_msg = (
                f"Filter {name} has not been applied yet. "
                "Please apply the filter from the filter page first."
            )
            logger.warning(warn_msg)
            st.warning(warn_msg)
            continue

        filter_type = st.session_state.get(type_key, None)
        if filter_type is None:
            warn_msg = (
                f"Filter {name} has not been applied yet. "
                "Please apply the filter from the filter page first."
            )
            logger.warning(warn_msg)
            st.warning(warn_msg)
            continue

        logger.info(f"Applying filter {name} of type {filter_type}")
        if filter_type == "columns":
            filter_component = ColumnsFilter.model_validate_json(status_json)
            feature_frame = filter_component.apply(feature_frame)
        elif filter_type == "histogram":
            filter_component = HistogramFilter.model_validate_json(status_json)
            feature_frame = filter_component.apply(feature_frame)
        elif filter_type == "scatter":
            filter_component = ScatterFilter.model_validate_json(status_json)
            feature_frame = filter_component.apply(feature_frame)
        else:
            st.warning(f"Filter {name} is not found. Please apply the filter first.")
            continue

    logger.info("Filters applied to feature table")
    return feature_frame


def feature_filters_manger(
    feature_table: pl.LazyFrame, table_name: str
) -> FeatureFrame:
    """
    Setup the feature table for the dashboard.
    """
    st.markdown(
        f"""
        ## Feature Table Setup
        Select the features to include in the feature table.
        
        Table Name: **{table_name}**
        """
    )
    feature_frame = build_feature_frame(feature_table)

    col1, _ = st.columns(2)
    with col1:
        add_filters()

    feature_frame = display_filters(feature_frame)
    return feature_frame


def main():
    verify_authentication()
    with st.sidebar:
        with st.expander("Advanced Options", expanded=False):
            if st.button(
                "Reset Filters",
                key=f"{Scope.FILTERS}:reset_filters",
                icon="🔄",
                help="Reset the filters state. This will clear all filters.",
            ):
                invalidate_session_state(f"{Scope.FILTERS}")
                st.rerun()

    feature_table = st.session_state.get(f"{Scope.DATA}:feature_table", None)
    feature_table_name = st.session_state.get(f"{Scope.DATA}:feature_table_name", "")
    if feature_table is None:
        st.warning(
            "No feature table found in session state. Please make sure to run the setup page first."
        )
        st.stop()

    feature_filters_manger(feature_table=feature_table, table_name=feature_table_name)
    logger.info("Filters page loading complete")


if __name__ == "__main__":
    main()
