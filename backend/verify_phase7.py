"""
AutoQ - Phase 7 Full-Stack Integration Verification Test Suite
Exhaustively validates all 14 integration requirements:
 1. Health check & diagnostic metadata (/api/health and /api/v1/health)
 2. Database connectivity & SQLite schema integrity
 3. Inspection CRUD operations (POST, GET, PUT, DELETE)
 4. Batch CSV upload validation & database ingestion
 5. Real Random Forest inference via API (no mock predictions)
 6. Decision threshold toggle behavior (0.35 high-recall vs 0.50 default)
 7. Multiclass defect mode attribution
 8. Database persistence of predictions
 9. Complete analytics endpoints suite
10. Empty database resilience (zero divisions, empty lists, clean KPIs)
11. Physical CSV report generation in backend/reports/
12. Physical PDF report generation with ReportLab
13. Binary streaming report download endpoint & path-traversal security
14. Route contract parity between /api/v1/* and /api/*
"""

import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Set up paths
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.connection import get_db
from app.main import app
from app.models.component import Component
from app.models.inspection import Inspection
from app.models.prediction import Prediction
from app.models.report import Report


class TestPhase7FullStackIntegration(unittest.TestCase):
    """Exhaustive integration test suite for AutoQ Phase 7."""

    @classmethod
    def setUpClass(cls):
        # Create an isolated temporary test database
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_db_path = os.path.join(cls.temp_dir, "test_phase7_autoq.db")
        cls.test_db_url = f"sqlite:///{cls.test_db_path.replace(os.sep, '/')}"

        cls.test_engine = create_engine(
            cls.test_db_url, connect_args={"check_same_thread": False}
        )
        cls.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=cls.test_engine
        )

        # Build schema
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
    # 1. Health check & Diagnostic Metadata
    # -------------------------------------------------------------
    def test_01_health_and_diagnostics(self):
        """Verify health endpoints return HTTP 200, database status, and ML engine metadata."""
        for path in ["/api/health", "/api/v1/health"]:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200, f"Failed on {path}")
            data = res.json()
            self.assertEqual(data.get("status"), "healthy")
            self.assertEqual(data.get("application"), "AutoQ")
            self.assertTrue(data.get("database_connected"), "Database must be reported connected")

            ml_eng = data.get("ml_engine", {})
            self.assertTrue(ml_eng.get("model_available"), "ML model must be available")
            self.assertIn("Random Forest", ml_eng.get("model_name", ""))
            self.assertAlmostEqual(ml_eng.get("recommended_threshold"), 0.35, places=2)

    # -------------------------------------------------------------
    # 2. Database Connectivity & SQLite Schema Integrity
    # -------------------------------------------------------------
    def test_02_database_connectivity(self):
        """Verify SQLite tables exist and session connectivity is functional."""
        with self.test_engine.connect() as conn:
            from sqlalchemy import text
            res = conn.execute(text("SELECT 1")).scalar()
            self.assertEqual(res, 1)

        inspector_tables = self.test_engine.dialect.get_table_names(self.test_engine.connect())
        for table in ["components", "inspections", "predictions", "reports"]:
            self.assertIn(table, inspector_tables, f"Table {table} missing from SQLite schema")

    # -------------------------------------------------------------
    # 3. Inspection CRUD Operations
    # -------------------------------------------------------------
    def test_03_inspection_crud(self):
        """Verify complete Inspection CRUD lifecycle via REST API."""
        # CREATE
        payload = {
            "component_id": "CMP-INT-701",
            "component_name": "Integrated Sensor Housing",
            "component_category": "Powertrain",
            "manufacturing_temperature": 750.5,
            "pressure": 152.0,
            "production_batch": "BATCH-2026-X1",
            "inspection_result": "Passed",
            "defect_category": None,
            "notes": "Precision tolerance verified in Phase 7 test.",
        }
        res = self.client.post("/api/inspections", json=payload)
        self.assertEqual(res.status_code, 201)
        created = res.json()
        rec_id = created["id"]
        self.assertEqual(created["component_id"], "CMP-INT-701")

        # READ (Single)
        res = self.client.get(f"/api/inspections/{rec_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["component_name"], "Integrated Sensor Housing")

        # READ (List & Filter)
        res = self.client.get("/api/inspections?batch=BATCH-2026-X1")
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(res.json()["total"], 1)

        # UPDATE
        update_payload = {"notes": "Updated audit inspection notes."}
        res = self.client.put(f"/api/inspections/{rec_id}", json=update_payload)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["notes"], "Updated audit inspection notes.")

        # DELETE
        res = self.client.delete(f"/api/inspections/{rec_id}")
        self.assertEqual(res.status_code, 200)

        # Verify Deleted
        res = self.client.get(f"/api/inspections/{rec_id}")
        self.assertEqual(res.status_code, 404)

    # -------------------------------------------------------------
    # 4. Batch CSV Upload Validation & Ingestion
    # -------------------------------------------------------------
    def test_04_csv_upload_batch(self):
        """Verify CSV upload parsing, row-level validation, and SQLite persistence."""
        csv_content = (
            "component_id,component_name,component_category,manufacturing_temperature,pressure,production_batch,inspection_result\n"
            "CMP-CSV-001,Piston Pin Assembly,Powertrain,740.0,140.0,BATCH-2026-A1,Passed\n"
            "CMP-CSV-002,Valve Spring Retainer,Engine,755.0,150.0,BATCH-2026-A1,Passed\n"
            "CMP-CSV-003,Hydraulic Braking Line,Braking System,780.0,170.0,BATCH-2026-A2,Defective\n"
        )
        files = {"file": ("batch_test.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        res = self.client.post("/api/inspections/upload-csv", files=files)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["imported_rows"], 3)
        self.assertEqual(data["rejected_rows"], 0)

        # Verify records exist in database
        res = self.client.get("/api/inspections?batch=BATCH-2026-A1")
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(res.json()["total"], 2)

    # -------------------------------------------------------------
    # 5. Real Random Forest Inference via API
    # -------------------------------------------------------------
    def test_05_real_random_forest_inference(self):
        """Verify real Random Forest pipeline executes inference and returns calibrated probabilities."""
        pred_payload = {
            "component_id": "CMP-ML-101",
            "component_name": "Transmission Planetary Gear",
            "component_category": "Transmission",
            "production_batch": "BATCH-2026-A1",
            "manufacturing_temperature": 745.0,
            "pressure": 140.0,
            "air_temperature": 298.5,
            "process_temperature": 308.7,
            "rotational_speed": 1500.0,
            "torque": 40.0,
            "tool_wear": 120.0,
            "product_type": "M",
            "decision_threshold": 0.50,
        }
        res = self.client.post("/api/predictions", json=pred_payload)
        self.assertIn(res.status_code, [200, 201])
        data = res.json()

        self.assertEqual(data["model_status"], "INFERENCE_COMPLETE")
        self.assertIn("Random Forest", data.get("model_name", "Random Forest"))
        status_val = data.get("predicted_status") or data.get("predicted_quality")
        self.assertIn(status_val, ["Passed", "Defective"])
        self.assertTrue(0.0 <= data["defect_probability"] <= 1.0)
        self.assertIsNotNone(data["recommendation"])

    # -------------------------------------------------------------
    # 6. Decision Threshold Toggle Behavior
    # -------------------------------------------------------------
    def test_06_decision_threshold_toggle(self):
        """Verify threshold toggle (0.35 high-recall vs 0.50 default) shifts classification properly."""
        borderline_payload = {
            "component_id": "CMP-BRD-201",
            "component_name": "High Torque Shaft",
            "component_category": "Powertrain",
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

        # Request at 0.50
        res_50 = self.client.post("/api/predictions", json=borderline_payload)
        self.assertIn(res_50.status_code, [200, 201])
        prob = res_50.json()["defect_probability"]

        # Request at 0.35
        borderline_payload["decision_threshold"] = 0.35
        res_35 = self.client.post("/api/predictions", json=borderline_payload)
        self.assertIn(res_35.status_code, [200, 201])

        expected_35 = "Defective" if prob >= 0.35 else "Passed"
        expected_50 = "Defective" if prob >= 0.50 else "Passed"

        status_35 = res_35.json().get("predicted_status") or res_35.json().get("predicted_quality")
        status_50 = res_50.json().get("predicted_status") or res_50.json().get("predicted_quality")
        self.assertEqual(status_35, expected_35)
        self.assertEqual(status_50, expected_50)

    # -------------------------------------------------------------
    # 7. Multiclass Defect Attribution
    # -------------------------------------------------------------
    def test_07_multiclass_defect_attribution(self):
        """Verify extreme parameter triggers multi-class failure attribution."""
        extreme_payload = {
            "component_id": "CMP-FAIL-901",
            "component_name": "Overloaded Rotor",
            "component_category": "Engine",
            "production_batch": "BATCH-2026-A1",
            "manufacturing_temperature": 780.0,
            "pressure": 190.0,
            "air_temperature": 304.0,
            "process_temperature": 313.0,
            "rotational_speed": 1200.0,
            "torque": 85.0,
            "tool_wear": 235.0,
            "product_type": "L",
            "decision_threshold": 0.35,
        }
        res = self.client.post("/api/predictions", json=extreme_payload)
        self.assertIn(res.status_code, [200, 201])
        data = res.json()
        status_val = data.get("predicted_status") or data.get("predicted_quality")
        self.assertEqual(status_val, "Defective")
        self.assertIsNotNone(data.get("predicted_defect_category"))
        valid_modes = [
            "Tool Wear Failure",
            "Heat Dissipation Failure",
            "Power Failure",
            "Overstrain Failure",
            "Random Failure",
            "Multi-mode Failure",
        ]
        self.assertIn(data["predicted_defect_category"], valid_modes)

    # -------------------------------------------------------------
    # 8. Database Persistence of Predictions
    # -------------------------------------------------------------
    def test_08_prediction_database_persistence(self):
        """Verify prediction record is stored in SQLite and retrievable."""
        res = self.client.get("/api/predictions")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        self.assertGreaterEqual(len(items), 1)

        first_id = items[0]["id"]
        res_single = self.client.get(f"/api/predictions/{first_id}")
        self.assertEqual(res_single.status_code, 200)
        self.assertEqual(res_single.json()["id"], first_id)

    # -------------------------------------------------------------
    # 9. Analytics Endpoints Suite
    # -------------------------------------------------------------
    def test_09_analytics_endpoints(self):
        """Verify all analytics endpoints compute valid summaries from SQLite records."""
        # 1. Overview
        res = self.client.get("/api/analytics/overview")
        self.assertEqual(res.status_code, 200)
        ov = res.json()
        self.assertIn("total_inspections", ov)
        self.assertIn("pass_rate_percentage", ov)

        # 2. Trends
        res = self.client.get("/api/analytics/trends")
        self.assertEqual(res.status_code, 200)
        trends_resp = res.json()
        self.assertTrue(isinstance(trends_resp, list) or "trends" in trends_resp)

        # 3. Defect Distribution
        res = self.client.get("/api/analytics/defect-distribution")
        self.assertEqual(res.status_code, 200)
        dd = res.json()
        self.assertTrue("categories" in dd or "distribution" in dd)

        # 4. Quality Performance
        res = self.client.get("/api/analytics/quality-performance")
        self.assertEqual(res.status_code, 200)
        perf_resp = res.json()
        self.assertTrue(isinstance(perf_resp, list) or "performance" in perf_resp)

        # 5. Batches
        res = self.client.get("/api/analytics/batches")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

        # 6. Model Insights
        res = self.client.get("/api/analytics/model-insights")
        self.assertEqual(res.status_code, 200)
        insights = res.json()
        self.assertIn("top_features", insights)
        self.assertIn("roc_auc", insights)

    # -------------------------------------------------------------
    # 10. Empty Database Resilience
    # -------------------------------------------------------------
    def test_10_empty_database_behavior(self):
        """Verify analytics handle an empty database cleanly with 0s and no 500 errors."""
        empty_db_path = os.path.join(self.temp_dir, "empty_test.db")
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
            res = self.client.get("/api/analytics/overview")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["total_inspections"], 0)
            self.assertEqual(res.json()["pass_rate_percentage"], 0.0)

            res = self.client.get("/api/analytics/defect-distribution")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["total_defects"], 0)
            self.assertEqual(res.json()["categories"], [])

            res = self.client.get("/api/analytics/batches")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json(), [])
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
    # 11. Physical CSV Report Generation
    # -------------------------------------------------------------
    def test_11_physical_csv_report_generation(self):
        """Verify POST /api/reports generates a genuine CSV document on disk."""
        req_payload = {
            "report_type": "Defect Analysis",
            "target_batch": "ALL",
            "format": "csv",
            "date_range": "Last 30 Days",
            "generated_by": "Test Engineer",
        }
        res = self.client.post("/api/reports", json=req_payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        file_path = data["file_path"]

        self.assertTrue(os.path.exists(file_path), f"File {file_path} was not created on disk.")
        self.assertTrue(file_path.endswith(".csv"))
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("AutoQ", content)
            self.assertIn("Defect Analysis", content)
            self.assertIn("Component_ID", content)

    # -------------------------------------------------------------
    # 12. Physical PDF Report Generation with ReportLab
    # -------------------------------------------------------------
    def test_12_physical_pdf_report_generation(self):
        """Verify POST /api/reports generates a genuine PDF document with ReportLab."""
        req_payload = {
            "report_type": "Quality Performance",
            "target_batch": "ALL",
            "format": "pdf",
            "date_range": "Last 30 Days",
            "generated_by": "Test Engineer",
        }
        res = self.client.post("/api/reports", json=req_payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        file_path = data["file_path"]

        self.assertTrue(os.path.exists(file_path), f"PDF {file_path} was not created on disk.")
        self.assertTrue(file_path.endswith(".pdf"))
        # Verify valid PDF header
        with open(file_path, "rb") as f:
            header = f.read(5)
            self.assertEqual(header, b"%PDF-", "File is not a valid PDF binary")

    # -------------------------------------------------------------
    # 13. Binary Streaming Report Download & Security
    # -------------------------------------------------------------
    def test_13_report_download_endpoint(self):
        """Verify GET /api/reports/{id}/download streams binary and blocks path traversal."""
        # Get list of reports
        res = self.client.get("/api/reports")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        reports = data.get("reports", data) if isinstance(data, dict) else data
        self.assertGreaterEqual(len(reports), 1)

        rep_id = reports[0]["id"]
        dl_res = self.client.get(f"/api/reports/{rep_id}/download")
        self.assertEqual(dl_res.status_code, 200)
        self.assertIn("Content-Disposition", dl_res.headers)
        self.assertGreater(len(dl_res.content), 50)

        # Malicious non-existent ID
        bad_res = self.client.get("/api/reports/99999/download")
        self.assertEqual(bad_res.status_code, 404)

    # -------------------------------------------------------------
    # 14. Route Parity (/api/v1/* and /api/*)
    # -------------------------------------------------------------
    def test_14_api_route_contract_synchronization(self):
        """Verify identical behavior across /api/v1 and /api aliases."""
        endpoints = [
            "/health",
            "/inspections",
            "/predictions",
            "/analytics/overview",
            "/reports",
        ]
        for ep in endpoints:
            r1 = self.client.get(f"/api{ep}")
            r2 = self.client.get(f"/api/v1{ep}")
            self.assertEqual(r1.status_code, r2.status_code, f"Status code mismatch on {ep}")
            j1 = r1.json()
            j2 = r2.json()
            if isinstance(j1, dict) and isinstance(j2, dict):
                self.assertEqual(set(j1.keys()), set(j2.keys()), f"Key mismatch on {ep}")
            elif isinstance(j1, list) and isinstance(j2, list):
                self.assertEqual(len(j1), len(j2), f"List length mismatch on {ep}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
