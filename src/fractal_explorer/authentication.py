from fractal_explorer.utils.config import get_config
import requests
import streamlit as st
from fractal_explorer.utils import Scope
from streamlit.logger import get_logger


logger = get_logger(__name__)


def verify_authentication():
    config = get_config()

    if config.skip_authentication:
        return

    MUST_LOGIN_MESSAGE = f"Login at {config.fractal_login_url} and come back here."

    current_email = st.session_state.get(f"{Scope.PRIVATE}:fractal-email", None)
    current_token = st.session_state.get(f"{Scope.PRIVATE}:fractal-token", None)

    if None not in (current_email, current_token):
        logger.info("User session is already authenticated.")
    else:
        logger.info(f"Proceed with user authentication {config=}.")
        # Extract cookie and token from browser
        try:
            cookie = next(
                _cookie.strip()
                for _cookie in st.context.headers["cookie"].split(";")
                if _cookie.strip().startswith(config.fractal_cookie_name)
            )
            token = cookie.split("=")[1]
        except StopIteration:
            raise ValueError(
                f"Could not find the expected cookie.\n{MUST_LOGIN_MESSAGE}"
            )
        except IndexError:
            raise ValueError(f"Invalid cookie.\n{MUST_LOGIN_MESSAGE}")
        # Get user information from Fractal backend
        logger.info("Now obtain user information.")
        response = requests.get(
            f"{config.fractal_backend_url}/auth/current-user/",
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.ok:
            st.session_state[f"{Scope.PRIVATE}:fractal-email"] = response.json()[
                "email"
            ]
            st.session_state[f"{Scope.PRIVATE}:fractal-token"] = token
            logger.info("Obtained user information.")
        else:
            raise ValueError(
                f"Could not obtain Fractal user information.\n{MUST_LOGIN_MESSAGE}"
            )