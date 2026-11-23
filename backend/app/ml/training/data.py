"""
AutoQ - Training Data Loader
Responsible for loading train and test partitions from processed storage,
separating features from targets, and isolating secondary multi-class defect categories.
"""
import os
from typing import List, Tuple
import pandas as pd


class TrainingDataLoader:
    """Loads processed training and testing partitions for model development."""

    DEFAULT_PROCESSED_DIR = os.path.join("backend", "datasets", "processed")

    FEATURE_COLUMNS = [
        "air_temperature",
        "process_temperature",
        "rotational_speed",
        "torque",
        "tool_wear",
        "temp_difference",
        "mechanical_power",
        "overstrain_index",
        "component_type",
    ]

    NUMERICAL_FEATURES = [
        "air_temperature",
        "process_temperature",
        "rotational_speed",
        "torque",
        "tool_wear",
        "temp_difference",
        "mechanical_power",
        "overstrain_index",
    ]

    CATEGORICAL_FEATURES = ["component_type"]

    def __init__(self, processed_dir: str = DEFAULT_PROCESSED_DIR):
        self.processed_dir = processed_dir
        self.train_path = os.path.join(processed_dir, "train.csv")
        self.test_path = os.path.join(processed_dir, "test.csv")

    def load_data(
        self,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        Loads training and testing data.
        Returns:
            X_train: pd.DataFrame (feature columns)
            X_test:  pd.DataFrame (feature columns)
            y_train: pd.Series (binary target: 0 = Passed, 1 = Defective)
            y_test:  pd.Series (binary target: 0 = Passed, 1 = Defective)
            y_train_multi: pd.Series (multiclass defect category)
            y_test_multi:  pd.Series (multiclass defect category)
        """
        if not os.path.exists(self.train_path) or not os.path.exists(self.test_path):
            raise FileNotFoundError(
                f"Train or test CSV missing from {self.processed_dir}. "
                "Ensure Phase 5 preprocessing has been executed."
            )

        train_df = pd.read_csv(self.train_path)
        test_df = pd.read_csv(self.test_path)

        X_train = train_df[self.FEATURE_COLUMNS].copy()
        y_train = train_df["target"].copy()
        y_train_multi = train_df["defect_category"].copy()

        X_test = test_df[self.FEATURE_COLUMNS].copy()
        y_test = test_df["target"].copy()
        y_test_multi = test_df["defect_category"].copy()

        return X_train, X_test, y_train, y_test, y_train_multi, y_test_multi

