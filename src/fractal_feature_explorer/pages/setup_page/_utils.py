import streamlit as st

from fractal_feature_explorer.utils import get_and_validate_store, is_http_url
from streamlit.logger import get_logger

logger = get_logger(__name__)


def sanify_http_url(url: str) -> str:
    """Sanitize the URL by removing the trailing slash."""
    url = url.replace(" ", "%20")

    if url.endswith("/"):
        url = url[:-1]
    return url


def sanify_path_url(url: str) -> str:
    """Sanitize a local path URL."""
    # Remove any leading spaces
    url = url.lstrip(" ")

    # Remove string quotes
    url = url.lstrip('"').rstrip('"')
    url = url.lstrip("'").rstrip("'")
    return str(url)


def sanify_and_validate_url(url: str) -> str | None:
    """Sanitize the URL by removing the trailing slash."""
    if len(url) == 0:
        st.error("URL is empty.")
        logger.error("URL is empty.")
        return None

    if is_http_url(url):
        url = sanify_http_url(url)
    else:
        url = sanify_path_url(url)

    store = get_and_validate_store(url)
    if store is None:
        return None

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
