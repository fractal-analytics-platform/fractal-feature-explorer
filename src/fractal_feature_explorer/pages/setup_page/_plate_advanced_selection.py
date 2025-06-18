import polars as pl
import streamlit as st

from fractal_feature_explorer.utils.common import Scope
from fractal_feature_explorer.utils.st_components import (
    double_slider_component,
    multiselect_component,
    pills_component,
    selectbox_component,
)

from fractal_feature_explorer.pages.setup_page._tables_io import (
    list_images_tables,
    list_plate_tables,
    collect_condition_table_from_images,
    collect_condition_table_from_plates,
)

from streamlit.logger import get_logger

logger = get_logger(__name__)


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


# ====================================================================
#
# Row Selection Widget:
# allow the used to select which rows to include in the analysis
#
# ====================================================================


def rows_selection_widget(
    plate_setup_df: pl.DataFrame,
) -> pl.DataFrame:
    """Create a widget for selecting rows."""
    rows = plate_setup_df["row"].unique().sort().to_list()
    rows_names = pills_component(
        key=f"{Scope.SETUP}:plate_setup:row_selection",
        label="Rows",
        options=rows,
        selection_mode="multi",
        help="Select rows to include in the analysis.",
    )

    plate_setup_df = plate_setup_df.filter(pl.col("row").is_in(rows_names))
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
) -> pl.DataFrame:
    """Join the condition table with the plate setup DataFrame."""
    plate_condition_tables = list_plate_tables(
        plate_setup_df, filter_types="condition_table"
    )
    image_condition_tables = list_images_tables(
        plate_setup_df, filter_types="condition_table"
    )
    selected_table, mode = _join_condition_table_widget(
        plate_condition_tables, image_condition_tables
    )
    if selected_table is None:
        return plate_setup_df

    if mode == "plate":
        new_plate_setup_df = collect_condition_table_from_plates(
            plate_setup_df=plate_setup_df,
            table_name=selected_table,
        )
        if new_plate_setup_df is None:
            st.warning(f"Condition table {selected_table} not found in the plates.")
            return plate_setup_df
        return new_plate_setup_df

    return collect_condition_table_from_images(plate_setup_df, selected_table)


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


def into_images_df(plate_setup_df: pl.DataFrame) -> pl.DataFrame:
    """Convert the plate setup DataFrame into a DataFrame of images."""
    plate_setup_df = plate_setup_df.group_by(
        ["plate_url", "row", "column", "path_in_well"]
    ).all()
    for col in plate_setup_df.columns:
        df_c = plate_setup_df[col]
        if df_c.dtype == pl.List and df_c.list.unique().list.len().eq(1).all():
            plate_setup_df = plate_setup_df.with_columns(
                pl.col(col).list.first().alias(col),
            )
    return plate_setup_df


def show_selected_images_widget(images_df: pl.DataFrame):
    """Show the selected images in the plate setup DataFrame."""
    images_df = images_df.drop("plate_url")
    st.dataframe(images_df)
    st.write("Images Selected: ", len(images_df))


def advanced_plate_selection_component(
    plate_setup_df: pl.DataFrame,
) -> pl.DataFrame:
    """Advanced selection of images from a plate."""
    empty_selection_warn_msg = "No plates selected. Please select at least one plate."
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
        st.warning(empty_selection_warn_msg)
        logger.warning(empty_selection_warn_msg)
        st.stop()

    if st.toggle(
        key=f"{Scope.SETUP}:plate_setup:toggle_condition_table",
        label="Load Condition Table",
        value=False,
    ):
        st.markdown("## Condition Tables")
        with st.spinner("Loading condition tables...", show_time=True):
            plate_setup_df = join_condition_tables(plate_setup_df)
            plate_setup_df = filter_based_on_condition(plate_setup_df)

        if plate_setup_df.is_empty():
            st.warning(empty_selection_warn_msg)
            logger.warning(empty_selection_warn_msg)
            st.stop()

    st.markdown("## Final Images Selection")
    images_setup = into_images_df(plate_setup_df)
    show_selected_images_widget(images_setup)

    return images_setup
