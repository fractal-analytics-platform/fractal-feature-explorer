import streamlit as st

from fractal_explorer.utils import Scope
from fractal_explorer.explore_utils import feature_explore_setup


def main():
    st.set_page_config(
        layout="wide",
        page_title="Fractal Plate Explorer",
        page_icon="https://raw.githubusercontent.com/fractal-analytics-platform/fractal-logos/main/common/fractal_favicon.png",
    )
    t_col1, t_col2 = st.columns([1, 5])
    with t_col1:
        st.image(
            "https://raw.githubusercontent.com/fractal-analytics-platform/fractal-logos/main/common/fractal_logo.png",
            width=100,
        )
    with t_col2:
        st.title("Fractal Plate Explorer")

    feature_table = st.session_state.get(f"{Scope.GLOBAL}:feature_table", None)
    feature_table_name = st.session_state.get(f"{Scope.GLOBAL}:feature_table_name", "")
    if feature_table is None:
        st.warning(
            "No feature table found in session state. Please make sure to run the setup page first."
        )
        st.stop()

    st.markdown(
        f"""
        ### Feature Table: {feature_table_name}
        """
    )

    feature_explore_setup(feature_table=feature_table, table_name=feature_table_name)


if __name__ == "__main__":
    main()
