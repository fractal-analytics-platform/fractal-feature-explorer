import asyncio

import polars as pl
import streamlit as st
from ngio.common import (
    concatenate_image_tables_as_async,
    concatenate_image_tables_async,
)
from ngio.tables import FeatureTable

from fractal_explorer.utils.common import Scope
from fractal_explorer.utils.ngio_caches import (
    get_ome_zarr_container,
    get_ome_zarr_plate,
    list_image_tables_async,
)
from fractal_explorer.utils.st_components import (
    double_slider_component,
    multiselect_component,
    pills_component,
    selectbox_component,
)


def sanifiy_url(url: str) -> str:
    """Sanitize the URL by removing the trailing slash."""
    url = url.replace(" ", "%20")

    if url.endswith("/"):
        url = url[:-1]
    return url


def plate_name_from_url(plate_url: str) -> str:
    """Get the plate name from the URL."""
    return plate_url.rsplit("/", 1)[-1]


def extras_from_url(image_url: str) -> dict[str, str]:
    """Get the extras from the URL."""
    *_, plate_name, row, column, path_in_well = image_url.split("/")
    return {
        "plate_name": plate_name,
        "row": row,
        "column": column,
        "path_in_well": path_in_well,
    }


def build_plate_setup_df(plate_urls: list[str], token=None) -> pl.DataFrame:
    plates = []
    for plate_url in plate_urls:
        plate_url = sanifiy_url(plate_url)
        plate = get_ome_zarr_plate(plate_url, token=token)
        images_paths = asyncio.run(plate.images_paths_async())
        for path_in_plate in images_paths:
            image_url = f"{plate_url}/{path_in_plate}"
            image_url = sanifiy_url(image_url)
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


def _plate_selection_filter(
    plate_setup_df: pl.DataFrame, plates_names: list[str]
) -> pl.DataFrame:
    """Filter the plate setup DataFrame based on the selected plates."""
    plate_setup_df = plate_setup_df.filter(pl.col("plate_name").is_in(plates_names))
    return plate_setup_df


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
# Row Selection Widget:
# allow the used to select which rows to include in the analysis
#
# ====================================================================


def _row_selection_widget(
    plate_setup_df: pl.DataFrame,
) -> list[str]:
    """Create a widget for selecting rows."""
    rows = plate_setup_df["row"].unique().sort().to_list()
    rows_names = pills_component(
        key=f"{Scope.SETUP}:plate_setup:row_selection",
        label="Rows",
        options=rows,
        selection_mode="multi",
        help="Select rows to include in the analysis.",
    )
    return rows_names


def _row_selection_filter(
    plate_setup_df: pl.DataFrame, rows_names: list[str]
) -> pl.DataFrame:
    """Filter the plate setup DataFrame based on the selected rows."""
    plate_setup_df = plate_setup_df.filter(pl.col("row").is_in(rows_names))
    return plate_setup_df


def rows_selection_widget(
    plate_setup_df: pl.DataFrame,
) -> pl.DataFrame:
    """Create a widget for selecting rows."""
    rows_names = _row_selection_widget(plate_setup_df)
    plate_setup_df = _row_selection_filter(plate_setup_df, rows_names)
    return plate_setup_df


# ====================================================================
#
# Column Selection Widget:
# allow the used to select which columns to include in the analysis
#
# ====================================================================


def _columns_selection_widget(
    plate_setup_df: pl.DataFrame,
) -> list[str]:
    """Create a widget for selecting columns."""
    columns = plate_setup_df["column"].unique().sort().to_list()
    columns_names = pills_component(
        key=f"{Scope.SETUP}:plate_setup:columns_selection",
        label="Columns",
        options=columns,
        selection_mode="multi",
        help="Select columns to include in the analysis.",
    )
    return columns_names


def _columns_selection_filter(
    plate_setup_df: pl.DataFrame, columns_names: list[str]
) -> pl.DataFrame:
    """Filter the plate setup DataFrame based on the selected columns."""
    plate_setup_df = plate_setup_df.filter(pl.col("column").is_in(columns_names))
    return plate_setup_df


