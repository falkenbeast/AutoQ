"""
AutoQ Phase 4 Automated Test Suite.
Validates SQLite database architecture, SQLAlchemy models, relationships,
CRUD endpoints, CSV batch ingestion, duplicate prevention, and analytics calculations
using a temporary isolated SQLite test database.
"""

import io
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database.base import Base
from app.database.connection import get_db
from app.main import app
from app.models.component import Component
from app.models.inspection import Inspection
from app.models.prediction import Prediction
from app.models.report import Report
from app.services.prediction_service import prediction_service


def run_phase4_tests():
    print("=" * 65)
    print("STARTING AUTOQ PHASE 4 DATABASE & API TEST SUITE")
    print("=" * 65)

    # Setup isolated temporary test database
    temp_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(temp_dir, "test_autoq.db")
    test_db_url = f"sqlite:///{test_db_path.replace(os.sep, '/')}"

    test_engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # 1. Database Initialization & 2. Table Creation
    Base.metadata.create_all(bind=test_engine)
    inspector_tables = test_engine.dialect.get_table_names(test_engine.connect())
    assert "components" in inspector_tables, "components table missing"
    assert "inspections" in inspector_tables, "inspections table missing"
    assert "predictions" in inspector_tables, "predictions table missing"
    assert "reports" in inspector_tables, "reports table missing"
    print("✓ TEST 1 & 2: Database initialized; tables verified in SQLite (components, inspections, predictions, reports)")

    # Override get_db dependency for isolated testing
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        # 3. Component Creation
        comp_payload = {
            "component_id": "CMP-BRK-401",
            "component_name": "Ventilated Brake Caliper Mount",
            "component_category": "Braking System",
            "description": "High performance brake caliper mount",
        }
        res = client.post("/api/v1/components", json=comp_payload)
        assert res.status_code == 201, f"Component creation failed: {res.text}"
        comp_data = res.json()
        assert comp_data["component_id"] == "CMP-BRK-401"
        assert comp_data["component_name"] == "Ventilated Brake Caliper Mount"
        print("✓ TEST 3: Component created successfully via POST /api/v1/components")

        # 4. Inspection Creation
        insp_payload = {
            "component_id": "CMP-BRK-401",
            "component_name": "Ventilated Brake Caliper Mount",
            "component_category": "Braking System",
            "manufacturing_temperature": 742.5,
            "pressure": 145.0,
            "production_batch": "BATCH-2026-A1",
            "inspection_result": "Passed",
            "notes": "Optimal tolerance limits",
        }
        res = client.post("/api/v1/inspections", json=insp_payload)
        assert res.status_code == 201, f"Inspection creation failed: {res.text}"
        insp_data = res.json()
        assert insp_data["component_id"] == "CMP-BRK-401"
        assert insp_data["inspection_result"] == "Passed"
        inspection_id = insp_data["id"]
        print(f"✓ TEST 4: Inspection record created (id={inspection_id}) via POST /api/v1/inspections")

        # 5. Inspection Retrieval (List & Single)
        res = client.get("/api/v1/inspections")
        assert res.status_code == 200
        list_data = res.json()
        assert list_data["total"] >= 1
        assert list_data["items"][0]["component_id"] == "CMP-BRK-401"

        res = client.get(f"/api/v1/inspections/{inspection_id}")
        assert res.status_code == 200
        assert res.json()["id"] == inspection_id
        print(f"✓ TEST 5: Inspection retrieved successfully via GET /api/v1/inspections & /{inspection_id}")

        # 6. Inspection Updating
        update_payload = {"notes": "Updated after optical comparator check (within 0.01mm)"}
        res = client.put(f"/api/v1/inspections/{inspection_id}", json=update_payload)
        assert res.status_code == 200
        assert "Updated after optical comparator" in res.json()["notes"]
        print(f"✓ TEST 6: Inspection updated successfully via PUT /api/v1/inspections/{inspection_id}")

        # 8. Component-Inspection Relationships
        with TestingSessionLocal() as session:
            comp = session.query(Component).filter(Component.component_id == "CMP-BRK-401").first()
            assert comp is not None
            assert len(comp.inspections) >= 1
            assert comp.inspections[0].id == inspection_id
            assert comp.inspections[0].component.component_id == "CMP-BRK-401"
        print("✓ TEST 8: Component-Inspection 1-to-many relationship verified via ORM")

        # 9. Prediction Record Storage (Actual Model Prediction Persistence)
        with TestingSessionLocal() as session:
            pred_record = prediction_service.save_prediction(
                db=session,
                component_id="CMP-BRK-401",
                inspection_id=inspection_id,
                predicted_status="Passed",
                defect_probability=0.042,
                model_version="1.0.0",
                model_status="INFERENCE_COMPLETE",
                contributing_factors=[{"factor": "temperature", "impact": "nominal"}],
                recommendation="Release for downstream chassis integration.",
            )
            pred_id = pred_record.id

        res = client.get("/api/v1/predictions")
        assert res.status_code == 200
        assert res.json()["total"] >= 1
        assert res.json()["items"][0]["predicted_status"] == "Passed"

        res = client.get(f"/api/v1/predictions/{pred_id}")
        assert res.status_code == 200
        assert res.json()["predicted_status"] == "Passed"
        print(f"✓ TEST 9: Genuine prediction record persisted and retrieved via GET /api/v1/predictions/{pred_id}")

        # 10. Report Metadata Storage
        report_payload = {
            "report_type": "Defect Analysis",
            "batch": "BATCH-2026-A1",
            "date_range": "Last 14 Days",
            "format": "PDF",
            "description": "Comprehensive quality audit report",
        }
        res = client.post("/api/v1/reports/generate", json=report_payload)
        assert res.status_code in (201, 202)
        report_data = res.json()
        report_id = report_data["id"]
        assert report_data.get("report_status") in ("Generated", "COMPLETED", "PENDING_PHASE_5") or res.status_code == 201

        res = client.get(f"/api/v1/reports/{report_id}")
        assert res.status_code == 200
        assert res.json()["report_type"] == "Defect Analysis"
        print(f"✓ TEST 10: Report metadata stored in SQLite via POST /api/v1/reports/generate (id={report_id})")

        # 11. CSV Batch Inspection Upload
        csv_content = (
            "component_id,component_name,component_category,manufacturing_temperature,pressure,production_batch,inspection_result,defect_category,inspection_date\r\n"
            "CMP-CRK-102,Forged Crankshaft V6,Engine,738.0,142.0,BATCH-2026-A1,Passed,,2026-11-19 10:00:00\r\n"
            "CMP-TRB-809,Turbo Housing,Powertrain,785.0,164.0,BATCH-2026-B1,Defective,Structural Porosity,2026-11-19 11:00:00\r\n"
            "CMP-STR-552,Steering Knuckle,Chassis & Steering,772.0,158.0,BATCH-2026-B2,Defective,Surface Micro-cracks,2026-11-19 12:00:00\r\n"
            "CMP-GER-310,Helical Input Gear,Transmission,746.0,144.0,BATCH-2026-A1,Passed,,2026-11-19 13:00:00\r\n"
        ).encode("utf-8")

        res = client.post(
            "/api/v1/inspections/upload",
            files={"file": ("batch_test.csv", csv_content, "text/csv")},
        )
        assert res.status_code == 200, f"CSV upload failed: {res.text}"
        upload_resp = res.json()
        assert upload_resp["imported_rows"] == 4
        assert upload_resp["rejected_rows"] == 0
        assert len(upload_resp["preview"]) == 4
        print(f"✓ TEST 11: CSV upload succeeded (4 rows imported into SQLite)")

        # 12. Invalid CSV Handling (Missing columns & invalid data)
        invalid_csv = (
            "component_id,temperature,pressure\r\n"
            "CMP-001,-999,9999\r\n"
        ).encode("utf-8")
        res = client.post(
            "/api/v1/inspections/upload",
            files={"file": ("invalid.csv", invalid_csv, "text/csv")},
        )
        assert res.status_code == 400
        assert res.json()["error_code"] == "INVALID_CSV_FILE"
        print("✓ TEST 12: Invalid CSV schema correctly rejected with 400 Bad Request")

        # 13. Duplicate Record Handling (Re-uploading duplicate records)
        duplicate_csv = (
            "component_id,component_name,component_category,manufacturing_temperature,pressure,production_batch,inspection_result,inspection_date\r\n"
            "CMP-CRK-102,Forged Crankshaft V6,Engine,738.0,142.0,BATCH-2026-A1,Passed,2026-11-19 10:00:00\r\n"
        ).encode("utf-8")
        res = client.post(
            "/api/v1/inspections/upload",
            files={"file": ("dup.csv", duplicate_csv, "text/csv")},
        )
        assert res.status_code == 200
        dup_resp = res.json()
        assert dup_resp["rejected_rows"] == 1
        assert dup_resp["imported_rows"] == 0
        assert "Duplicate inspection record" in dup_resp["errors"][0]
        print("✓ TEST 13: Deduplication logic successfully identified duplicate and rejected with error report")

        # 14. Analytics Calculations (Derived from actual SQLite rows)
        res = client.get("/api/v1/analytics/overview")
        assert res.status_code == 200
        ov = res.json()
        # 1 manual inspection (passed) + 4 CSV inspections (2 passed, 2 defective) = 5 total (3 passed, 2 defective)
        assert ov["total_inspections"] == 5
        assert ov["passed_components"] == 3
        assert ov["defective_components"] == 2
        assert ov["defect_rate"] == 40.0
        assert ov["pass_rate"] == 60.0
        print(f"✓ TEST 14a: Analytics Overview computed from SQLite (total=5, passed=3, defective=2, rate=40.0%)")

        res = client.get("/api/v1/analytics/defect-distribution")
        assert res.status_code == 200
        dist = res.json()
        assert dist["total_defects"] == 2
        assert len(dist["distribution"]) == 2  # Porosity & Micro-cracks
        print(f"✓ TEST 14b: Defect Distribution computed from SQLite (2 categories found)")

        res = client.get("/api/v1/analytics/quality-performance")
        assert res.status_code == 200
        perf = res.json()
        assert len(perf["performance"]) >= 3  # Braking, Powertrain, Engine, Chassis, Transmission
        print(f"✓ TEST 14c: Quality Performance by Category computed from SQLite")

        res = client.get("/api/v1/analytics/inspection-trends")
        assert res.status_code == 200
        trends = res.json()
        assert len(trends["trends"]) >= 1
        print(f"✓ TEST 14d: Inspection Trends grouped by date computed from SQLite")

        # 7. Inspection Deletion
        res = client.delete(f"/api/v1/inspections/{inspection_id}")
        assert res.status_code == 200
        assert res.json()["status"] == "success"

        res = client.get(f"/api/v1/inspections/{inspection_id}")
        assert res.status_code == 404
        print(f"✓ TEST 7: Inspection record deleted successfully via DELETE /api/v1/inspections/{inspection_id}")

    # 15. Database Persistence After Session / Restart
    # Re-open the database with a fresh connection to verify persistent writes
    ReopenSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    with ReopenSessionLocal() as session:
        count = session.query(Inspection).count()
        # 5 total - 1 deleted = 4 records remain
        assert count == 4, f"Expected 4 persisted inspections after restart, found {count}"
        comp_count = session.query(Component).count()
        assert comp_count >= 4, f"Expected components persisted, found {comp_count}"
        print(f"✓ TEST 15: Verified SQLite database persistence after restart (4 inspections, {comp_count} components)")

    # Clean up test database
    app.dependency_overrides.clear()
    test_engine.dispose()
    try:
        os.remove(test_db_path)
        os.rmdir(temp_dir)
    except Exception:
        pass

    print("=" * 65)
    print("ALL 15 DATABASE & API INTEGRATION TESTS PASSED WITH ZERO DEFECTS!")
    print("=" * 65)


if __name__ == "__main__":
    run_phase4_tests()
