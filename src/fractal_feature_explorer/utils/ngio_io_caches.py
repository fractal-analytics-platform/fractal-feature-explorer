import urllib3
import asyncio
from collections.abc import Iterable
from typing import Literal

import numpy as np
import streamlit as st
from ngio import (
    OmeZarrContainer,
    OmeZarrPlate,
    open_ome_zarr_container,
    open_ome_zarr_plate,
)
from ngio.common import Dimensions, Roi, list_image_tables_async
from ngio.common._zoom import numpy_zoom
from ngio.ome_zarr_meta.ngio_specs import PixelSize
from ngio.tables import MaskingRoiTable
from ngio.utils import fractal_fsspec_store

from pathlib import Path

import fsspec
from ngio.utils import NgioValueError
import urllib3.util
from fractal_feature_explorer.utils import get_fractal_token
from streamlit.logger import get_logger

from fractal_feature_explorer.config import get_config

logger = get_logger(__name__)


def _url_belongs_to_base(url: str, base_url: str) -> bool:
    """
    Check if the url has the same protocol and host as the base_url,
    and if the path of the url is a subpath of the base_url.
    """
    parsed_url = urllib3.util.parse_url(url)
    parsed_base_url = urllib3.util.parse_url(base_url)
    if (parsed_url.scheme, parsed_url.host) != (
        parsed_base_url.scheme,
        parsed_base_url.host,
    ):
        logger.debug(f"Not including token for {url=}, case 1.")
        return False
    elif parsed_url.path is not None and (
        parsed_base_url.path is None
        or not parsed_url.path.startswith(parsed_base_url.path)
    ):
        logger.debug(f"Not including token for {url=}, case 2.")
        return False
    else:
        logger.debug(f"Including token for {url=}.")
        return True


def _include_token_for_url(url: str) -> bool:
    """
    Check if the URL is a valid HTTP Fractal URL.
    """
    config = get_config()
    if config.deployment_type == "production":
        return _url_belongs_to_base(url, config.fractal_data_url)
    else:
        for data_url in config.fractal_data_urls:
            if _url_belongs_to_base(url, data_url):
                logger.debug(f"Including token for {url=}, matched with {data_url=}.")
                return True
        else:
            logger.debug(f"Not including token for {url=}, not a Fractal URL.")
            return False


def is_http_url(url: str) -> bool:
    """Check if the URL is a valid HTTP URL."""
    return url.startswith("http://") or url.startswith("https://")


@st.cache_data
def _get_http_store(
    url: str, fractal_token: str | None = None
) -> fsspec.mapping.FSMap | None:
    """Ping the URL to check if it is reachable."""
    try:
        logger.info(f"Attempting to open URL: {url}")
        store = fractal_fsspec_store(url, fractal_token=fractal_token)
    except NgioValueError as e:
        st.error(e)
        logger.error(e)
        return None
    return store


def get_http_store(
    url: str, fractal_token: str | None = None
) -> fsspec.mapping.FSMap | None:
    """Ping the URL to check if it is reachable."""
    if not _include_token_for_url(url):
        # Do not use a fractal token for non-Fractal URLs
        fractal_token = None

    return _get_http_store(url, fractal_token=fractal_token)


def get_path(url: str) -> str | None:
    """Sanitize the URL by removing the trailing slash."""
    config = get_config()
    if not config.allow_local_paths:
        st.error("Local paths are not allowed in this configuration.")
        logger.error("Local paths are not allowed in this configuration.")
        return None

    if url.startswith("~/"):
        url = url.replace("~", str(Path.home()))

    path = Path(url).resolve()
    if not path.exists():
        st.error(f"Path does not exist: {path}")
        logger.error(f"Path does not exist: {path}")
        return None
    return str(path)


def _get_and_validate_store(
    url: str, fractal_token: str | None = None
) -> fsspec.mapping.FSMap | str | None:
    """Get the store for the given URL."""
    if is_http_url(url):
        return get_http_store(url, fractal_token=fractal_token)

    return get_path(url)


def get_and_validate_store(url: str) -> fsspec.mapping.FSMap | str | None:
    """Get the store for the given URL."""
    fractal_token = get_fractal_token()
    return _get_and_validate_store(url, fractal_token=fractal_token)


