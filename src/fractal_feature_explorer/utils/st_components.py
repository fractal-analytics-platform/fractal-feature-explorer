from typing import Literal

import streamlit as st
from pydantic import BaseModel, ConfigDict, model_validator
from streamlit.logger import get_logger

logger = get_logger(__name__)


class PillsState(BaseModel):
    options: list
    default: list

    model_config = ConfigDict(
        validate_assignment=True,
    )

    @model_validator(mode="after")
    def check_model(self):
        # default should be a subset of options
        # if not set default to the intersection of options and default
        if not set(self.default).issubset(set(self.options)):
            self.default = list(set(self.options).intersection(set(self.default)))
        return self


def pills_component(
    key: str,
    label: str,
    options: list,
    selection_mode: Literal["multi", "single"] = "multi",
    help: str | None = None,
) -> list:
    """Wrapper for the streamlit.pills component.

    This function handles the session state for the pills component.
    A unique key is required for each pills component.
    """
    if f"{key}_state_model" not in st.session_state:
        pills_model = PillsState(
            options=options,
            default=options,
        )
        st.session_state[f"{key}_state_model"] = pills_model.model_dump_json()
    else:
        pills_model = PillsState.model_validate_json(
            st.session_state[f"{key}_state_model"]
        )
        pills_model.options = options
        if len(pills_model.default) == 0 and len(options) > 0:
            pills_model.default = [options[0]]

    def _update_session_state():
        pills_model.default = st.session_state[key]
        st.session_state[f"{key}_state_model"] = pills_model.model_dump_json()

    selected_options = st.pills(
        label=label,
        options=pills_model.options,
        default=pills_model.default,
        selection_mode=selection_mode,
        help=help,
        key=key,
        on_change=_update_session_state,
    )

    if selected_options is None:
        selected_options = []
    if not isinstance(selected_options, list):
        selected_options = [selected_options]

    return selected_options


class SelectBoxState(BaseModel):
    options: list
    index: int = 0

    model_config = ConfigDict(
        validate_assignment=True,
    )

    @model_validator(mode="after")
    def check_model(self):
        # index should be less than the length of options
        if len(self.options) == 0:
            return self

        if self.index >= len(self.options):
            self.index = 0
        return self


def selectbox_component(
    key: str,
    label: str,
    options: list[str],
    help: str | None = None,
) -> str:
    """Wrapper for the streamlit.selectbox component.
    This function handles the session state for the selectbox component.
    A unique key is required for each selectbox component.
    """

    if len(options) == 0:
        raise ValueError(
            "Selectbox options are empty. Selectbox cannot be created with an empty list."
        )

    if f"{key}_state_model" not in st.session_state:
        selectbox_model = SelectBoxState(
            options=options,
        )
        st.session_state[f"{key}_state_model"] = selectbox_model.model_dump_json()
    else:
        selectbox_model = SelectBoxState.model_validate_json(
            st.session_state[f"{key}_state_model"]
        )
        selectbox_model.options = options

    def _update_session_state():
        selected_option = st.session_state[key]
        selectbox_model.index = selectbox_model.options.index(selected_option)
        st.session_state[f"{key}_state_model"] = selectbox_model.model_dump_json()

    selected_option = st.selectbox(
        label=label,
        options=selectbox_model.options,
        index=selectbox_model.index,
        help=help,
        key=key,
        on_change=_update_session_state,
    )

    return selected_option


class MultiSelectState(BaseModel):
    options: list
    default: list

    model_config = ConfigDict(
        validate_assignment=True,
    )

    @model_validator(mode="after")
    def check_model(self):
        # default should be a subset of options
        # if not set default to the intersection of options and default
        if not set(self.default).issubset(set(self.options)):
            self.default = self.options
        return self


def multiselect_component(
    key: str,
    label: str,
    options: list,
    help: str | None = None,
) -> list:
    """Wrapper for the streamlit.multiselect component.
    This function handles the session state for the multiselect component.
    A unique key is required for each multiselect component.
    """
    if f"{key}_state_model" not in st.session_state:
        multiselect_model = MultiSelectState(
            options=options,
            default=options,
        )
        st.session_state[f"{key}_state_model"] = multiselect_model.model_dump_json()
    else:
        multiselect_model = MultiSelectState.model_validate_json(
            st.session_state[f"{key}_state_model"]
        )
        multiselect_model.options = options
        if len(multiselect_model.default) == 0 and len(options) > 0:
            multiselect_model.default = [options[0]]

    def _update_session_state():
        multiselect_model.default = st.session_state[key]
        st.session_state[f"{key}_state_model"] = multiselect_model.model_dump_json()

    selected_options = st.multiselect(
        label=label,
        options=multiselect_model.options,
        default=multiselect_model.default,
        help=help,
        key=key,
        on_change=_update_session_state,
    )

    return selected_options


