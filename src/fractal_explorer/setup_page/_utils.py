import streamlit as st

from pathlib import Path

from ngio.utils import fractal_fsspec_store
from ngio.utils import NgioValueError

from streamlit.logger import get_logger

logger = get_logger(__name__)


@st.cache_data
def validate_http_url(url: str, token: str | None) -> bool:
    """Validate the URL by checking if it is a valid HTTP URL."""
    try:
        logger.info(f"Attempting to open URL: {url}")
        fractal_fsspec_store(url, fractal_token=token)
    except NgioValueError as e:
        st.error(e)
        logger.error(e)
        return False
    return True


def sanifiy_http_url(url: str, token: str | None) -> str | None:
    """Sanitize the URL by removing the trailing slash."""
    url = url.replace(" ", "%20")

    if url.endswith("/"):
        url = url[:-1]

    if not validate_http_url(url, token=token):
        return None

    return url


def sanify_path_url(url: str) -> str | None:
    """Sanitize a local path URL."""

    # Remove any leading spaces
    url = url.lstrip(" ")

    # Remove string quotes
    url = url.lstrip('"').rstrip('"')
    url = url.lstrip("'").rstrip("'")

    # If start with a ~, expand the user directory
    if url.startswith("~"):
        url = str(Path.home()) + url[1:]

    path = Path(url).absolute()
    if not path.exists():
        st.error(f"Path {path} does not exist.")
        logger.error(f"Path {path} does not exist.")
        return None

    return str(path)


def sanifiy_url(url: str, token: str | None) -> str | None:
    """Sanitize the URL by removing the trailing slash."""
    if url.startswith("http://") or url.startswith("https://"):
        return sanifiy_http_url(url, token=token)
    else:
        return sanify_path_url(url)


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