def columns_selection_widget(
    plate_setup_df: pl.DataFrame,
) -> pl.DataFrame:
    """Create a widget for selecting columns."""
    columns_names = _columns_selection_widget(plate_setup_df)
    plate_setup_df = _columns_selection_filter(plate_setup_df, columns_names)
    return plate_setup_df


# ====================================================================
#
# Acquisition Selection Widget:
# allow the used to select which acquisitions to include in the analysis
#
# ====================================================================


def _acquisition_selection_widget(
    plate_setup_df: pl.DataFrame,
) -> list[str]:
    """Create a widget for selecting acquisitions."""
    acquisitions = plate_setup_df["path_in_well"].unique().sort().to_list()
    acquisitions_names = pills_component(
        key=f"{Scope.SETUP}:plate_setup:acquisition_selection",
        label="Acquisitions",
        options=acquisitions,
        selection_mode="multi",
        help="Select acquisitions to include in the analysis.",
    )
    return acquisitions_names


def _acquisition_selection_filter(
    plate_setup_df: pl.DataFrame, acquisitions_names: list[str]
) -> pl.DataFrame:
    """Filter the plate setup DataFrame based on the selected acquisitions."""
    plate_setup_df = plate_setup_df.filter(
        pl.col("path_in_well").is_in(acquisitions_names)
    )
    return plate_setup_df


def acquisition_selection_widget(
    plate_setup_df: pl.DataFrame,
) -> pl.DataFrame:
    """Create a widget for selecting acquisitions."""
    acquisitions_names = _acquisition_selection_widget(plate_setup_df)
    plate_setup_df = _acquisition_selection_filter(plate_setup_df, acquisitions_names)
    return plate_setup_df


# ====================================================================
#
# Wells Selection Widget:
# allow the used to select which wells to include in the analysis
#
# ====================================================================


def _wells_selection_widget(
    plate_setup_df: pl.DataFrame,
) -> list[str]:
    """Create a widget for selecting wells."""
    wells = plate_setup_df["well_id"].unique().sort().to_list()
    wells_names = pills_component(
        key=f"{Scope.SETUP}:plate_setup:wells_selection",
        label="Wells",
        options=wells,
        selection_mode="multi",
        help="Select wells to include in the analysis.",
    )
    return wells_names


def _wells_selection_filter(
    plate_setup_df: pl.DataFrame, wells_names: list[str]
) -> pl.DataFrame:
    """Filter the plate setup DataFrame based on the selected wells."""
    plate_setup_df = plate_setup_df.filter(pl.col("well_id").is_in(wells_names))
    return plate_setup_df


def wells_selection_widget(
    plate_setup_df: pl.DataFrame,
) -> pl.DataFrame:
    """Create a widget for selecting wells."""
    plate_setup_df = plate_setup_df.with_columns(
        pl.concat_str(["row", "column"], separator="").alias("well_id"),
    )
    wells_names = _wells_selection_widget(plate_setup_df)
    plate_setup_df = _wells_selection_filter(plate_setup_df, wells_names)
    plate_setup_df = plate_setup_df.drop("well_id")
    return plate_setup_df


# ====================================================================
#
# Find condition tables and join them with the plate setup DataFrame
#
# ====================================================================


def _collect_plate_tables(
    plate_setup_df: pl.DataFrame, token=None, filter_types: str = "condition_table"
) -> list[str]:
    """Collect existing tables from the plate URLs."""
    plate_urls = plate_setup_df["plate_url"].unique().to_list()
    plate_tables = set()

    for url in plate_urls:
        plate = get_ome_zarr_plate(url, token=token)
        if plate._tables_container is None:
            continue
        try:
            plate_tables.update(plate.list_tables(filter_types=filter_types))
        except Exception as e:
            st.warning(f"Error loading {filter_types} tables: {e}")
            continue
    return list(plate_tables)


def _collect_image_tables(
    plate_setup_df: pl.DataFrame, token=None, table_type: str = "condition_table"
) -> list[str]:
    """Collect existing image tables from the plate URLs."""
    images_urls = plate_setup_df["image_url"].unique().to_list()
    images = [
        get_ome_zarr_container(url, token=token, mode="plate") for url in images_urls
    ]
    images_condition_tables = asyncio.run(
        list_image_tables_async(images=images, filter_types=table_type)
    )
    return images_condition_tables


