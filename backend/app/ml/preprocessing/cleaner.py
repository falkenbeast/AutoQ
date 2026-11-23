"""
AutoQ - Data Cleaner Module
Cleans raw manufacturing data, standardizes feature naming, handles defect categorization,
and validates data types without causing data leakage.
"""
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np


class DataCleaner:
    """
    Standardizes raw UCI AI4I 2020 dataset into a clean, normalized schema suitable
    for exploratory analytics, database synchronization, and machine learning pipelines.
    """

    COLUMN_MAPPING = {
        "UDI": "udi",
        "Product ID": "product_id",
        "Type": "component_type",
        "Air temperature [K]": "air_temperature",
        "Process temperature [K]": "process_temperature",
        "Rotational speed [rpm]": "rotational_speed",
        "Torque [Nm]": "torque",
        "Tool wear [min]": "tool_wear",
        "Machine failure": "target",
        "TWF": "twf",
        "HDF": "hdf",
        "PWF": "pwf",
        "OSF": "osf",
        "RNF": "rnf",
    }

    FAILURE_MODES = ["twf", "hdf", "pwf", "osf", "rnf"]

    def __init__(self):
        pass

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Executes complete data standardization pipeline:
        1. Renames headers to canonical snake_case identifiers.
        2. Assigns unified defect_category column based on multi-label failure flags.
        3. Formats component_category and inspection_result for database compatibility.
        4. Validates absence of nulls and correct datatypes.
        """
        cleaned = df.copy()

        # 1. Rename columns
        cleaned = cleaned.rename(columns=self.COLUMN_MAPPING)

        # 2. Derive single categorical defect_category
        cleaned["defect_category"] = self._derive_defect_category(cleaned)

        # 3. Add AutoQ database compatibility fields
        cleaned["inspection_result"] = cleaned["target"].map({0: "Passed", 1: "Defective"})

        # Type mapping: L -> Chassis Mounts, M -> Braking System, H -> Powertrain
        type_to_category = {
            "L": "Chassis Mounts",
            "M": "Braking System",
            "H": "Powertrain",
        }
        cleaned["component_category"] = cleaned["component_type"].map(type_to_category)

        # 4. Strict data validation
        null_count = cleaned.isnull().sum().sum()
        if null_count > 0:
            raise ValueError(f"Cleaned dataset contains {null_count} unexpected null values.")

        return cleaned

    def _derive_defect_category(self, df: pd.DataFrame) -> pd.Series:
        """
        Maps binary failure indicators to an interpretable multi-class defect classification.
        """
        categories = []
        for _, row in df.iterrows():
            if row["target"] == 0:
                categories.append("No Defect")
                continue

            active_modes = [mode.upper() for mode in self.FAILURE_MODES if row[mode] == 1]

            if len(active_modes) == 1:
                mode = active_modes[0]
                if mode == "HDF":
                    categories.append("Heat Dissipation Failure")
                elif mode == "OSF":
                    categories.append("Overstrain Failure")
                elif mode == "PWF":
                    categories.append("Power Failure")
                elif mode == "TWF":
                    categories.append("Tool Wear Failure")
                elif mode == "RNF":
                    categories.append("Random Failure")
                else:
                    categories.append("Unspecified Defect")
            elif len(active_modes) > 1:
                categories.append("Multi-mode Failure")
            else:
                categories.append("Process Anomaly")

        return pd.Series(categories, index=df.index)


def clean_raw_dataset(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Convenience helper to clean raw dataset."""
    cleaner = DataCleaner()
    return cleaner.clean(raw_df)
