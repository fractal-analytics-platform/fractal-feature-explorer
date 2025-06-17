import io

import polars as pl
import streamlit as st

from fractal_feature_explorer.pages.filters_page import (
    apply_filters,
    build_feature_frame,
)
from fractal_feature_explorer.utils import Scope
from fractal_feature_explorer.authentication import verify_authentication


def table_to_csv_buffer(table: pl.LazyFrame) -> io.BytesIO:
    """
    Convert a Polars DataFrame to a CSV buffer.
    """
    _table = table.collect()
    buffer = io.BytesIO()
    _table.write_csv(buffer)
    buffer.seek(0)
    return buffer


def table_to_parquet_buffer(table: pl.LazyFrame) -> io.BytesIO:
    """
    Convert a Polars DataFrame to a Parquet buffer.
    """
    _table = table.collect()
    buffer = io.BytesIO()
    _table.write_parquet(buffer)
    buffer.seek(0)
    return buffer


def main():
    verify_authentication()
    feature_table = st.session_state.get(f"{Scope.DATA}:feature_table", None)
    feature_table_name = st.session_state.get(f"{Scope.DATA}:feature_table_name", "")
    if feature_table is None:
        st.warning(
            "No feature table found in session state. Please make sure to run the setup page first."
        )
        st.stop()

    export_format = st.pills(
        label="Select Export Format",
        options=["CSV", "Parquet"],
        default=None,
        help="Select the format to export the Table.",
    )

    if export_format is None:
        st.warning("Please select an export format to download the filtered data.")
        st.stop()

    if st.toggle(
        label="Apply Filters",
        value=True,
        help="Toggle to apply filters to the feature table.",
    ):
        feature_frame = build_feature_frame(
            feature_table,
        )
        feature_table = apply_filters(feature_frame=feature_frame).table

    if export_format == "CSV":
        file = table_to_csv_buffer(feature_table)
        st.download_button(
            label="Download Filtered Data as CSV",
            data=file,
            file_name=f"{feature_table_name}_filtered.csv",
            mime="text/csv",
            on_click="ignore",
            icon="📥",
        )
    elif export_format == "Parquet":
        file = table_to_parquet_buffer(feature_table)
        st.download_button(
            label="Download Filtered Data as Parquet",
            data=file,
            file_name=f"{feature_table_name}_filtered.parquet",
            mime="application/octet-stream",
            on_click="ignore",
            icon="📥",
        )


if __name__ == "__main__":
    main()