@st.cache_data
def _load_single_plate_condition_table(
    url: str,
    table_name: str,
    token=None,
) -> pl.DataFrame | None:
    """Load the condition table from a single plate URL."""
    plate = get_ome_zarr_plate(url, token=token)
    try:
        table = plate.get_table(table_name)
    except Exception as e:
        st.warning(f"Error loading condition tables: {e}")
        return None
    table_df = table.lazy_frame.collect()
    table_df = table_df.with_columns(
        pl.lit(plate_name_from_url(url)).alias("plate_name"),
        pl.col("column").cast(pl.Int64),
        pl.col("path_in_well").cast(pl.Utf8),
    )

    required_columns = ["row", "column", "path_in_well"]
    for column in required_columns:
        if column not in table_df.columns:
            st.error(
                f"Condition table {table_name} does not contain required column {column}."
            )
            return None
    return table_df


@st.cache_data
def _load_plates_condition_table(
    list_urls: list[str],
    table_name: str,
    token=None,
) -> pl.DataFrame | None:
    """Load the condition table from the plate URLs."""
    condition_tables = []
    for url in list_urls:
        table_df = _load_single_plate_condition_table(url, table_name, token=token)
        if table_df is None:
            continue
        condition_tables.append(table_df)

    condition_table = pl.concat(condition_tables)
    return condition_table


@st.cache_data
def _load_images_condition_table(
    list_urls: list[str],
    table_name: str,
    token=None,
) -> pl.DataFrame:
    """Load the condition table from the image URLs."""
    images = [
        get_ome_zarr_container(url, token=token, mode="plate") for url in list_urls
    ]

    extras = [extras_from_url(url) for url in list_urls]
    # For more efficient loading, we should reimplement this
    # using the streamlit caches
    condition_table = asyncio.run(
        concatenate_image_tables_async(
            images=images,
            extras=extras,
            table_name=table_name,
        )
    )
    condition_table = condition_table.lazy_frame.collect()
    condition_table = condition_table.with_columns(
        pl.col("column").cast(pl.Int64),
        pl.col("path_in_well").cast(pl.Utf8),
    )
    return condition_table


def _join_setup_condition_table(
    plate_setup_df: pl.DataFrame, condition_df: pl.DataFrame
) -> pl.DataFrame:
    """Join the condition table with the plate setup DataFrame."""
    plate_setup_df = plate_setup_df.join(
        condition_df,
        on=["plate_name", "row", "column", "path_in_well"],
        how="inner",
    )
    return plate_setup_df


def _join_plate_condition_table(
    plate_setup_df: pl.DataFrame,
    table_name: str,
    token=None,
) -> pl.DataFrame:
    """Load the condition table from the plate URLs."""
    plate_urls = plate_setup_df["plate_url"].unique().to_list()
    condition_df = _load_plates_condition_table(plate_urls, table_name, token=token)
    if condition_df is None:
        return plate_setup_df

    return _join_setup_condition_table(plate_setup_df, condition_df)


def _join_image_condition_table(
    plate_setup_df: pl.DataFrame,
    table_name: str,
    token=None,
) -> pl.DataFrame:
    """Load the condition table from the image URLs."""
    images_urls = plate_setup_df["image_url"].unique().to_list()
    condition_df = _load_images_condition_table(images_urls, table_name, token=token)
    return _join_setup_condition_table(plate_setup_df, condition_df)


def _join_condition_table_widget(
    table_condition_tables: list[str], image_condition_tables: list[str]
) -> tuple[str | None, str | None]:
    """Create a widget for selecting the condition table."""
    image_condition_tables_suffix = " (Require Agg.)"
    image_condition_tables = [
        f"{t_name}{image_condition_tables_suffix}" for t_name in image_condition_tables
    ]
    condition_tables = (
        ["-- No Condition Table --"] + table_condition_tables + image_condition_tables
    )
    selected_table = selectbox_component(
        key=f"{Scope.SETUP}:plate_setup:condition_table_selection",
        label="Select Condition Table",
        options=condition_tables,
    )
    if selected_table == "-- No Condition Table --":
        return None, None

    if image_condition_tables_suffix in selected_table:
        selected_table = selected_table.replace(image_condition_tables_suffix, "")
        mode = "image"
    else:
        mode = "plate"
    return selected_table, mode