@st.cache_resource
def _get_ome_zarr_plate(url: str, fractal_token: str | None = None) -> OmeZarrPlate:
    store = _get_and_validate_store(url, fractal_token=fractal_token)
    if store is None:
        raise ValueError(f"Could not get store for URL: {url}")
    plate = open_ome_zarr_plate(store, cache=True, parallel_safe=False, mode="r")
    return plate


def get_ome_zarr_plate(url: str) -> OmeZarrPlate:
    fractal_token = get_fractal_token()
    return _get_ome_zarr_plate(url, fractal_token=fractal_token)


@st.cache_resource
def _get_ome_zarr_image_container(
    url: str, fractal_token: str | None = None
) -> OmeZarrContainer:
    store = _get_and_validate_store(url, fractal_token=fractal_token)
    if store is None:
        raise ValueError(f"Could not get store for URL: {url}")
    container = open_ome_zarr_container(store, cache=True, mode="r")
    return container


def _get_ome_zarr_container_in_plate(
    url: str, fractal_token: str | None = None
) -> OmeZarrContainer:
    *_plate_url, row, col, path_in_well = url.split("/")
    plate_url = "/".join(_plate_url)
    plate = _get_ome_zarr_plate(plate_url, fractal_token=fractal_token)
    images = asyncio.run(plate.get_images_async())
    path = f"{row}/{col}/{path_in_well}"
    return images[path]


@st.cache_resource
def _get_ome_zarr_container(
    url: str,
    fractal_token: str | None = None,
    mode: Literal["image", "plate"] = "image",
):
    if mode == "plate":
        return _get_ome_zarr_container_in_plate(url, fractal_token=fractal_token)

    return _get_ome_zarr_image_container(url, fractal_token=fractal_token)


def get_ome_zarr_container(
    url: str, mode: Literal["image", "plate"] = "image"
) -> OmeZarrContainer:
    fractal_token = get_fractal_token()
    if mode == "plate":
        return _get_ome_zarr_container_in_plate(url, fractal_token=fractal_token)

    return _get_ome_zarr_image_container(url, fractal_token=fractal_token)


@st.cache_data
def _list_image_tables(
    urls: list[str],
    fractal_token: str | None = None,
    mode: Literal["image", "plate"] = "image",
) -> list[str]:
    images = [
        _get_ome_zarr_container(url, fractal_token=fractal_token, mode=mode)
        for url in urls
    ]
    image_list = asyncio.run(list_image_tables_async(images))
    return image_list


@st.cache_data
def list_image_tables(
    urls: list[str],
    fractal_token: str | None = None,
    mode: Literal["image", "plate"] = "image",
) -> list[str]:
    fractal_token = get_fractal_token()
    return _list_image_tables(
        urls=urls,
        fractal_token=fractal_token,
        mode=mode,
    )


def roi_to_slice_kwargs(
    roi: Roi,
    pixel_size: PixelSize,
    dimensions: Dimensions,
    z_slice: int = 0,
    t_slice: int = 0,
) -> dict[str, slice | int | Iterable[int]]:
    """Convert a WorldCooROI to slice_kwargs."""
    raster_roi = roi.to_pixel_roi(
        pixel_size=pixel_size, dimensions=dimensions
    ).to_slices()

    if dimensions.has_axis(axis_name="z"):
        raster_roi["z"] = z_slice  # type: ignore

    if dimensions.has_axis(axis_name="t"):
        raster_roi["t"] = t_slice  # type: ignore

    return raster_roi  # type: ignore


@st.cache_resource
def _get_masking_roi(
    image_url: str,
    ref_label: str,
    fractal_token: str | None = None,
) -> MaskingRoiTable:
    container = _get_ome_zarr_container(
        image_url,
        fractal_token=fractal_token,
        mode="image",
    )

    for table in container.list_tables(filter_types="masking_roi_table"):
        table = container.get_masking_roi_table(name=table)
        if table.reference_label == ref_label:
            table.set_table_data()
            return table

    label_img = container.get_label(name=ref_label)
    masking_roi = label_img.build_masking_roi_table()
    return masking_roi


