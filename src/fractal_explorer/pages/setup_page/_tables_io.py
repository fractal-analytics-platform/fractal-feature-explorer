import asyncio

import polars as pl
import streamlit as st
from ngio.common import (
    concatenate_image_tables_async,
    concatenate_image_tables_as_async,
)
from ngio.tables import FeatureTable
from typing import Literal
from fractal_feature_explorer.utils import (
    get_ome_zarr_container,
    get_ome_zarr_plate,
)
from fractal_feature_explorer.pages.setup_page._utils import (
    plate_name_from_url,
    extras_from_url,
)
from ngio.common import list_image_tables_async

from streamlit.logger import get_logger

logger = get_logger(__name__)


def list_plate_tables(
    plate_setup_df: pl.DataFrame,
    filter_types: str = "condition_table",
    mode: Literal["all", "common"] = "common",
) -> list[str]:
    """Collect existing tables from the plate URLs."""
    plate_urls = plate_setup_df["plate_url"].unique().to_list()
    plate_tables = {}

    for url in plate_urls:
        logger.warning(f"Loading plate {url}...")

        plate = get_ome_zarr_plate(url)
        if plate._tables_container is None:
            logger.warning(
                f"Plate {url} does not contain any Plate level tables. Skipping."
            )
            continue
        try:
            list_tables = plate.list_tables(filter_types=filter_types)
            for table_name in list_tables:
                if table_name not in plate_tables:
                    plate_tables[table_name] = []
                plate_tables[table_name].append(url)
            logger.info(f"List of plate tables in {url}: {list_tables}")
        except Exception as e:
            erro_msg = f"Error loading {filter_types} tables from {url}. "
            st.error(erro_msg)
            logger.error(erro_msg)
            raise e

    if mode == "all":
        logger.info(f"List of plate level tables: {plate_tables}")
        return list(plate_tables.keys())
    elif mode == "common":
        common_tables = []
        logger.info(f"List of common plate level tables: {plate_tables}")
        for table_name, urls in plate_tables.items():
            if len(urls) == len(plate_urls):
                common_tables.append(table_name)
        return common_tables
    else:
        raise ValueError(f"Invalid mode {mode}. Must be 'all' or 'common'.")


def list_images_tables(
    plate_setup_df: pl.DataFrame,
    filter_types: str = "condition_table",
    mode: Literal["all", "common"] = "common",
) -> list[str]:
    """Collect existing image tables from the plate URLs."""
    images_urls = plate_setup_df["image_url"].unique().to_list()
    images = [get_ome_zarr_container(url, mode="plate") for url in images_urls]
    images_condition_tables = asyncio.run(
        list_image_tables_async(images=images, filter_types=filter_types, mode=mode)
    )
    if mode == "all":
        logger.info(f"List of image level tables: {images_condition_tables}")
    elif mode == "common":
        logger.info(f"List of common image level tables: {images_condition_tables}")
    return images_condition_tables


# ====================================================================
#
# Condition tables utils
#
# ====================================================================


@st.cache_data
def _load_single_plate_condition_table(
    url: str,
    table_name: str,
) -> pl.DataFrame | None:
    """Load the condition table from a single plate URL."""
    plate = get_ome_zarr_plate(url)
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
def _collect_condition_table_from_plates_cached(
    list_urls: list[str],
    table_name: str,
) -> pl.DataFrame | None:
    """Load the condition table from the plate URLs."""
    condition_tables = []
    for url in list_urls:
        table_df = _load_single_plate_condition_table(url, table_name)
        if table_df is None:
            continue
        condition_tables.append(table_df)

    condition_table = pl.concat(condition_tables)
    return condition_table


@st.cache_data
def _collect_condition_table_from_images_cached(
    list_urls: list[str],
    table_name: str,
    mode: Literal["plate", "image"] = "plate",
) -> pl.DataFrame:
    """Load the condition table from the image URLs."""
    images = [get_ome_zarr_container(url, mode=mode) for url in list_urls]

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
    if mode == "plate":
        condition_table = condition_table.with_columns(
            pl.col("column").cast(pl.Int64),
            pl.col("path_in_well").cast(pl.Utf8),
        )
    return condition_table


