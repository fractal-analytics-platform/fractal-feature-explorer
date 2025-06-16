import streamlit as st
import fractal_feature_explorer
import ngio
from fractal_feature_explorer.config import get_config
from pathlib import Path


def main():
    icon_path = Path(__file__).parent / "resources" / "fractal_favicon.png"
    logo_path = Path(__file__).parent / "resources" / "fractal_logo.png"

    st.set_page_config(
        layout="wide",
        page_title="Fractal Plate Explorer",
        page_icon=icon_path,
    )
    t_col1, t_col2 = st.columns([1, 5])
    with t_col1:
        st.image(logo_path, width=100)
    with t_col2:
        st.title("Fractal Explorer")

    footer_style = """
    <style>
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #f0f2f6;
            text-align: center;
            padding: 10px;
            font-size: 0.9em;
            color: #6c757d;
        }
    </style>
    """

    footer_content = f"""
    <div class='footer'>
        Fractal Explorer Version: {fractal_feature_explorer.__version__} |
        ngio Version: {ngio.__version__} |
        © Copyright 2025 University of Zurich (see LICENSE file for details)
    </div>
    """
    st.markdown(f"{footer_style}{footer_content}", unsafe_allow_html=True)

    setup_page = st.Page(
        "pages/setup_page/setup_page.py",
        title="OME-Zarr Setup",
        icon=":material/settings:",
    )
    filter_page = st.Page(
        "pages/filters_page/filters_page.py",
        title="Features Filters",
        icon=":material/filter:",
    )
    explore_page = st.Page(
        "pages/explore_page/explore_page.py", title="Explore", icon=":material/search:"
    )
    export_page = st.Page(
        "pages/export_page.py", title="Export", icon=":material/download:"
    )

    pages = [setup_page, filter_page, explore_page, export_page]
    config = get_config()
    if config.deployment_type == "production":
        user_info_page = st.Page("pages/info.py", title="Info", icon=":material/info:")
        pages.append(user_info_page)

    pg = st.navigation(pages)
    pg.run()


if __name__ == "__main__":
    main()
