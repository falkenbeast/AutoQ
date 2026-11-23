"""
AutoQ - Feature Engineering & Preprocessing Pipeline
Implements domain-informed feature engineering, Scikit-learn ColumnTransformer,
stratified train/test splitting, and zero data leakage guarantees.
"""
import json
import os
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, RobustScaler, StandardScaler


class DomainFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Computes domain-informed physical automotive manufacturing features:
    1. temp_difference = process_temperature - air_temperature
    2. mechanical_power = (2 * pi * rotational_speed * torque) / 60
    3. overstrain_index = tool_wear * torque
    """

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X_out = X.copy()
        # Temperature gradient
        X_out["temp_difference"] = (
            X_out["process_temperature"] - X_out["air_temperature"]
        )
        # Instantaneous spindle power in Watts
        X_out["mechanical_power"] = (
            2 * np.pi * X_out["rotational_speed"] * X_out["torque"]
        ) / 60.0
        # Coupled fatigue stress index
        X_out["overstrain_index"] = X_out["tool_wear"] * X_out["torque"]
        return X_out


class FeaturePipeline:
    """
    Modular preprocessing pipeline ensuring zero data leakage.
    Fits all scaling and encoding parameters strictly on the training partition.
    """

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

    def __init__(
        self,
        scaler_type: str = "robust",
        test_size: float = 0.20,
        random_state: int = 42,
    ):
        self.scaler_type = scaler_type
        self.test_size = test_size
        self.random_state = random_state

        self.feature_engineer = DomainFeatureEngineer()
        self.preprocessor: Optional[ColumnTransformer] = None
        self.fitted_feature_names: List[str] = []

    def _build_column_transformer(self) -> ColumnTransformer:
        """Constructs Scikit-learn ColumnTransformer."""
        scaler = (
            RobustScaler()
            if self.scaler_type == "robust"
            else StandardScaler()
        )

        encoder = OneHotEncoder(
            drop="first",
            sparse_output=False,
            handle_unknown="ignore",
        )

        return ColumnTransformer(
            transformers=[
                ("num", scaler, self.NUMERICAL_FEATURES),
                ("cat", encoder, self.CATEGORICAL_FEATURES),
            ],
            remainder="drop",
        )

    def prepare_and_split(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Applies domain feature engineering, separates features from target,
        and generates a stratified train/test split.
        Zero data leakage is preserved as transformer fitting is deferred.
        """
        # Step 1: Feature Engineering
        df_engineered = self.feature_engineer.transform(df)

        feature_cols = self.NUMERICAL_FEATURES + self.CATEGORICAL_FEATURES
        X = df_engineered[feature_cols].copy()
        y = df_engineered["target"].copy()

        # Step 2: Stratified Split
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=y,
        )

        return X_train, X_test, y_train, y_test

    def fit_transform_train(self, X_train: pd.DataFrame) -> np.ndarray:
        """
        Fits the ColumnTransformer strictly on X_train and returns transformed array.
        """
        self.preprocessor = self._build_column_transformer()
        X_train_transformed = self.preprocessor.fit_transform(X_train)

        # Cache transformed feature names
        cat_encoder = self.preprocessor.named_transformers_["cat"]
        cat_cols = cat_encoder.get_feature_names_out(self.CATEGORICAL_FEATURES).tolist()
        self.fitted_feature_names = self.NUMERICAL_FEATURES + cat_cols

        return X_train_transformed

    def transform_test(self, X_test: pd.DataFrame) -> np.ndarray:
        """
        Transforms test partition using parameters learned strictly from training partition.
        """
        if self.preprocessor is None:
            raise RuntimeError("Preprocessor must be fitted on training data before transforming test data.")
        return self.preprocessor.transform(X_test)

    def get_feature_names(self) -> List[str]:
        return self.fitted_feature_names


