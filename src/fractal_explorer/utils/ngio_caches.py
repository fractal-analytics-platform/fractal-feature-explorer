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
from ngio.ome_zarr_meta.ngio_specs import PixelSize
from ngio.tables import MaskingRoiTable
from ngio.utils import fractal_fsspec_store


@st.cache_resource
def get_ome_zarr_plate(url: str, token: str | None = None) -> OmeZarrPlate:
    is_http = url.startswith("http://") or url.startswith("https://")
    if token is not None and is_http:
        store = fractal_fsspec_store(url, fractal_token=token)
    else:
        store = url
    plate = open_ome_zarr_plate(store, cache=True, parallel_safe=False, mode="r")
    return plate


def _get_ome_zarr_container(url: str, token: str | None = None) -> OmeZarrContainer:
    is_http = url.startswith("http://") or url.startswith("https://")
    if token is not None and is_http:
        store = fractal_fsspec_store(url, fractal_token=token)
    else:
        store = url
    container = open_ome_zarr_container(store, cache=True, mode="r")
    return container


def _get_ome_zarr_container_in_plate_cached(
    url: str, token: str | None = None
) -> OmeZarrContainer:
    *_plate_url, row, col, path_in_well = url.split("/")
    plate_url = "/".join(_plate_url)
    plate = get_ome_zarr_plate(plate_url, token=token)
    images = asyncio.run(plate.get_images_async())
    path = f"{row}/{col}/{path_in_well}"
    return images[path]


@st.cache_resource
def get_ome_zarr_container(
    url: str, token: str | None = None, mode: Literal["image", "plate"] = "image"
) -> OmeZarrContainer:
    if mode == "plate":
        container = _get_ome_zarr_container_in_plate_cached(url, token=token)
    else:
        container = _get_ome_zarr_container(url, token=token)
    return container


@st.cache_data
def list_image_tables(
    urls: list[str],
    token: str | None = None,
    mode: Literal["image", "plate"] = "image",
) -> list[str]:
    images = [get_ome_zarr_container(url, token=token, mode=mode) for url in urls]
    image_list = asyncio.run(list_image_tables_async(images))
    return image_list


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
def get_masking_roi(
    image_url: str,
    ref_label: str,
    token: str | None = None,
) -> MaskingRoiTable:
    container = get_ome_zarr_container(
        image_url,
        token=token,
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
def get_image_array(
    image_url: str,
    ref_label: str,
    label: int,
    channel: int,
    z_slice: int = 0,
    t_slice: int = 0,
    level_path: str = "0",
    zoom_factor: float = 1,
    token: str | None = None,
) -> np.ndarray:
    container = get_ome_zarr_container(
        image_url,
        token=token,
        mode="image",
    )
    image = container.get_image(path=level_path)
    masking_roi = get_masking_roi(
        image_url=image_url,
        ref_label=ref_label,
        token=token,
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
def get_label_array(
    image_url: str,
    ref_label: str,
    label: int,
    z_slice: int = 0,
    t_slice: int = 0,
    level_path: str = "0",
    zoom_factor: float = 1,
    token: str | None = None,
) -> np.ndarray:
    container = get_ome_zarr_container(
        image_url,
        token=token,
        mode="image",
    )
    image = container.get_image(path=level_path)
    label_img = container.get_label(
        name=ref_label, pixel_size=image.pixel_size, strict=False
    )
    masking_roi = get_masking_roi(
        image_url=image_url,
        ref_label=ref_label,
        token=token,
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
    token: str | None = None,
) -> np.ndarray:
    """
    Get the region of interest from the image url
    """
    image_array = get_image_array(
        image_url=image_url,
        ref_label=ref_label,
        label=label,
        channel=channel,
        z_slice=z_slice,
        t_slice=t_slice,
        level_path=level_path,
        zoom_factor=zoom_factor,
        token=token,
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

    label_array = get_label_array(
        image_url=image_url,
        ref_label=ref_label,
        label=label,
        z_slice=z_slice,
        t_slice=t_slice,
        level_path=level_path,
        zoom_factor=zoom_factor,
        token=token,
    )
    label_array = label_array.squeeze()
    label_array = np.where(label_array == label, 255, 0)

    image_rgba[label_array > 0, 0] = 255

    return image_rgba