def join_condition_tables(
    plate_setup_df: pl.DataFrame,
    token=None,
) -> pl.DataFrame:
    """Join the condition table with the plate setup DataFrame."""
    plate_condition_tables = _collect_plate_tables(
        plate_setup_df, token=token, filter_types="condition_table"
    )
    image_condition_tables = _collect_image_tables(
        plate_setup_df, token=token, table_type="condition_table"
    )
    selected_table, mode = _join_condition_table_widget(
        plate_condition_tables, image_condition_tables
    )
    if selected_table is None:
        return plate_setup_df

    if mode == "plate":
        return _join_image_condition_table(plate_setup_df, selected_table, token=token)

    return _join_plate_condition_table(plate_setup_df, selected_table, token=token)


# ====================================================================
#
# Filter Based on Condition Tables
# allow the user to filter the images based on the condition tables
#
# ====================================================================


def _numeric_filter_widget(plate_setup_df: pl.DataFrame, column: str) -> pl.DataFrame:
    """Create a widget for filtering numeric columns."""
    series = plate_setup_df[column]

    min_value = series.min()
    max_value = series.max()

    if min_value == max_value:
        return plate_setup_df

    # ignore the type error
    # this is a numeric column

    selected_range = double_slider_component(
        key=f"{Scope.SETUP}:plate_setup:numeric_filter_{column}",
        label=f"Filter {column}:",
        min_value=min_value,  # type: ignore
        max_value=max_value,  # type: ignore
        help=f"Select range to include in the analysis for the column {column}.",
    )

    plate_setup_df = plate_setup_df.filter(
        (pl.col(column) >= selected_range[0]) & (pl.col(column) <= selected_range[1])
    )
    return plate_setup_df


def _boolean_filter_widget(plate_setup_df: pl.DataFrame, column: str) -> pl.DataFrame:
    """Create a widget for filtering boolean columns."""
    selected_value = pills_component(
        key=f"{Scope.SETUP}:plate_setup:boolean_filter_{column}",
        label=f"Filter {column}:",
        options=[True, False],
        selection_mode="multi",
        help=f"Select values to include in the analysis for the column {column}.",
    )
    plate_setup_df = plate_setup_df.filter(pl.col(column).is_in(selected_value))
    return plate_setup_df


def _string_filter_widget(plate_setup_df: pl.DataFrame, column: str) -> pl.DataFrame:
    """Create a widget for filtering string columns."""
    unique_values = plate_setup_df[column].unique().sort().to_list()
    selected_values = multiselect_component(
        key=f"{Scope.SETUP}:plate_setup:string_filter_{column}",
        label=f"Filter {column}:",
        options=unique_values,
        help=f"Select values to include in the analysis for the column {column}.",
    )
    plate_setup_df = plate_setup_df.filter(pl.col(column).is_in(selected_values))
    return plate_setup_df


def filter_based_on_condition(plate_setup_df: pl.DataFrame) -> pl.DataFrame:
    condition_columns = set(plate_setup_df.columns) - set(
        [
            "plate_url",
            "plate_name",
            "row",
            "column",
            "path_in_well",
            "image_url",
        ]
    )

    for column in condition_columns:
        column_series: pl.Series = plate_setup_df[column]
        column_type = column_series.dtype

        if column_type.is_numeric():
            plate_setup_df = _numeric_filter_widget(plate_setup_df, column)
        elif column_type == pl.Boolean:
            plate_setup_df = _boolean_filter_widget(plate_setup_df, column)
        elif column_type == pl.String():
            plate_setup_df = _string_filter_widget(plate_setup_df, column)
        else:
            st.warning(
                f"Column {column} is of type {column_type}. Filtering not supported."
            )

    return plate_setup_df


def _remove_redudant_lists(plate_setup_df: pl.DataFrame) -> pl.DataFrame:
    """Remove redundant lists from the plate setup DataFrame."""
    for col in plate_setup_df.columns:
        df_c = plate_setup_df[col]
        if df_c.dtype == pl.List and df_c.list.unique().list.len().eq(1).all():
            plate_setup_df = plate_setup_df.with_columns(
                pl.col(col).list.first().alias(col),
            )
    return plate_setup_df


