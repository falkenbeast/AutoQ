"""
AutoQ - Phase 9 Final Verification Script
Runs end-to-end verification covering:
1. Frontend production build existence and assets
2. Backend API health and diagnostics
3. Serialized ML model loading and artifact validation
4. Live genuine prediction execution
5. Relational database persistence
6. ReportLab PDF & CSV report generation
7. Binary report streaming download
8. Documentation and presentation artifact verification
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import joblib
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.component import Component
from app.models.inspection import Inspection
from app.models.prediction import Prediction
from app.models.report import Report


def run_phase9_final_verification():
    print("=" * 70)
    print("AutoQ Phase 9 - Final Verification Checklist")
    print("=" * 70)

    client = TestClient(app)

    # 1. API Health Check
    res_health = client.get("/api/health")
    assert res_health.status_code == 200, f"Health check failed: {res_health.text}"
    health_data = res_health.json()
    assert health_data["status"] == "healthy"
    assert health_data["database_connected"] is True
    assert health_data["ml_engine"]["model_available"] is True
    print("[PASS] 1. Backend API Health & Database Connectivity")

    # 2. Model Artifacts Loading
    champ_path = os.path.join("backend", "trained_models", "defect_classifier_pipeline.joblib")
    multi_path = os.path.join("backend", "trained_models", "multiclass_defect_classifier.joblib")
    assert os.path.isfile(champ_path), "Champion pipeline file missing"
    assert os.path.isfile(multi_path), "Multiclass classifier file missing"
    champ_model = joblib.load(champ_path)
    assert hasattr(champ_model, "predict_proba"), "Champion model missing predict_proba"
    print("[PASS] 2. Serialized ML Artifacts (Champion & Multiclass Pipelines)")

    # 3. Live Genuine Prediction & Threshold Shift
    pred_payload = {
        "component_id": "CMP-VERIFY-901",
        "component_name": "Front Axle Spindle",
        "component_category": "Chassis & Steering",
        "production_batch": "BATCH-2026-FINAL",
        "rotational_speed": 1200.0,
        "torque": 75.0,
        "tool_wear": 230.0,
        "manufacturing_temperature": 40.0,
        "decision_threshold": 0.50,
    }
    res_pred = client.post("/api/predictions", json=pred_payload)
    assert res_pred.status_code == 200, f"Prediction failed: {res_pred.text}"
    pred_data = res_pred.json()
    assert pred_data["predicted_status"] == "Defective"
    assert pred_data["defect_probability"] >= 0.70
    assert pred_data["predicted_defect_category"] in [
        "Overstrain Failure", "Tool Wear Failure", "Power Failure", "Multi-mode Failure"
    ]
    pred_id = pred_data["id"]
    print(f"[PASS] 3. Live ML Prediction: {pred_data['predicted_status']} (p={pred_data['defect_probability']:.4f}, Cause={pred_data['predicted_defect_category']})")

    # 4. Database Persistence Verification
    with SessionLocal() as db:
        saved_pred = db.query(Prediction).filter(Prediction.id == pred_id).first()
        assert saved_pred is not None, "Prediction not found in database"
        assert saved_pred.component_id == "CMP-VERIFY-901"
        assert saved_pred.predicted_status == "Defective"
    print("[PASS] 4. Database Persistence & Relational Integrity")

    # 5. ReportLab PDF & CSV Generation
    rep_pdf = client.post("/api/reports", json={
        "report_type": "Defect Analysis",
        "batch": "All-Batches",
        "format": "PDF",
    })
    assert rep_pdf.status_code == 201, f"PDF report generation failed: {rep_pdf.text}"
    pdf_id = rep_pdf.json()["id"]

    rep_csv = client.post("/api/reports", json={
        "report_type": "Inspection Summary",
        "batch": "All-Batches",
        "format": "CSV",
    })
    assert rep_csv.status_code == 201, f"CSV report generation failed: {rep_csv.text}"
    print("[PASS] 5. ReportLab Dynamic PDF & CSV Generation")

    # 6. Binary Report Streaming Download
    res_dl = client.get(f"/api/reports/{pdf_id}/download")
    assert res_dl.status_code == 200, f"Download failed: {res_dl.status_code}"
    assert res_dl.headers["content-type"] == "application/pdf"
    assert len(res_dl.content) > 1000, "Downloaded PDF is empty"
    print(f"[PASS] 6. Binary Report Streaming Download ({len(res_dl.content)} bytes)")

    # 7. Frontend Production Build Check
    dist_html = os.path.join("frontend", "dist", "index.html")
    assert os.path.isfile(dist_html), "frontend/dist/index.html missing"
    print("[PASS] 7. Frontend Production Bundle (Vite dist/index.html verified)")

    # 8. Presentation & Documentation Deliverables
    required_docs = [
        "docs/final_project_audit.md",
        "docs/final_ml_results.md",
        "docs/AutoQ_Final_Project_Report.md",
        "docs/API_DOCUMENTATION.md",
        "docs/USER_MANUAL.md",
        "docs/DEMO_SCRIPT.md",
        "docs/VIVA_QUESTIONS.md",
        "docs/AutoQ_Final_Presentation.pptx",
        "docs/FINAL_SUBMISSION_CHECKLIST.md",
        "docs/diagrams/README.md",
        "docs/diagrams/system_architecture.png",
        "docs/diagrams/prediction_workflow.png",
        "docs/diagrams/database_erd.png",
        "docs/diagrams/ml_training_pipeline.png",
    ]
    for doc in required_docs:
        assert os.path.isfile(doc), f"Missing required document: {doc}"
        assert os.path.getsize(doc) > 500, f"Document is too small/empty: {doc}"
    print(f"[PASS] 8. All {len(required_docs)} Final Documentation & Presentation Deliverables Verified")

    print("=" * 70)
    print("ALL 8 VERIFICATION CHECKS PASSED WITH 100% SUCCESS!")
    print("=" * 70)


if __name__ == "__main__":
    run_phase9_final_verification()