@st.cache_data
def _get_image_array(
    image_url: str,
    ref_label: str,
    label: int,
    channel: int,
    z_slice: int = 0,
    t_slice: int = 0,
    level_path: str = "0",
    zoom_factor: float = 1,
    fractal_token: str | None = None,
) -> np.ndarray:
    container = _get_ome_zarr_container(
        image_url,
        fractal_token=fractal_token,
        mode="image",
    )
    image = container.get_image(path=level_path)
    masking_roi = _get_masking_roi(
        image_url=image_url,
        ref_label=ref_label,
        fractal_token=fractal_token,
    )
    roi = masking_roi.get(label=label)
    roi = roi.zoom(zoom_factor=zoom_factor)
    roi_slice = roi_to_slice_kwargs(
        roi=roi,
        pixel_size=image.pixel_size,
        dimensions=image.dimensions,
        z_slice=z_slice,
        t_slice=t_slice,
    )
    image_array = image.get_array(
        mode="numpy",
        c=channel,
        **roi_slice,  # type: ignore
    )
    assert isinstance(image_array, np.ndarray), "Image is not a numpy array"
    return image_array


@st.cache_data
def _get_label_array(
    image_url: str,
    ref_label: str,
    label: int,
    z_slice: int = 0,
    t_slice: int = 0,
    level_path: str = "0",
    zoom_factor: float = 1,
    fractal_token: str | None = None,
) -> np.ndarray:
    container = _get_ome_zarr_container(
        image_url,
        fractal_token=fractal_token,
        mode="image",
    )
    image = container.get_image(path=level_path)
    label_img = container.get_label(
        name=ref_label, pixel_size=image.pixel_size, strict=False
    )
    masking_roi = _get_masking_roi(
        image_url=image_url,
        ref_label=ref_label,
        fractal_token=fractal_token,
    )
    roi = masking_roi.get(label=label)
    roi = roi.zoom(zoom_factor=zoom_factor)
    roi_slice = roi_to_slice_kwargs(
        roi=roi,
        pixel_size=label_img.pixel_size,
        dimensions=label_img.dimensions,
        z_slice=z_slice,
        t_slice=t_slice,
    )
    label_array = label_img.get_array(
        mode="numpy",
        **roi_slice,  # type: ignore
    )
    assert isinstance(label_array, np.ndarray), "Label is not a numpy array"
    return label_array


def get_single_label_image(
    image_url: str,
    ref_label: str,
    label: int,
    channel: int,
    z_slice: int = 0,
    t_slice: int = 0,
    level_path: str = "0",
    show_label: bool = True,
    zoom_factor: float = 1,
) -> np.ndarray:
    """
    Get the region of interest from the image url
    """
    fractal_token = get_fractal_token()
    image_array = _get_image_array(
        image_url=image_url,
        ref_label=ref_label,
        label=label,
        channel=channel,
        z_slice=z_slice,
        t_slice=t_slice,
        level_path=level_path,
        zoom_factor=zoom_factor,
        fractal_token=fractal_token,
    )
    image_array = image_array.squeeze()
    image_array = np.clip(image_array, 0, 255)

    image_rgba = np.empty(
        (image_array.shape[0], image_array.shape[1], 4), dtype=np.uint8
    )
    image_rgba[..., 0:3] = image_array[..., np.newaxis].repeat(3, axis=2)
    image_rgba[..., 3] = 255

    if not show_label:
        return image_rgba

    label_array = _get_label_array(
        image_url=image_url,
        ref_label=ref_label,
        label=label,
        z_slice=z_slice,
        t_slice=t_slice,
        level_path=level_path,
        zoom_factor=zoom_factor,
        fractal_token=fractal_token,
    )

    label_array = label_array.squeeze()
    label_array = np.where(label_array == label, 255, 0)

    # Scale the label array to match the image size
    label_array = numpy_zoom(
        label_array,
        target_shape=image_rgba.shape[:2],
        order=0,  # Always use nearest neighbor for labels
    )

    image_rgba[label_array > 0, 0] = 255

    return image_rgba
