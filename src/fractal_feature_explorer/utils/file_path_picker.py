from pathlib import Path

import streamlit as st


@st.dialog("File Picker", width="large")
def _file_path_picker(fpp_base_path: str | None = None) -> None:
    st.title("Simple File Browser")

    # Let the user specify a base directory (defaults to current working directory)
    def on_fpp_base_path_change():
        st.session_state.fpp_base_path = st.session_state.fpp_path_select

    def format_func(path: str | Path) -> str:
        path = str(path)
        if len(path) > 80:
            path = path[-80:]
            return f"..{path}"
        return path

    if fpp_base_path is None:
        fpp_base_path = st.session_state.get("fpp_base_path", str(Path.home()))

    if not isinstance(fpp_base_path, str):
        fpp_base_path = str(fpp_base_path)

    if not Path(fpp_base_path).exists():
        st.error(f"Base directory does not exist: {fpp_base_path}")
        st.rerun(scope="app")

    st.session_state.fpp_base_path = fpp_base_path

    st.write("Pick a file or directory:")
    all_files = [str(f) for f in Path(fpp_base_path).glob("*")]
    all_files = [Path(fpp_base_path), *all_files]

    selected_path = st.selectbox(
        "Select a directory",
        options=all_files,
        index=0,
        format_func=format_func,
        on_change=on_fpp_base_path_change,
        key="fpp_path_select",
    )

    col1, col2, col3, _ = st.columns(4)
    with col1:
        if st.button("Go back"):
            st.session_state.fpp_base_path = str(
                Path(st.session_state.fpp_base_path).parent
            )
            st.rerun(scope="fragment")

    with col2:
        if st.button("Home"):
            st.session_state.fpp_base_path = str(Path.home())
            st.rerun(scope="fragment")

    with col3:
        if st.button("Pick Current Selection"):
            st.session_state.fpp_selected_path = str(selected_path)
            st.rerun(scope="app")

    st.stop()


def file_path_picker(fpp_base_path: str | None = None) -> str | None:
    if st.button("Pick a file"):
        _file_path_picker(fpp_base_path=fpp_base_path)
    file_path = st.session_state.get("fpp_selected_path", None)
    return file_path
