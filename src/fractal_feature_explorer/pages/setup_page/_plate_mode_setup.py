import asyncio

import polars as pl
import streamlit as st

from fractal_feature_explorer.utils.common import Scope
from fractal_feature_explorer.utils.ngio_io_caches import (
    get_ome_zarr_plate,
)
from fractal_feature_explorer.utils.st_components import (
    pills_component,
    selectbox_component,
)


from streamlit.logger import get_logger
from fractal_feature_explorer.pages.setup_page._plate_advanced_selection import (
    advanced_plate_selection_component,
)
from fractal_feature_explorer.pages.setup_page._tables_io import (
    list_images_tables,
    list_plate_tables,
    collect_feature_table_from_images,
    collect_feature_table_from_plates,
)
from fractal_feature_explorer.pages.setup_page._utils import (
    sanify_and_validate_url,
    extras_from_url,
)

logger = get_logger(__name__)

# ====================================================================
#
# Zarr URL Setup:
# allow the user to add Zarr URLs to the DataFrame
#
# ====================================================================


def user_plate_url_input_component():
    """Create a widget for inputting plate URLs."""
    st.markdown("## Input Plate URLs")
    global_urls = st.session_state.get(f"{Scope.SETUP}:zarr_urls", [])
    logger.info(f"Global URLs: {global_urls}")

    if f"{Scope.SETUP}:plate_setup:urls" not in st.session_state:
        st.session_state[f"{Scope.SETUP}:plate_setup:urls"] = set()

    new_url = st.text_input("Plate URL")
    if st.button("Add Plate URL", icon="➕"):
        # Validate the URL
        new_url = sanify_and_validate_url(new_url)
        if new_url is not None:
            try:
                _ = get_ome_zarr_plate(new_url)
                current_urls = st.session_state[f"{Scope.SETUP}:plate_setup:urls"]
                current_urls.add(new_url)
                st.session_state[f"{Scope.SETUP}:plate_setup:urls"] = current_urls
            except Exception as e:
                error_msg = f"Error loading plate at {new_url} \n{e}"
                st.error(error_msg)
                logger.error(error_msg)

    local_urls = st.session_state[f"{Scope.SETUP}:plate_setup:urls"]
    return local_urls


def build_plate_setup_df(plate_urls: list[str]) -> pl.DataFrame:
    plates = []
    for plate_url in plate_urls:
        plate_url = sanify_and_validate_url(plate_url)
        if plate_url is None:
            continue
        plate = get_ome_zarr_plate(plate_url)
        images_paths = asyncio.run(plate.images_paths_async())
        for path_in_plate in images_paths:
            image_url = f"{plate_url}/{path_in_plate}"
            image_url = sanify_and_validate_url(image_url)
            if image_url is None:
                continue
            extras = extras_from_url(image_url)
            plates.append(
                {
                    "image_url": image_url,
                    "plate_url": plate_url,
                    **extras,
                }
            )

    plate_setup_df = pl.DataFrame(
        plates,
        schema={
            "plate_url": pl.Utf8(),
            "plate_name": pl.Utf8(),
            "row": pl.Utf8(),
            "column": pl.Int64(),
            "path_in_well": pl.Utf8(),
            "image_url": pl.Utf8(),
        },
    )
    return plate_setup_df


# ====================================================================
#
# Plate Selection Widget:
# allow the used to select which plates to include in the analysis
#
# ====================================================================


def plate_name_selection(
    plate_setup_df: pl.DataFrame,
) -> pl.DataFrame:
    """Create a widget for selecting plates."""

    plate_names = plate_setup_df["plate_name"].unique().sort().to_list()
    plate_urls = plate_setup_df["plate_url"].unique().sort().to_list()

    plates = {}
    if len(plate_urls) == len(plate_names):
        for plate_url, plate_name in zip(plate_urls, plate_names, strict=True):
            plates[plate_url] = plate_name
    else:
        st.warning(
            "The plate names are not unique. The url is used to identify the plate."
        )
        logger.warning(
            "The plate names are not unique. The url is used to identify the plate."
        )
        for plate_url in plate_urls:
            plates[plate_url] = plate_url

    selected_plates_names = pills_component(
        key=f"{Scope.SETUP}:plate_setup:plate_selection",
        label="Plates",
        options=list(plates.values()),
        selection_mode="multi",
        help="Select plates to include in the analysis.",
    )

    selected_plate_urls = []
    for plate_url, plate_name in plates.items():
        if plate_name in selected_plates_names:
            selected_plate_urls.append(plate_url)
    plate_setup_df = plate_setup_df.filter(
        pl.col("plate_url").is_in(selected_plate_urls)
    )
    return plate_setup_df


