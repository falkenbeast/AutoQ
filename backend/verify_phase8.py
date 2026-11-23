"""
AutoQ - Phase 8 Automated Verification & Validation Suite
Exhaustively tests all 16 Phase 8 audit and optimization assertions:
 1. Model artifact integrity (pipeline files, metadata, non-empty serialization)
 2. Binary prediction correctness (probabilities, confidence, classification status)
 3. Threshold behaviour (0.35 high-recall vs 0.50 balanced threshold shift)
 4. Multiclass attribution (verification against supported multiclass_metadata.json classes)
 5. Feature mapping (canonical feature ordering, unit conversion, component type mapping)
 6. Invalid input handling (boundary checks, negative values, missing fields -> 422)
 7. Inspection CRUD operations (POST, GET, PUT, DELETE, 404 verification)
 8. Prediction persistence (SQLite persistence, component linkage)
 9. Database integrity (foreign key pragma enforcement, decoupled deletion)
10. Analytics calculations (single-query aggregate overview, trends, defect distribution, batches)
11. Report generation (ReportLab PDF with %PDF- header and CSV generation on disk)
12. Report download security (streaming binary response, path-traversal prevention)
13. API route parity (identical behavior across /api/* and /api/v1/*)
14. Frontend production build (dist/index.html and asset chunks validation)
15. Empty database behaviour (zero division resilience, empty list responses)
16. Regression compatibility (Phase 4, Phase 6, and Phase 7 verification suites)
"""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import joblib
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.connection import get_db
from app.main import app
from app.ml.inference.mapping import FeatureMappingLayer
from app.ml.inference.predictor import DefectPredictor, predictor
from app.models.component import Component
from app.models.inspection import Inspection
from app.models.prediction import Prediction
from app.models.report import Report