class SliderState(BaseModel):
    min_value: float
    max_value: float
    value: float | tuple[float, float]

    model_config = ConfigDict(
        validate_assignment=True,
    )

    @model_validator(mode="after")
    def check_model(self):
        # value should be between min_value and max_value
        if isinstance(self.value, tuple):
            if self.value[0] < self.min_value or self.value[1] > self.max_value:
                self.value = (self.min_value, self.max_value)
        else:
            if self.value < self.min_value or self.value > self.max_value:
                self.value = (self.min_value + self.max_value) / 2
        return self


def _slider_component(
    key: str,
    label: str,
    min_value: float,
    max_value: float,
    value: float | tuple[float, float],
    help: str | None = None,
) -> float | tuple[float, float]:
    """Wrapper for the streamlit.slider component.
    This function handles the session state for the slider component.
    A unique key is required for each slider component.
    """
    if f"{key}_state_model" not in st.session_state:
        slider_model = SliderState(
            min_value=min_value,
            max_value=max_value,
            value=value,
        )
        st.session_state[f"{key}_state_model"] = slider_model.model_dump_json()
    else:
        slider_model = SliderState.model_validate_json(
            st.session_state[f"{key}_state_model"]
        )
        slider_model.min_value = min_value
        slider_model.max_value = max_value

    def _update_session_state():
        slider_model.value = st.session_state[key]
        st.session_state[f"{key}_state_model"] = slider_model.model_dump_json()

    selected_option = st.slider(
        label=label,
        min_value=slider_model.min_value,
        max_value=slider_model.max_value,
        value=slider_model.value,
        help=help,
        key=key,
        on_change=_update_session_state,
    )

    return selected_option


def double_slider_component(
    key: str,
    label: str,
    min_value: float,
    max_value: float,
    help: str | None = None,
) -> tuple[float, float]:
    """Wrapper for the streamlit.slider component.
    This function handles the session state for the slider component.
    A unique key is required for each slider component.
    """
    range_values = _slider_component(
        key=key,
        label=label,
        min_value=min_value,
        max_value=max_value,
        value=(min_value, max_value),
        help=help,
    )
    if not isinstance(range_values, tuple):
        raise ValueError(
            f"Expected a tuple for the range values, got {type(range_values)}"
        )

    return range_values


def single_slider_component(
    key: str,
    label: str,
    min_value: float,
    max_value: float,
    default: float | None = None,
    help: str | None = None,
) -> float:
    """Wrapper for the streamlit.slider component.
    This function handles the session state for the slider component.
    A unique key is required for each slider component.
    """
    default_value = default if default is not None else (min_value + max_value) / 2
    value = _slider_component(
        key=key,
        label=label,
        min_value=min_value,
        max_value=max_value,
        value=default_value,
        help=help,
    )
    if isinstance(value, tuple):
        raise ValueError(f"Expected a single value for the slider, got {type(default)}")
    return value


class NumberInputState(BaseModel):
    min_value: float | int
    max_value: float | int
    value: float | int

    model_config = ConfigDict(
        validate_assignment=True,
    )

    @model_validator(mode="after")
    def check_model(self):
        # value should be between min_value and max_value
        if self.value < self.min_value or self.value > self.max_value:
            _value = (self.min_value + self.max_value) / 2
            if isinstance(self.value, int):
                _value = int(_value)
            self.value = _value
        return self


def number_input_component(
    key: str,
    label: str,
    min_value: float | int,
    max_value: float | int,
    value: float | int,
    step: float | int = 1,
    help: str | None = None,
) -> float | int:
    """Wrapper for the streamlit.number_input component.
    This function handles the session state for the number input component.
    A unique key is required for each number input component.
    """
    if f"{key}_state_model" not in st.session_state:
        number_input_model = NumberInputState(
            min_value=min_value,
            max_value=max_value,
            value=value,
        )
        st.session_state[f"{key}_state_model"] = number_input_model.model_dump_json()
    else:
        number_input_model = NumberInputState.model_validate_json(
            st.session_state[f"{key}_state_model"]
        )
        number_input_model.min_value = min_value
        number_input_model.max_value = max_value

    def _update_session_state():
        number_input_model.value = st.session_state[key]
        st.session_state[f"{key}_state_model"] = number_input_model.model_dump_json()

    selected_option = st.number_input(
        label=label,
        min_value=number_input_model.min_value,
        max_value=number_input_model.max_value,
        value=number_input_model.value,
        help=help,
        key=key,
        step=step,
        on_change=_update_session_state,
    )

    return selected_option
