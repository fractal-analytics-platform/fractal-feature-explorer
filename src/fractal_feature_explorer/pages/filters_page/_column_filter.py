import streamlit as st
from pydantic import BaseModel, ConfigDict

from fractal_feature_explorer.pages.filters_page._common import FeatureFrame
from fractal_feature_explorer.utils.st_components import (
    multiselect_component,
)


class ColumnsFilter(BaseModel):
    features: list[str]
    cathegorical: list[str]
    others: list[str]

    model_config = ConfigDict(
        validate_assignment=True,
    )

    def apply(self, feature_frame: FeatureFrame) -> FeatureFrame:
        """
        Filter the feature frame using the columns filter
        """
        all_columns = set(
            self.features + self.cathegorical + self.others + feature_frame.protected
        )
        filtered_table = feature_frame.table.select(
            all_columns,
        )
        return FeatureFrame(
            table=filtered_table,
            features=self.features,
            cathegorical=self.cathegorical,
            others=self.others,
        )


def columns_filter_component(
    key: str,
    feature_frame: FeatureFrame,
) -> FeatureFrame:
    """
    Filter the feature table to only include the specified columns.
    """
    features = feature_frame.features
    selected_features = multiselect_component(
        key=f"{key}:features_filter",
        label="Select features to include in the feature table",
        options=features,
    )

    cathegorical = set(feature_frame.cathegorical) - set(feature_frame.protected)
    selected_categorical = multiselect_component(
        key=f"{key}:categorical_filter",
        label="Select categorical features to include in the feature table",
        options=list(cathegorical),
    )

    others = set(feature_frame.others) - set(feature_frame.protected)
    selected_others = multiselect_component(
        key=f"{key}:others_filter",
        label="Select other features to include in the feature table",
        options=list(others),
    )
    selected_others = list(set(selected_others) - set(selected_categorical))

    all_columns = set(
        selected_features
        + selected_categorical
        + selected_others
        + feature_frame.protected
    )
    filtered_table = feature_frame.table.select(all_columns)

    feature_frame = FeatureFrame(
        table=filtered_table,
        features=selected_features,
        cathegorical=selected_categorical,
        others=selected_others,
    )

    st.session_state[f"{key}:type"] = "columns"
    st.session_state[f"{key}:state"] = ColumnsFilter(
        features=selected_features,
        cathegorical=selected_categorical,
        others=selected_others,
    ).model_dump_json()
    return feature_frame