def into_images_df(plate_setup_df: pl.DataFrame) -> pl.DataFrame:
    """Convert the plate setup DataFrame into a DataFrame of images."""
    plate_setup_df = plate_setup_df.group_by(
        ["plate_url", "row", "column", "path_in_well"]
    ).all()
    plate_setup_df = _remove_redudant_lists(plate_setup_df)
    if plate_setup_df.is_empty():
        st.warning("No images selected.")
        st.stop()
    return plate_setup_df


def show_selected_images_widget(images_df: pl.DataFrame):
    """Show the selected images in the plate setup DataFrame."""
    images_df = images_df.drop("plate_url")
    st.dataframe(images_df)
    st.write("Images Selected: ", len(images_df))


# ====================================================================
#
# Load feature table
#
# ====================================================================


@st.cache_data
def _load_single_plate_feature_table(
    url: str,
    table_name: str,
    token=None,
) -> pl.DataFrame:
    """Load the feature table from a single plate URL."""
    plate = get_ome_zarr_plate(url, token=token)
    try:
        table = plate.get_table_as(table_name, FeatureTable)
        reference_label = table.reference_label
    except Exception as e:
        st.error(f"Error loading feature tables: {e}")
        raise e

    table_df = table.lazy_frame.collect()
    table_df = table_df.with_columns(
        pl.lit(plate_name_from_url(url)).alias("plate_name"),
        pl.col("column").cast(pl.Int64),
        pl.col("path_in_well").cast(pl.Utf8),
        pl.lit(reference_label).alias("reference_label"),
    )

    required_columns = ["row", "column", "path_in_well"]
    for column in required_columns:
        if column not in table_df.columns:
            st.error(
                f"Feature table {table_name} does not contain required column {column}."
            )
            raise ValueError(
                f"Feature table {table_name} does not contain required column {column}."
            )

    return table_df


@st.cache_data
def _load_plates_feature_table(
    list_urls: list[str],
    table_name: str,
    token=None,
) -> pl.DataFrame:
    """Load the feature table from the plate URLs."""
    feature_tables = []
    for url in list_urls:
        table_df = _load_single_plate_feature_table(url, table_name, token=token)
        feature_tables.append(table_df)

    feature_table = pl.concat(feature_tables)
    return feature_table


@st.cache_data
def _load_images_feature_table(
    list_urls: list[str],
    table_name: str,
    token=None,
) -> pl.DataFrame:
    """Load the feature table from the image URLs."""
    images = [
        get_ome_zarr_container(url, token=token, mode="plate") for url in list_urls
    ]

    extras = [extras_from_url(url) for url in list_urls]
    # For more efficient loading, we should reimplement this
    # using the streamlit caches
    feature_table = asyncio.run(
        concatenate_image_tables_as_async(
            images=images,
            extras=extras,
            table_name=table_name,
            table_cls=FeatureTable,
            mode="lazy",
        )
    )
    feature_df = feature_table.lazy_frame.collect()
    feature_df = feature_df.with_columns(
        pl.col("column").cast(pl.Int64),
        pl.col("path_in_well").cast(pl.Utf8),
        pl.lit(feature_table.reference_label).alias("reference_label"),
    )
    return feature_df


def load_images_feature_table(
    plate_setup_df: pl.DataFrame,
    table_name: str,
    token=None,
) -> pl.DataFrame:
    """Load the feature table from the image URLs."""
    images_urls = plate_setup_df["image_url"].unique().to_list()
    feature_table = _load_images_feature_table(images_urls, table_name, token=token)
    return feature_table


def load_plate_feature_table(
    plate_setup_df: pl.DataFrame,
    table_name: str,
    token=None,
) -> pl.DataFrame:
    """Load the feature table from the plate URLs."""
    plate_urls = plate_setup_df["plate_url"].unique().to_list()
    feature_table = _load_plates_feature_table(plate_urls, table_name, token=token)
    return feature_table


