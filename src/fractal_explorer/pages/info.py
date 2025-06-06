import streamlit as st
from streamlit.logger import get_logger
from fractal_feature_explorer.utils import Scope

from fractal_feature_explorer.authentication import verify_authentication

from fractal_feature_explorer.config import get_config

logger = get_logger(__name__)


def main():
    verify_authentication()
    current_email = st.session_state.get(f"{Scope.PRIVATE}:fractal-email", None)
    config = get_config()
    if config.deployment_type == "production":
        st.write("You are currently logged in as a Fractal user.")
        st.write(f"Fractal server URL: {config.fractal_frontend_url}")
        st.write(f"User email: {current_email}.")
    else:
        # FIXME Lorenzo: handle `config.deployment_type="local"` if relevant,
        # or disable the "info" page.
        st.write("This is a local deployment.")


if __name__ == "__main__":
    main()