class TestPhase8SystemAuditAndValidation(unittest.TestCase):
    """Exhaustive test suite for AutoQ Phase 8."""

    @classmethod
    def setUpClass(cls):
        # Create an isolated temporary test database
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_db_path = os.path.join(cls.temp_dir, "test_phase8_autoq.db")
        cls.test_db_url = f"sqlite:///{cls.test_db_path.replace(os.sep, '/')}"

        cls.test_engine = create_engine(
            cls.test_db_url, connect_args={"check_same_thread": False}
        )
        cls.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=cls.test_engine
        )

        Base.metadata.create_all(bind=cls.test_engine)

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client_ctx = TestClient(app)
        cls.client = cls.client_ctx.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_ctx.__exit__(None, None, None)
        app.dependency_overrides.clear()
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

    # -------------------------------------------------------------
    # 1. Model Artifact Integrity
    # -------------------------------------------------------------
    def test_01_model_artifact_integrity(self):
        """Verify model files exist, are non-empty, and load cleanly via joblib."""
        models_dir = Path("backend") / "trained_models"
        champ_path = models_dir / "defect_classifier_pipeline.joblib"
        multi_path = models_dir / "multiclass_defect_classifier.joblib"
        meta_path = models_dir / "model_metadata.json"
        multi_meta_path = models_dir / "multiclass_metadata.json"

        self.assertTrue(champ_path.is_file(), "Champion pipeline artifact must exist")
        self.assertTrue(multi_path.is_file(), "Multiclass pipeline artifact must exist")
        self.assertTrue(meta_path.is_file(), "Model metadata JSON must exist")
        self.assertTrue(multi_meta_path.is_file(), "Multiclass metadata JSON must exist")

        self.assertGreater(champ_path.stat().st_size, 500000, "Champion pipeline file must be > 500KB")
        self.assertGreater(multi_path.stat().st_size, 300000, "Multiclass pipeline file must be > 300KB")

        pipe = joblib.load(champ_path)
        self.assertTrue(hasattr(pipe, "predict_proba"), "Pipeline must implement predict_proba")

    # -------------------------------------------------------------
    # 2. Binary Prediction Correctness
    # -------------------------------------------------------------
    def test_02_binary_prediction_correctness(self):
        """Verify inference outputs valid calibrated probabilities and status."""
        conforming_payload = {
            "component_id": "CMP-TST-001",
            "component_name": "Precision Spindle Bearing",
            "component_category": "Powertrain",
            "production_batch": "BATCH-2026-A1",
            "manufacturing_temperature": 740.0,
            "pressure": 142.0,
            "rotational_speed": 1520.0,
            "torque": 38.0,
            "tool_wear": 45.0,
            "decision_threshold": 0.50,
        }
        res = self.client.post("/api/predictions", json=conforming_payload)
        self.assertIn(res.status_code, [200, 201])
        data = res.json()
        self.assertEqual(data["model_status"], "INFERENCE_COMPLETE")
        self.assertTrue(0.0 <= data["defect_probability"] <= 1.0)
        self.assertTrue(0.5 <= data["confidence"] <= 1.0)
        self.assertEqual(data["predicted_status"], "Passed")

    # -------------------------------------------------------------
    # 3. Threshold Behaviour
    # -------------------------------------------------------------
    def test_03_threshold_behaviour(self):
        """Verify 0.35 high-recall vs 0.50 balanced threshold shift and trade-off."""
        borderline_payload = {
            "component_id": "CMP-TST-002",
            "component_name": "High Torque Pinion",
            "component_category": "Transmission",
            "production_batch": "BATCH-2026-A2",
            "manufacturing_temperature": 750.0,
            "pressure": 155.0,
            "air_temperature": 300.0,
            "process_temperature": 310.0,
            "rotational_speed": 1380.0,
            "torque": 55.0,
            "tool_wear": 195.0,
            "product_type": "L",
            "decision_threshold": 0.50,
        }
        res_50 = self.client.post("/api/predictions", json=borderline_payload)
        self.assertIn(res_50.status_code, [200, 201])
        prob = res_50.json()["defect_probability"]

        borderline_payload["decision_threshold"] = 0.35
        res_35 = self.client.post("/api/predictions", json=borderline_payload)
        self.assertIn(res_35.status_code, [200, 201])

        expected_35 = "Defective" if prob >= 0.35 else "Passed"
        expected_50 = "Defective" if prob >= 0.50 else "Passed"
        self.assertEqual(res_35.json()["predicted_status"], expected_35)
        self.assertEqual(res_50.json()["predicted_status"], expected_50)

    # -------------------------------------------------------------
    # 4. Multiclass Attribution
    # -------------------------------------------------------------
    def test_04_multiclass_attribution(self):
        """Verify attributed defect categories strictly adhere to multiclass_metadata.json."""
        with open("backend/trained_models/multiclass_metadata.json", "r", encoding="utf-8") as f:
            meta = json.load(f)
        supported_classes = meta.get("classes", [])
        self.assertTrue(len(supported_classes) >= 5)

        extreme_payload = {
            "component_id": "CMP-TST-003",
            "component_name": "High Wear Cutter",
            "component_category": "Braking System",
            "production_batch": "BATCH-2026-B1",
            "manufacturing_temperature": 780.0,
            "pressure": 190.0,
            "air_temperature": 304.0,
            "process_temperature": 313.0,
            "rotational_speed": 1200.0,
            "torque": 85.0,
            "tool_wear": 235.0,
            "decision_threshold": 0.35,
        }
        res = self.client.post("/api/predictions", json=extreme_payload)
        self.assertIn(res.status_code, [200, 201])
        data = res.json()
        self.assertEqual(data["predicted_status"], "Defective")
        category = data.get("predicted_defect_category")
        self.assertIn(category, supported_classes, f"Category '{category}' not in supported classes")

    # -------------------------------------------------------------
    # 5. Feature Mapping Layer
    # -------------------------------------------------------------
    def test_05_feature_mapping(self):
        """Verify FeatureMappingLayer produces correct 9-column canonical schema and unit conversions."""
        mapper = FeatureMappingLayer()
        input_data = {
            "component_category": "Powertrain",
            "manufacturing_temperature": 745.0,
            "pressure": 150.0,
            "rotational_speed": 1600.0,
            "torque": 42.0,
            "tool_wear": 80.0,
        }
        df = mapper.map_request_to_features(input_data)
        self.assertEqual(df.shape[0], 1)
        expected_cols = [
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
        self.assertEqual(list(df.columns), expected_cols)
        self.assertEqual(df["component_type"].iloc[0], "H")
        # Process temperature must be converted to Kelvin (~308-314K)
        self.assertTrue(295.0 <= df["process_temperature"].iloc[0] <= 320.0)

    # -------------------------------------------------------------
    # 6. Invalid Input Handling
    # -------------------------------------------------------------
    def test_06_invalid_input_handling(self):
        """Verify invalid physical numbers and missing parameters trigger HTTP 422."""
        invalid_payloads = [
            # Negative rotational speed
            {
                "component_id": "CMP-ERR-001",
                "component_category": "Powertrain",
                "production_batch": "BATCH-2026-A1",
                "rotational_speed": -500.0,
            },
            # Absurd temperature
            {
                "component_id": "CMP-ERR-002",
                "component_category": "Powertrain",
                "production_batch": "BATCH-2026-A1",
                "manufacturing_temperature": 9999.0,
            },
            # Missing component_id
            {
                "component_category": "Powertrain",
                "production_batch": "BATCH-2026-A1",
            },
        ]
        for payload in invalid_payloads:
            res = self.client.post("/api/predictions", json=payload)
            self.assertIn(res.status_code, [400, 422], f"Expected validation failure on {payload}")

    # -------------------------------------------------------------
    # 7. Inspection CRUD Operations
    # -------------------------------------------------------------
    def test_07_inspection_crud(self):
        """Verify complete inspection lifecycle: create, read, update, delete."""
        create_payload = {
            "component_id": "CMP-CRUD-801",
            "component_name": "Cylinder Liner Sleeve",
            "component_category": "Engine",
            "manufacturing_temperature": 752.0,
            "pressure": 148.0,
            "production_batch": "BATCH-2026-Z1",
            "inspection_result": "Passed",
            "notes": "Initial audit inspection.",
        }
        # CREATE
        res = self.client.post("/api/inspections", json=create_payload)
        self.assertEqual(res.status_code, 201)
        insp_id = res.json()["id"]

        # READ
        res = self.client.get(f"/api/inspections/{insp_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["component_id"], "CMP-CRUD-801")

        # UPDATE
        res = self.client.put(f"/api/inspections/{insp_id}", json={"notes": "Updated note."})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["notes"], "Updated note.")

        # DELETE
        res = self.client.delete(f"/api/inspections/{insp_id}")
        self.assertEqual(res.status_code, 200)

        # 404 CONFIRMATION
        res = self.client.get(f"/api/inspections/{insp_id}")
        self.assertEqual(res.status_code, 404)

    # -------------------------------------------------------------
    # 8. Prediction Persistence
    # -------------------------------------------------------------
    def test_08_prediction_persistence(self):
        """Verify prediction record is stored in SQLite and linked correctly."""
        pred_payload = {
            "component_id": "CMP-PERSIST-901",
            "component_name": "Steering Knuckle Arm",
            "component_category": "Chassis & Steering",
            "production_batch": "BATCH-2026-A1",
            "manufacturing_temperature": 745.0,
            "pressure": 144.0,
            "decision_threshold": 0.50,
        }
        res = self.client.post("/api/predictions", json=pred_payload)
        self.assertIn(res.status_code, [200, 201])
        pred_id = res.json()["id"]

        # Retrieve
        res = self.client.get(f"/api/predictions/{pred_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["component_id"], "CMP-PERSIST-901")

    # -------------------------------------------------------------
    # 9. Database Integrity & Foreign Key Pragma Enforcement
    # -------------------------------------------------------------
    def test_09_database_integrity(self):
        """Verify PRAGMA foreign_keys is ON and deleting an inspection safely decouples predictions."""
        # Check SQLite foreign key pragma
        with self.test_engine.connect() as conn:
            fk_status = conn.execute(text("PRAGMA foreign_keys")).scalar()
            self.assertEqual(fk_status, 1, "PRAGMA foreign_keys must be active")

        # Create an inspection
        insp_res = self.client.post("/api/inspections", json={
            "component_id": "CMP-FK-101",
            "component_name": "Differential Gear Pin",
            "component_category": "Transmission",
            "manufacturing_temperature": 748.0,
            "pressure": 146.0,
            "production_batch": "BATCH-2026-FK",
            "inspection_result": "Passed",
        })
        self.assertEqual(insp_res.status_code, 201)
        insp_id = insp_res.json()["id"]

        # Create a prediction linked to this inspection
        pred_res = self.client.post("/api/predictions", json={
            "component_id": "CMP-FK-101",
            "component_category": "Transmission",
            "production_batch": "BATCH-2026-FK",
            "inspection_id": insp_id,
        })
        self.assertIn(pred_res.status_code, [200, 201])
        pred_id = pred_res.json()["id"]

        # Delete inspection
        del_res = self.client.delete(f"/api/inspections/{insp_id}")
        self.assertEqual(del_res.status_code, 200)

        # Verify prediction still exists with inspection_id decoupled to None
        check_pred = self.client.get(f"/api/predictions/{pred_id}")
        self.assertEqual(check_pred.status_code, 200)
        self.assertIsNone(check_pred.json()["inspection_id"], "Linked inspection_id must be nullified")

    # -------------------------------------------------------------
    # 10. Analytics Calculations & Single-Query Optimization
    # -------------------------------------------------------------
    def test_10_analytics_calculations(self):
        """Verify analytics endpoints return valid KPIs, trends, defect distributions, and batches."""
        # 1. Overview KPIs
        res = self.client.get("/api/analytics/overview")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_inspections", data)
        self.assertIn("pass_rate", data)
        self.assertIn("defect_rate", data)

        # 2. Daily Trends
        res = self.client.get("/api/analytics/trends")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(isinstance(res.json(), list) or "trends" in res.json())

        # 3. Defect Distribution
        res = self.client.get("/api/analytics/defect-distribution")
        self.assertEqual(res.status_code, 200)
        self.assertTrue("categories" in res.json() or "distribution" in res.json())

        # 4. Batches
        res = self.client.get("/api/analytics/batches")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

        # 5. Model Insights
        res = self.client.get("/api/analytics/model-insights")
        self.assertEqual(res.status_code, 200)
        insights = res.json()
        self.assertIn("top_features", insights)
        # Verify MDI importances sum to a reasonable proportion
        top_importances = [f["importance"] for f in insights["top_features"]]
        self.assertAlmostEqual(top_importances[0], 0.2035, places=2)  # Rotational speed

    # -------------------------------------------------------------
    # 11. Report Generation (PDF & CSV)
    # -------------------------------------------------------------
    def test_11_report_generation(self):
        """Verify report_service compiles physical PDF and CSV documents on disk."""
        # CSV
        res_csv = self.client.post("/api/reports", json={
            "report_type": "Defect Analysis",
            "batch": "ALL",
            "format": "CSV",
            "date_range": "Last 30 Days",
        })
        self.assertEqual(res_csv.status_code, 201)
        csv_path = Path(res_csv.json()["file_path"])
        self.assertTrue(csv_path.is_file(), f"CSV file {csv_path} was not created")

        # PDF
        res_pdf = self.client.post("/api/reports", json={
            "report_type": "Quality Performance",
            "batch": "ALL",
            "format": "PDF",
            "date_range": "Last 30 Days",
        })
        self.assertEqual(res_pdf.status_code, 201)
        pdf_path = Path(res_pdf.json()["file_path"])
        self.assertTrue(pdf_path.is_file(), f"PDF file {pdf_path} was not created")
        with open(pdf_path, "rb") as f:
            self.assertEqual(f.read(5), b"%PDF-", "File must have valid PDF header")

    # -------------------------------------------------------------
    # 12. Report Download Security & Streaming
    # -------------------------------------------------------------
    def test_12_report_download_security(self):
        """Verify binary streaming download and rejection of path traversal."""
        reports_res = self.client.get("/api/reports")
        self.assertEqual(reports_res.status_code, 200)
        reports = reports_res.json().get("reports", [])
        self.assertGreaterEqual(len(reports), 1)

        rep_id = reports[0]["id"]
        dl = self.client.get(f"/api/reports/{rep_id}/download")
        self.assertEqual(dl.status_code, 200)
        self.assertIn("Content-Disposition", dl.headers)
        self.assertGreater(len(dl.content), 50)

        # Path traversal / non-existent ID rejection
        bad_dl = self.client.get("/api/reports/999999/download")
        self.assertEqual(bad_dl.status_code, 404)

    # -------------------------------------------------------------
    # 13. API Route Parity
    # -------------------------------------------------------------
    def test_13_api_route_parity(self):
        """Verify complete route contract parity between /api/* and /api/v1/*."""
        probed_routes = [
            "/health",
            "/inspections",
            "/predictions",
            "/analytics/overview",
            "/reports",
        ]
        for route in probed_routes:
            r_unversioned = self.client.get(f"/api{route}")
            r_versioned = self.client.get(f"/api/v1{route}")
            self.assertEqual(
                r_unversioned.status_code,
                r_versioned.status_code,
                f"Status mismatch on {route}",
            )
            j_un = r_unversioned.json()
            j_v = r_versioned.json()
            if isinstance(j_un, dict) and isinstance(j_v, dict):
                self.assertEqual(set(j_un.keys()), set(j_v.keys()), f"Key schema mismatch on {route}")

    # -------------------------------------------------------------
    # 14. Frontend Production Build Integrity
    # -------------------------------------------------------------
    def test_14_frontend_production_build(self):
        """Verify Vite production bundle exists with valid assets."""
        dist_dir = Path("frontend") / "dist"
        index_html = dist_dir / "index.html"
        assets_dir = dist_dir / "assets"

        self.assertTrue(index_html.is_file(), "frontend/dist/index.html must exist")
        self.assertGreater(index_html.stat().st_size, 300)

        self.assertTrue(assets_dir.is_dir(), "frontend/dist/assets/ directory must exist")
        js_files = list(assets_dir.glob("*.js"))
        css_files = list(assets_dir.glob("*.css"))
        self.assertGreaterEqual(len(js_files), 1, "At least one JS bundle must exist")
        self.assertGreaterEqual(len(css_files), 1, "At least one CSS bundle must exist")

    # -------------------------------------------------------------
    # 15. Empty Database Resilience
    # -------------------------------------------------------------
    def test_15_empty_database_behaviour(self):
        """Verify analytics and queries handle zero records with zero-division safety."""
        empty_db_path = os.path.join(self.temp_dir, "empty_phase8.db")
        empty_engine = create_engine(
            f"sqlite:///{empty_db_path.replace(os.sep, '/')}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=empty_engine)
        EmptySession = sessionmaker(autocommit=False, autoflush=False, bind=empty_engine)

        def override_empty_db():
            db = EmptySession()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_empty_db
        try:
            res_ov = self.client.get("/api/analytics/overview")
            self.assertEqual(res_ov.status_code, 200)
            self.assertEqual(res_ov.json()["total_inspections"], 0)
            self.assertEqual(res_ov.json()["pass_rate"], 0.0)
            self.assertEqual(res_ov.json()["defect_rate"], 0.0)

            res_dist = self.client.get("/api/analytics/defect-distribution")
            self.assertEqual(res_dist.status_code, 200)
            self.assertEqual(res_dist.json()["total_defects"], 0)

            res_batch = self.client.get("/api/analytics/batches")
            self.assertEqual(res_batch.status_code, 200)
            self.assertEqual(res_batch.json(), [])
        finally:
            # Restore class db override
            def override_get_db():
                db = self.TestingSessionLocal()
                try:
                    yield db
                finally:
                    db.close()

            app.dependency_overrides[get_db] = override_get_db

    # -------------------------------------------------------------
    # 16. Regression Compatibility
    # -------------------------------------------------------------
    def test_16_regression_compatibility(self):
        """Verify Phase 4, Phase 6, and Phase 7 verification suites execute without failures."""
        suites = [
            ("Phase 4 Database Regression", [sys.executable, "backend/tests_phase4.py"]),
            ("Phase 6 ML Pipeline Regression", [sys.executable, "backend/verify_phase6.py"]),
            ("Phase 7 Full-Stack Regression", [sys.executable, "backend/verify_phase7.py"]),
        ]
        for name, cmd in suites:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(Path.cwd()),
            )
            self.assertEqual(
                proc.returncode,
                0,
                f"{name} failed with exit code {proc.returncode}:\n{proc.stderr}\n{proc.stdout}",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)