def _feature_table_selection_widget(
    plate_feature_tables: list[str], image_feature_tables: list[str]
) -> tuple[str | None, str | None]:
    """Create a widget for selecting the feature table."""
    image_feature_tables_suffix = " (Require Agg.)"
    image_feature_tables = [
        f"{t_name}{image_feature_tables_suffix}" for t_name in image_feature_tables
    ]
    feature_tables = plate_feature_tables + image_feature_tables
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
    token=None,
) -> tuple[pl.DataFrame, str]:
    """Load the feature table from the plate URLs."""
    plate_feature_tables = _collect_plate_tables(
        plate_setup_df, token=token, filter_types="feature_table"
    )
    image_feature_tables = _collect_image_tables(
        plate_setup_df, token=token, table_type="feature_table"
    )
    selected_table, mode = _feature_table_selection_widget(
        plate_feature_tables, image_feature_tables
    )
    if selected_table is None:
        st.stop()

    with st.spinner("Loading feature table...", show_time=True):
        if mode == "image":
            return load_images_feature_table(
                plate_setup_df, selected_table, token=token
            ), selected_table

        return load_plate_feature_table(
            plate_setup_df, selected_table, token=token
        ), selected_table


def feature_table_setup(
    plate_setup_df: pl.DataFrame,
    token=None,
) -> tuple[pl.DataFrame, str]:
    """Load the feature table from the plate URLs."""
    feature_table, table_name = load_feature_table(plate_setup_df, token=token)
    feature_table = feature_table.join(
        plate_setup_df, on=["plate_name", "row", "column", "path_in_well"], how="inner"
    )
    feature_table = feature_table.drop("plate_url")
    return feature_table, table_name


def features_infos(feature_table: pl.DataFrame, name: str = "Feature Table"):
    """Show the first few features in the feature table."""
    st.write(
        f"Feature table: {name} correctly loaded. "
        f"Contains `{len(feature_table)}` observations and "
        f"`{len(feature_table.columns)}` features."
    )


def plate_mode_setup():
    """Setup the plate mode for the dashboard."""

    st.markdown("## Input Plate URLs")
    global_urls = st.session_state.get(f"{Scope.GLOBAL}:zarr_urls", [])
    token = st.session_state.get(f"{Scope.GLOBAL}:token", None)

    if f"{Scope.SETUP}:plate_setup:urls" not in st.session_state:
        st.session_state[f"{Scope.SETUP}:plate_setup:urls"] = set()

    new_url = st.text_input("Plate URL")
    if st.button("Add Plate URL"):
        # Validate the URL
        try:
            _ = get_ome_zarr_plate(new_url, token=token)
            current_urls = st.session_state[f"{Scope.SETUP}:plate_setup:urls"]
            current_urls.add(new_url)
            st.session_state[f"{Scope.SETUP}:plate_setup:urls"] = current_urls
        except Exception as e:
            st.error(f"Invalid URL: {e}")

    local_urls = st.session_state[f"{Scope.SETUP}:plate_setup:urls"]
    urls = global_urls + list(local_urls)
    urls = list(set(urls))

    if not urls:
        st.warning("No URLs provided. Please provide at least one URL.")
        st.stop()

    st.markdown("## Plates Selection")
    plate_setup_df = build_plate_setup_df(urls, token=token)
    plate_setup_df = plate_name_selection(plate_setup_df)

    with st.expander("Advanced Selection", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            plate_setup_df = rows_selection_widget(plate_setup_df)
        with col2:
            plate_setup_df = columns_selection_widget(plate_setup_df)
        plate_setup_df = acquisition_selection_widget(plate_setup_df)

        if st.toggle(
            key=f"{Scope.SETUP}:plate_setup:toggle_wells_selection",
            label="Select Specific Wells",
            value=False,
        ):
            plate_setup_df = wells_selection_widget(plate_setup_df)

        if plate_setup_df.is_empty():
            st.warning("No images selected.")
            st.stop()

        st.markdown("## Condition Tables")
        with st.spinner("Loading condition tables...", show_time=True):
            plate_setup_df = join_condition_tables(plate_setup_df, token=token)
            plate_setup_df = filter_based_on_condition(plate_setup_df)

        if plate_setup_df.is_empty():
            st.warning("No images selected.")
            st.stop()

        st.markdown("## Final Images Selection")
        images_setup = into_images_df(plate_setup_df)
        show_selected_images_widget(images_setup)

    feature_table, table_name = feature_table_setup(images_setup, token=token)
    st.markdown("## Feature Table Selection")
    features_infos(feature_table, table_name)
    return feature_table.lazy(), table_name