# ====================================================================
#
# Load feature table
#
# ====================================================================


def _feature_table_selection_widget(
    plate_feature_tables: list[str], image_feature_tables: list[str]
) -> tuple[str, str]:
    """Create a widget for selecting the feature table."""
    image_feature_tables_suffix = " (Require Agg.)"
    image_feature_tables = [
        f"{t_name}{image_feature_tables_suffix}" for t_name in image_feature_tables
    ]
    feature_tables = plate_feature_tables + image_feature_tables

    if len(feature_tables) == 0:
        error_msg = "No feature table is common to the selected plates/images."
        st.error(error_msg)
        logger.error(error_msg)
        st.stop()

    selected_table = selectbox_component(
        key=f"{Scope.SETUP}:feature_table_selection",
        label="Select Feature Table",
        options=feature_tables,
        help="Select the feature table to join with the plate setup DataFrame.",
    )

    if image_feature_tables_suffix in selected_table:
        selected_table = selected_table.replace(image_feature_tables_suffix, "")
        mode = "image"
    else:
        mode = "plate"
    return selected_table, mode


def load_feature_table(
    plate_setup_df: pl.DataFrame,
) -> tuple[pl.DataFrame, str]:
    """Load the feature table from the plate URLs."""
    plate_feature_tables = list_plate_tables(
        plate_setup_df, filter_types="feature_table"
    )
    image_feature_tables = list_images_tables(
        plate_setup_df, filter_types="feature_table"
    )

    selected_table, mode = _feature_table_selection_widget(
        plate_feature_tables, image_feature_tables
    )

    with st.spinner("Loading feature table...", show_time=True):
        if mode == "image":
            feature_table = collect_feature_table_from_images(
                plate_setup_df, selected_table
            )
            return feature_table, selected_table

        feature_table = collect_feature_table_from_plates(
            plate_setup_df, selected_table
        )
        if feature_table is None:
            st.error(f"Feature table `{selected_table}` not found in the plate URLs.")
            logger.error(
                f"Feature table `{selected_table}` not found in the plate URLs."
            )
            st.stop()
        return feature_table, selected_table


def features_infos(feature_table: pl.DataFrame, name: str = "Feature Table"):
    """Show the first few features in the feature table."""
    st.write(
        f"Feature table: {name} correctly loaded. "
        f"Contains `{len(feature_table)}` observations and "
        f"`{len(feature_table.columns)}` features."
    )


# ====================================================================
#
# Plate Mode Setup:
# allow the user to add Zarr URLs to the DataFrame
#
# ====================================================================


def plate_mode_setup_component():
    """Setup the plate mode for the dashboard."""
    global_urls = st.session_state.get(f"{Scope.SETUP}:zarr_urls", [])

    local_urls = user_plate_url_input_component()
    logger.info(f"Local URLs: {local_urls}")
    urls = global_urls + list(local_urls)
    urls = list(set(urls))

    if not urls:
        error_msg = "No URLs provided. Please provide at least one URL."
        st.error(error_msg)
        logger.error(error_msg)
        st.stop()

    st.markdown("## Plates Selection")
    plate_setup_df = build_plate_setup_df(urls)
    plate_setup_df = plate_name_selection(plate_setup_df)

    empty_selection_warn_msg = "No plates selected. Please select at least one plate."
    if plate_setup_df.is_empty():
        st.warning(empty_selection_warn_msg)
        logger.warning(empty_selection_warn_msg)
        st.stop()

    with st.expander("Advanced Selection", expanded=False):
        images_setup = advanced_plate_selection_component(plate_setup_df)

    st.markdown("## Feature Table Selection")
    feature_table, table_name = load_feature_table(images_setup)
    features_infos(feature_table, table_name)
    return feature_table.lazy(), table_name
