import urllib3.util
from fractal_feature_explorer.config import get_config
import urllib3
import streamlit as st
from fractal_feature_explorer.utils import Scope
from streamlit.logger import get_logger


logger = get_logger(__name__)


def _verify_authentication():
    logger.debug("Enter _verify_authentication.")

    config = get_config()

    if config.deployment_type == "local":
        return

    current_email = st.session_state.get(f"{Scope.PRIVATE}:fractal-email", None)
    current_token = st.session_state.get(f"{Scope.PRIVATE}:fractal-token", None)

    if None not in (current_email, current_token):
        logger.info("User session is already authenticated.")
    else:
        logger.info("Proceed with user authentication.")
        # Extract cookie and token from browser
        try:
            cookie = next(
                _cookie.strip()
                for _cookie in st.context.headers["cookie"].split(";")
                if _cookie.strip().startswith(config.fractal_cookie_name)
            )
            token = cookie.split("=")[1]
        except StopIteration:
            msg = "Could not find the expected cookie."
            logger.info(msg)
            raise ValueError(msg)
        except IndexError:
            msg = "Invalid cookie."
            raise ValueError(msg)
        # Get user information from Fractal backend
        logger.info("Now obtain user information.")
        current_user_url = f"{config.fractal_backend_url}/auth/current-user/"

        response = urllib3.request(
            "GET",
            current_user_url,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status == 200:
            email_address = response.json()["email"]
            st.session_state[f"{Scope.PRIVATE}:fractal-email"] = email_address
            st.session_state[f"{Scope.PRIVATE}:fractal-token"] = token
            logger.info("Obtained user information.")
        else:
            msg = f"Could not obtain Fractal user information from {current_user_url}."
            logger.info(msg)
            raise ValueError(msg)


def verify_authentication():
    try:
        _verify_authentication()
    except Exception as e:
        logger.info(f"Authentication failed. Original error: {str(e)}.")
        config = get_config()
        login_url = f"{config.fractal_frontend_url}/auth/login"
        MSG = (
            "You are not authenticated as a Fractal user. "
            f"Please login at {login_url} and "
            "then refresh the current page."
        )
        st.error(MSG)
        st.stop()
