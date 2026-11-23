"""
AutoQ - Secondary Multiclass Defect Category Trainer
Trains an explainable root-cause attribution classifier to categorize defects
into the 5 verified physical failure modes (Heat Dissipation, Power Failure,
Overstrain, Tool Wear, Stochastic Process Anomaly).
"""
import json
import os
from typing import Any, Dict, Tuple
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import Pipeline


class MulticlassDefectTrainer:
    """Trains secondary multi-class root-cause classifier on verified failure taxonomy."""

    MODELS_DIR = os.path.join("backend", "trained_models")
    PREPROCESSOR_PATH = os.path.join("backend", "trained_models", "preprocessor.joblib")

    def __init__(self, random_state: int = 42, models_dir: str = MODELS_DIR):
        self.random_state = random_state
        self.models_dir = models_dir
        self.preprocessor = joblib.load(self.PREPROCESSOR_PATH)

    def train_and_serialize(
        self,
        X_train: pd.DataFrame,
        y_train_multi: pd.Series,
        X_test: pd.DataFrame,
        y_test_multi: pd.Series,
    ) -> Tuple[Pipeline, Dict[str, Any]]:
        """Trains multiclass pipeline, computes evaluation metrics, and saves artifact."""
        pipeline = Pipeline([
            ("preprocessor", self.preprocessor),
            ("classifier", RandomForestClassifier(
                n_estimators=120,
                max_depth=10,
                class_weight="balanced",
                random_state=self.random_state,
                n_jobs=-1,
            )),
        ])

        pipeline.fit(X_train, y_train_multi)

        y_pred = pipeline.predict(X_test)
        acc = float(accuracy_score(y_test_multi, y_pred))
        report = classification_report(y_test_multi, y_pred, output_dict=True, zero_division=0)

        # Serialize model
        artifact_path = os.path.join(self.models_dir, "multiclass_defect_classifier.joblib")
        joblib.dump(pipeline, artifact_path)

        metadata = {
            "model_name": "Multiclass Root-Cause Defect Classifier",
            "model_version": "1.0.0",
            "artifact_file": "multiclass_defect_classifier.joblib",
            "accuracy": round(acc, 4),
            "classes": sorted(list(y_train_multi.unique())),
            "per_class_f1": {k: round(v["f1-score"], 3) for k, v in report.items() if isinstance(v, dict)},
        }

        meta_path = os.path.join(self.models_dir, "multiclass_metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)

        return pipeline, metadata

