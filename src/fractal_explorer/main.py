import streamlit as st


def main():
    setup_page = st.Page(
        "setup_page/page.py", title="OME-Zarr Setup", icon=":material/settings:"
    )
    filter_page = st.Page(
        "pages/2_filters.py", title="Features Filters", icon=":material/filter:"
    )
    explore_page = st.Page(
        "pages/3_explore.py", title="Explore", icon=":material/search:"
    )
    export_page = st.Page(
        "pages/4_export.py", title="Export", icon=":material/download:"
    )
    pg = st.navigation([setup_page, filter_page, explore_page, export_page])

    pg.run()


if __name__ == "__main__":
    main()
