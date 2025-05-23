import streamlit as st

from fractal_explorer.filters_utils import feature_filters_setup
from fractal_explorer.utils import Scope


def main():
    feature_table = st.session_state.get(f"{Scope.DATA}:feature_table", None)
    feature_table_name = st.session_state.get(f"{Scope.DATA}:feature_table_name", "")
    if feature_table is None:
        st.warning(
            "No feature table found in session state. Please make sure to run the setup page first."
        )
        st.stop()

    feature_filters_setup(feature_table=feature_table, table_name=feature_table_name)


if __name__ == "__main__":
    main()