def _join_setup_to_condition_table(
    plate_setup_df: pl.DataFrame,
    condition_df: pl.DataFrame,
    on=("plate_name", "row", "column", "path_in_well"),
) -> pl.DataFrame:
    """Join the condition table with the plate setup DataFrame."""
    plate_setup_df = plate_setup_df.join(
        condition_df,
        left_on=on,
        how="inner",
    )
    return plate_setup_df


def collect_condition_table_from_plates(
    plate_setup_df: pl.DataFrame,
    table_name: str,
) -> pl.DataFrame | None:
    """Load the condition table from the plate URLs."""
    plate_urls = plate_setup_df["plate_url"].unique().sort().to_list()
    condition_df = _collect_condition_table_from_plates_cached(plate_urls, table_name)
    if condition_df is None:
        return None
    return _join_setup_to_condition_table(plate_setup_df, condition_df)


def collect_condition_table_from_images(
    plate_setup_df: pl.DataFrame,
    table_name: str,
    on=("plate_name", "row", "column", "path_in_well"),
    mode: Literal["plate", "image"] = "plate",
) -> pl.DataFrame:
    """Load the condition table from the image URLs."""
    images_urls = plate_setup_df["image_url"].unique().sort().to_list()
    condition_df = _collect_condition_table_from_images_cached(
        images_urls, table_name, mode=mode
    )
    return _join_setup_to_condition_table(plate_setup_df, condition_df, on=on)


# ====================================================================
#
# Feature tables utils
#
# ====================================================================


@st.cache_data
def _load_plate_feature_table(
    url: str,
    table_name: str,
) -> pl.DataFrame:
    """Load the feature table from a single plate URL."""
    plate = get_ome_zarr_plate(url)
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
def _collect_feature_table_from_plates_cached(
    list_urls: list[str],
    table_name: str,
) -> pl.DataFrame:
    """Load the feature table from the plate URLs."""
    feature_tables = []
    for url in list_urls:
        table_df = _load_plate_feature_table(url, table_name)
        feature_tables.append(table_df)

    feature_table = pl.concat(feature_tables)
    return feature_table


@st.cache_data
def _collect_feature_table_from_images_cached(
    list_urls: list[str],
    table_name: str,
    mode: Literal["plate", "image"] = "plate",
) -> pl.DataFrame:
    """Load the feature table from the image URLs."""
    images = [get_ome_zarr_container(url, mode="plate") for url in list_urls]

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
    if mode == "plate":
        feature_df = feature_df.with_columns(
            pl.col("column").cast(pl.Int64),
            pl.col("path_in_well").cast(pl.Utf8),
            pl.lit(feature_table.reference_label).alias("reference_label"),
        )
    else:
        feature_df = feature_df.with_columns(
            pl.lit(feature_table.reference_label).alias("reference_label"),
        )
    return feature_df


def _join_feature_table_to_setup(
    plate_setup_df: pl.DataFrame,
    feature_df: pl.DataFrame,
    on=("plate_name", "row", "column", "path_in_well"),
    drop=("plate_url",),
) -> pl.DataFrame:
    """Join the feature table with the plate setup DataFrame."""
    feature_df = feature_df.join(
        plate_setup_df,
        on=on,
        how="inner",
    )
    feature_df = feature_df.drop(drop)
    return feature_df


def collect_feature_table_from_plates(
    plate_setup_df: pl.DataFrame,
    table_name: str,
) -> pl.DataFrame | None:
    """Load the feature table from the plate URLs."""
    plate_urls = plate_setup_df["plate_url"].unique().sort().to_list()
    feature_table = _collect_feature_table_from_plates_cached(plate_urls, table_name)
    if feature_table is None:
        return None
    feature_table = _join_feature_table_to_setup(plate_setup_df, feature_table)
    return feature_table


def collect_feature_table_from_images(
    plate_setup_df: pl.DataFrame,
    table_name: str,
) -> pl.DataFrame:
    """Load the feature table from the image URLs."""
    images_urls = plate_setup_df["image_url"].unique().sort().to_list()
    feature_table = _collect_feature_table_from_images_cached(images_urls, table_name)
    feature_table = _join_feature_table_to_setup(plate_setup_df, feature_table)
    return feature_table
