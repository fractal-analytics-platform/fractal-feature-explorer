from dataclasses import dataclass, field

import polars as pl


@dataclass
class FeatureFrame:
    table: pl.LazyFrame
    features: list[str] = field(default_factory=list)
    cathegorical: list[str] = field(default_factory=list)
    others: list[str] = field(default_factory=list)

    @property
    def protected(self) -> list[str]:
        return ["image_url", "reference_label", "label"]

    def all_columns(self) -> list[str]:
        """
        Get all columns in the feature table.
        """
        return self.features + self.cathegorical + self.others
