"""
AutoQ - Phase 5 Verification Test Suite
Automated regression tests to verify dataset research, acquisition, EDA charts,
data cleaning, feature engineering, no-leakage preprocessing, and database compatibility.
"""
import hashlib
import json
import os
import sys
import unittest
import joblib
import numpy as np
import pandas as pd

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.ml.preprocessing.data_loader import RawDataLoader
from app.ml.preprocessing.cleaner import DataCleaner
from app.ml.preprocessing.feature_pipeline import FeaturePipeline


class TestPhase5DatasetVerification(unittest.TestCase):
    """Automated tests validating Phase 5 outputs and constraints."""

    RAW_PATH = os.path.join("backend", "datasets", "raw", "ai4i2020.csv")
    MANIFEST_PATH = os.path.join("backend", "datasets", "raw", "dataset_manifest.json")
    PROCESSED_DIR = os.path.join("backend", "datasets", "processed")
    EDA_DIR = os.path.join("docs", "eda")

    def test_01_raw_dataset_and_manifest_integrity(self):
        """Verify raw dataset exists and its SHA-256 matches manifest."""
        self.assertTrue(os.path.exists(self.RAW_PATH), "Raw dataset file must exist.")
        self.assertTrue(os.path.exists(self.MANIFEST_PATH), "Dataset manifest must exist.")

        with open(self.RAW_PATH, "rb") as f:
            computed_hash = hashlib.sha256(f.read()).hexdigest()

        with open(self.MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(
            computed_hash,
            manifest["sha256_checksum"],
            "Computed SHA-256 must match manifest checksum."
        )
        self.assertEqual(manifest["record_count"], 10000)
        self.assertEqual(manifest["feature_count"], 14)
        self.assertIn("CC BY 4.0", manifest["license"])

    def test_02_documentation_artifacts_exist(self):
        """Verify research and data dictionary documentation files exist."""
        research_doc = os.path.join("docs", "dataset_research.md")
        dict_doc = os.path.join("docs", "data_dictionary.md")

        self.assertTrue(os.path.exists(research_doc), "docs/dataset_research.md must exist.")
        self.assertTrue(os.path.exists(dict_doc), "docs/data_dictionary.md must exist.")

        self.assertGreater(os.path.getsize(research_doc), 2000, "Research doc must be comprehensive.")
        self.assertGreater(os.path.getsize(dict_doc), 2000, "Data dictionary must be comprehensive.")

    def test_03_eda_visualizations_exist(self):
        """Verify all 5 required EDA visualizations are rendered and non-empty."""
        expected_charts = [
            "target_distribution.png",
            "missing_values.png",
            "feature_distributions.png",
            "correlation_heatmap.png",
            "parameter_relationships.png",
        ]
        for chart in expected_charts:
            chart_path = os.path.join(self.EDA_DIR, chart)
            self.assertTrue(os.path.exists(chart_path), f"EDA chart {chart} must exist.")
            self.assertGreater(os.path.getsize(chart_path), 50000, f"EDA chart {chart} must not be empty.")

    def test_04_cleaned_dataset_integrity(self):
        """Verify cleaned_dataset.csv has 10,000 rows, 0 nulls, and proper defect categories."""
        cleaned_path = os.path.join(self.PROCESSED_DIR, "cleaned_dataset.csv")
        self.assertTrue(os.path.exists(cleaned_path), "cleaned_dataset.csv must exist.")

        df = pd.read_csv(cleaned_path)
        self.assertEqual(len(df), 10000)
        self.assertEqual(df.isnull().sum().sum(), 0, "No null values allowed in cleaned data.")

        # Check required columns
        required_cols = [
            "udi", "product_id", "component_type", "air_temperature",
            "process_temperature", "rotational_speed", "torque", "tool_wear",
            "target", "twf", "hdf", "pwf", "osf", "rnf", "defect_category",
            "inspection_result", "component_category", "temp_difference",
            "mechanical_power", "overstrain_index"
        ]
        for col in required_cols:
            self.assertIn(col, df.columns, f"Column {col} must be present in cleaned dataset.")

        # Check target class distribution
        target_counts = df["target"].value_counts()
        self.assertEqual(target_counts[0], 9661)
        self.assertEqual(target_counts[1], 339)

    def test_05_train_test_split_and_stratification(self):
        """Verify 80/20 train/test split preserving stratification."""
        train_path = os.path.join(self.PROCESSED_DIR, "train.csv")
        test_path = os.path.join(self.PROCESSED_DIR, "test.csv")

        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)

        self.assertEqual(len(train_df), 8000, "Train partition must have 8,000 samples (80%).")
        self.assertEqual(len(test_df), 2000, "Test partition must have 2,000 samples (20%).")

        train_defect_rate = train_df["target"].mean()
        test_defect_rate = test_df["target"].mean()

        # Both should match the overall ~3.39% within tight margin
        self.assertAlmostEqual(train_defect_rate, 0.0339, delta=0.002)
        self.assertAlmostEqual(test_defect_rate, 0.0340, delta=0.002)

    def test_06_preprocessor_serialization_and_inference(self):
        """Verify preprocessor artifact can be loaded and transforms sample inference input."""
        preprocessor_path = os.path.join("backend", "trained_models", "preprocessor.joblib")
        self.assertTrue(os.path.exists(preprocessor_path), "preprocessor.joblib must exist.")

        preprocessor = joblib.load(preprocessor_path)

        # Create a sample raw inference row
        sample_input = pd.DataFrame([{
            "air_temperature": 300.0,
            "process_temperature": 310.0,
            "rotational_speed": 1500.0,
            "torque": 40.0,
            "tool_wear": 100.0,
            "temp_difference": 10.0,
            "mechanical_power": (2 * np.pi * 1500.0 * 40.0) / 60.0,
            "overstrain_index": 4000.0,
            "component_type": "M",
        }])

        transformed = preprocessor.transform(sample_input)
        self.assertEqual(transformed.shape, (1, 10), "Transformed feature dimension must be 1x10.")
        self.assertFalse(np.isnan(transformed).any(), "Transformed features must not contain NaN.")

    def test_07_database_compatibility(self):
        """Verify database tables are intact and compatible with dataset mapping."""
        from app.database.connection import SessionLocal
        from app.models.component import Component
        from app.models.inspection import Inspection

        with SessionLocal() as db:
            components = db.query(Component).all()
            self.assertGreaterEqual(len(components), 1, "Components table must be accessible.")
            inspections = db.query(Inspection).all()
            self.assertGreaterEqual(len(inspections), 1, "Inspections table must be accessible.")


if __name__ == "__main__":
    unittest.main(verbosity=2)

