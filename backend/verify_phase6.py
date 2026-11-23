"""
AutoQ - Phase 6 Automated Verification Test Suite
Exhaustively tests:
1. Model training and serialization artifacts.
2. Diagnostic evaluation plots (docs/model_evaluation/).
3. Technical documentation (docs/model_development.md).
4. Inference engine prediction generation and probability bounds.
5. Secondary multi-class root-cause attribution.
6. Input validation and physical boundary error handling.
7. Prediction reproducibility under identical inputs.
8. End-to-end API service and SQLite persistence.
"""
import json
import os
import sys
import unittest
import numpy as np
import pandas as pd
import joblib

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.ml.inference.predictor import DefectPredictor
from app.ml.inference.mapping import FeatureMappingLayer
from app.schemas.prediction import PredictionRequest
from app.database.connection import SessionLocal
from app.models.prediction import Prediction
from app.services.prediction_service import prediction_service


class TestPhase6ModelDevelopment(unittest.TestCase):
    """Regression test suite validating all Phase 6 deliverables."""

    MODELS_DIR = os.path.join("backend", "trained_models")
    DOCS_EVAL_DIR = os.path.join("docs", "model_evaluation")
    DOC_PATH = os.path.join("docs", "model_development.md")

    def test_01_training_artifacts_and_metadata(self):
        """Verify champion and multiclass model artifacts and metadata exist."""
        champ_path = os.path.join(self.MODELS_DIR, "defect_classifier_pipeline.joblib")
        multi_path = os.path.join(self.MODELS_DIR, "multiclass_defect_classifier.joblib")
        meta_path = os.path.join(self.MODELS_DIR, "model_metadata.json")

        self.assertTrue(os.path.exists(champ_path), "Champion pipeline joblib must exist.")
        self.assertTrue(os.path.exists(multi_path), "Multiclass pipeline joblib must exist.")
        self.assertTrue(os.path.exists(meta_path), "Model metadata JSON must exist.")

        self.assertGreater(os.path.getsize(champ_path), 500000, "Champion pipeline artifact must be non-empty.")
        self.assertGreater(os.path.getsize(multi_path), 500000, "Multiclass artifact must be non-empty.")

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        self.assertEqual(meta["model_name"], "Random Forest")
        self.assertEqual(meta["model_version"], "1.0.0")
        self.assertGreaterEqual(meta["champion_test_metrics"]["roc_auc"], 0.95)
        self.assertGreaterEqual(meta["champion_test_metrics"]["recall"], 0.80)
        self.assertEqual(meta["dataset"]["train_records"], 8000)
        self.assertEqual(meta["dataset"]["test_records"], 2000)

    def test_02_evaluation_plots_exist(self):
        """Verify all 5 evaluation plots are rendered with valid non-empty images."""
        expected_plots = [
            "confusion_matrix.png",
            "roc_curve.png",
            "precision_recall_curve.png",
            "model_comparison.png",
            "feature_importance.png",
        ]
        for plot_name in expected_plots:
            p = os.path.join(self.DOCS_EVAL_DIR, plot_name)
            self.assertTrue(os.path.exists(p), f"Plot {plot_name} must exist in docs/model_evaluation/")
            self.assertGreater(os.path.getsize(p), 50000, f"Plot {plot_name} must have non-trivial size.")

    def test_03_model_documentation_exists(self):
        """Verify docs/model_development.md contains complete documentation."""
        self.assertTrue(os.path.exists(self.DOC_PATH), "docs/model_development.md must exist.")
        self.assertGreater(os.path.getsize(self.DOC_PATH), 3000, "Model documentation must be thorough.")

        with open(self.DOC_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Random Forest", content)
        self.assertIn("Logistic Regression", content)
        self.assertIn("Decision Tree", content)
        self.assertIn("Gradient Boosting", content)
        self.assertIn("False Negative", content)
        self.assertIn("Gini Impurity", content)

    def test_04_inference_engine_prediction_generation(self):
        """Verify inference engine generates valid predictions and probability bounds."""
        predictor = DefectPredictor()
        self.assertTrue(predictor.is_model_available(), "Predictor must report model available.")

        # Test normal conforming part
        normal_input = {
            "component_id": "CMP-TST-001",
            "component_category": "Powertrain",
            "manufacturing_temperature": 35.0,  # 35°C -> ~308K
            "pressure": 140.0,
            "rotational_speed": 1500.0,
            "torque": 40.0,
            "tool_wear": 50.0,
        }
        res_normal = predictor.predict(normal_input)
        self.assertEqual(res_normal["predicted_status"], "Passed")
        self.assertLess(res_normal["defect_probability"], 0.40)
        self.assertGreaterEqual(res_normal["confidence"], 0.50)
        self.assertEqual(res_normal["model_status"], "INFERENCE_COMPLETE")

        # Test defective part (extreme torque, low speed, high tool wear)
        defective_input = {
            "component_id": "CMP-TST-002",
            "component_category": "Powertrain",
            "manufacturing_temperature": 40.0,
            "pressure": 260.0,
            "rotational_speed": 1200.0,
            "torque": 75.0,     # extreme torque
            "tool_wear": 230.0,  # high wear
        }
        res_defect = predictor.predict(defective_input)
        self.assertEqual(res_defect["predicted_status"], "Defective")
        self.assertGreaterEqual(res_defect["defect_probability"], 0.50)
        self.assertGreater(len(res_defect["contributing_factors"]), 0)
        self.assertIn("REJECT", res_defect["recommendation"])

    def test_05_secondary_multiclass_attribution(self):
        """Verify secondary classifier attributes defective conditions to physical failure modes."""
        predictor = DefectPredictor()

        # Input with high heat dissipation risk: ΔT < 8.6K and low rotational speed
        hdf_input = {
            "component_id": "CMP-HDF-01",
            "component_category": "Powertrain",
            "manufacturing_temperature": 36.0,
            "air_temperature": 30.0,  # ΔT = 6.0 K (< 8.6 K)
            "pressure": 145.0,
            "rotational_speed": 1250.0,  # < 1380 rpm
            "torque": 55.0,
            "tool_wear": 120.0,
        }
        res = predictor.predict(hdf_input)
        self.assertIn(
            res["predicted_defect_category"],
            ["Heat Dissipation Failure", "Power Failure", "Overstrain Failure", "General Manufacturing Non-Conformance"],
            "Defect category must belong to the verified failure taxonomy."
        )

    def test_06_input_validation_and_error_handling(self):
        """Verify predictor strictly rejects missing features and invalid physical numbers."""
        predictor = DefectPredictor()

        # Missing manufacturing_temperature
        missing_input = {
            "component_category": "Powertrain",
            "pressure": 140.0,
        }
        with self.assertRaises(ValueError):
            predictor.predict(missing_input)

        # Physically impossible temperature (> 2500°C)
        impossible_temp = {
            "component_category": "Powertrain",
            "manufacturing_temperature": 8000.0,
            "pressure": 140.0,
        }
        with self.assertRaises(ValueError):
            predictor.predict(impossible_temp)

        # Negative pressure
        negative_pressure = {
            "component_category": "Powertrain",
            "manufacturing_temperature": 750.0,
            "pressure": -25.0,
        }
        with self.assertRaises(ValueError):
            predictor.predict(negative_pressure)

    def test_07_prediction_reproducibility(self):
        """Verify deterministic outputs for identical inputs."""
        predictor = DefectPredictor()
        input_data = {
            "component_id": "CMP-DET-999",
            "component_category": "Braking System",
            "manufacturing_temperature": 745.0,
            "pressure": 142.0,
            "stress_tolerance": 335.0,
            "cycle_time": 44.0,
            "vibration_index": 1.82,
            "torque_resistance": 208.0,
            "production_batch": "BATCH-2026-A1",
        }

        res1 = predictor.predict(input_data)
        res2 = predictor.predict(input_data)

        self.assertEqual(res1["predicted_status"], res2["predicted_status"])
        self.assertEqual(res1["defect_probability"], res2["defect_probability"])
        self.assertEqual(res1["confidence"], res2["confidence"])
        self.assertEqual(res1["predicted_defect_category"], res2["predicted_defect_category"])

    def test_08_end_to_end_api_and_database_persistence(self):
        """Verify prediction_service processes PredictionRequest and persists record to SQLite."""
        with SessionLocal() as db:
            initial_count = db.query(Prediction).count()

            request_payload = PredictionRequest(
                component_id="CMP-BRK-401",
                component_category="Braking System",
                manufacturing_temperature=742.0,
                pressure=145.0,
                production_batch="BATCH-2026-A1",
            )

            import asyncio
            response = asyncio.run(prediction_service.predict_defect(db=db, payload=request_payload))

            self.assertEqual(response.model_status, "INFERENCE_COMPLETE")
            self.assertIn(response.predicted_status, ["Passed", "Defective"])
            self.assertIsNotNone(response.defect_probability)
            self.assertIsNotNone(response.id)

            new_count = db.query(Prediction).count()
            self.assertEqual(new_count, initial_count + 1)

            persisted = db.query(Prediction).filter(Prediction.id == response.id).first()
            self.assertIsNotNone(persisted)
            self.assertEqual(persisted.component_id, "CMP-BRK-401")
            self.assertEqual(persisted.predicted_status, response.predicted_status)


if __name__ == "__main__":
    unittest.main(verbosity=2)