def execute_preprocessing_pipeline(
    cleaned_df: pd.DataFrame,
    output_dir: str = os.path.join("backend", "datasets", "processed"),
    models_dir: str = os.path.join("backend", "trained_models"),
) -> Dict[str, Any]:
    """
    End-to-end execution of Phase 5 preprocessing:
    1. Engineers domain features.
    2. Stratified 80/20 train/test split.
    3. Fits ColumnTransformer on train partition only.
    4. Transforms train and test partitions.
    5. Saves cleaned_dataset.csv, train.csv, test.csv, preprocessor.joblib, and preprocessing_metadata.json.
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)

    pipeline = FeaturePipeline(scaler_type="robust", test_size=0.20, random_state=42)

    # 1. Feature Engineering on full cleaned dataset for saving full clean copy
    full_engineered = pipeline.feature_engineer.transform(cleaned_df)
    cleaned_csv_path = os.path.join(output_dir, "cleaned_dataset.csv")
    full_engineered.to_csv(cleaned_csv_path, index=False)

    # 2. Stratified train/test split of full dataframe (including metadata for auditability)
    train_df, test_df = train_test_split(
        full_engineered,
        test_size=0.20,
        random_state=42,
        stratify=full_engineered["target"],
    )

    train_csv_path = os.path.join(output_dir, "train.csv")
    test_csv_path = os.path.join(output_dir, "test.csv")
    train_df.to_csv(train_csv_path, index=False)
    test_df.to_csv(test_csv_path, index=False)

    # 3. Fit transformer on train features only
    feature_cols = pipeline.NUMERICAL_FEATURES + pipeline.CATEGORICAL_FEATURES
    X_train = train_df[feature_cols].copy()
    X_test = test_df[feature_cols].copy()

    X_train_trans = pipeline.fit_transform_train(X_train)
    X_test_trans = pipeline.transform_test(X_test)

    # 4. Serialize fitted preprocessor
    preprocessor_path = os.path.join(models_dir, "preprocessor.joblib")
    joblib.dump(pipeline.preprocessor, preprocessor_path)

    # Also keep a copy in processed dir for direct dataset reference
    joblib.dump(pipeline.preprocessor, os.path.join(output_dir, "preprocessor.joblib"))

    # 5. Extract metadata
    train_target_counts = train_df["target"].value_counts().to_dict()
    test_target_counts = test_df["target"].value_counts().to_dict()

    metadata = {
        "dataset_name": "AI4I 2020 Manufacturing Quality Benchmark",
        "train_samples": int(len(train_df)),
        "test_samples": int(len(test_df)),
        "split_ratio": "80/20 Stratified",
        "random_state": 42,
        "input_features": feature_cols,
        "numerical_features": pipeline.NUMERICAL_FEATURES,
        "categorical_features": pipeline.CATEGORICAL_FEATURES,
        "transformed_feature_names": pipeline.get_feature_names(),
        "transformed_feature_count": len(pipeline.get_feature_names()),
        "scaler": "RobustScaler (IQR-based centering and scaling)",
        "encoder": "OneHotEncoder(drop='first')",
        "target_column": "target",
        "train_class_distribution": {
            "passed_0": int(train_target_counts.get(0, 0)),
            "defective_1": int(train_target_counts.get(1, 0)),
            "defect_rate_pct": round(float(train_target_counts.get(1, 0) / len(train_df) * 100), 2),
        },
        "test_class_distribution": {
            "passed_0": int(test_target_counts.get(0, 0)),
            "defective_1": int(test_target_counts.get(1, 0)),
            "defect_rate_pct": round(float(test_target_counts.get(1, 0) / len(test_df) * 100), 2),
        },
        "zero_data_leakage_guarantee": "Transformers fitted strictly on X_train. X_test transformed using train-fitted parameters.",
        "preprocessor_artifact": preprocessor_path,
    }

    metadata_path = os.path.join(output_dir, "preprocessing_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)

    return metadata

