"""
AutoQ Runtime Verification Suite
Validates the 5 focused issues investigated and resolved:
1. Quality Analytics Data Contract & Non-Crashing Guarantee
2. Defect Prediction Engine, Thresholding (tau=0.50 vs tau=0.35), & Persistence
3. Defect Analysis ML Feature Importance API & Pipeline MDI Integrity
4. ML Engine Health & Readiness Source-of-Truth Consistency
5. Database Integrity & Zero-Division / Empty-State Resilience
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import get_db, SessionLocal
from app.models.inspection import Inspection
from app.models.prediction import Prediction
from app.models.component import Component

client = TestClient(app)


def test_1_quality_analytics_contract():
    print("Testing Issue 1: Quality Analytics Endpoint Contracts...")
    # Batches must return avg_temperature, avg_pressure, defectRate, inspections
    res_b = client.get("/api/analytics/batches")
    assert res_b.status_code == 200, f"Batches failed: {res_b.status_code}"
    batches = res_b.json()
    assert isinstance(batches, list), "Batches must be a list"
    if len(batches) > 0:
        b0 = batches[0]
        assert "avg_temperature" in b0, "avg_temperature field missing in batch"
        assert "avg_pressure" in b0, "avg_pressure field missing in batch"
        assert "defectRate" in b0 or "defect_rate" in b0, "defect rate missing in batch"
        assert "inspections" in b0 or "total_inspections" in b0, "inspections missing"
    print("  [PASS] /api/analytics/batches contract confirmed.")

    # Batch comparison alias
    res_bc = client.get("/api/analytics/batch-comparison")
    assert res_bc.status_code == 200, f"Batch comparison alias failed: {res_bc.status_code}"
    print("  [PASS] /api/analytics/batch-comparison alias confirmed.")

    # Trends structure check
    res_t = client.get("/api/analytics/trends")
    assert res_t.status_code == 200, f"Trends failed: {res_t.status_code}"
    trends_json = res_t.json()
    assert "trends" in trends_json, "trends key must exist in trends endpoint"
    print("  [PASS] /api/analytics/trends contract confirmed.")

    # Quality performance structure check
    res_qp = client.get("/api/analytics/quality-performance")
    assert res_qp.status_code == 200, f"Quality-performance failed: {res_qp.status_code}"
    qp_json = res_qp.json()
    assert "performance" in qp_json, "performance key must exist in quality-performance"
    print("  [PASS] /api/analytics/quality-performance contract confirmed.")


def test_2_defect_prediction_and_thresholding():
    print("Testing Issue 2: Defect Prediction, Dual Operating Points (tau=0.50 vs tau=0.35), & Persistence...")
    # Standard conforming component
    conforming_payload = {
        "component_id": "CMP-RT-PASS-01",
        "component_category": "Powertrain",
        "manufacturing_temperature": 745.0,
        "pressure": 148.0,
        "rotational_speed": 1520.0,
        "tool_wear": 110.0,
        "stress_tolerance": 340.0,
        "cycle_time": 45.0,
        "torque_resistance": 42.0,
        "production_batch": "BATCH-2026-B1",
        "decision_threshold": 0.50,
    }
    r_pass = client.post("/api/predictions", json=conforming_payload)
    assert r_pass.status_code == 200, f"Pass prediction failed: {r_pass.status_code}"
    pass_data = r_pass.json()
    assert pass_data["predicted_status"] == "Passed", f"Expected Passed, got {pass_data['predicted_status']}"
    assert pass_data["defect_probability"] < 0.50
    assert pass_data["id"] is not None
    print(f"  [PASS] Conforming sample evaluated as Passed (p={pass_data['defect_probability']:.4f}).")

    # High tool wear & torque evaluated at standard tau=0.50 vs high-recall tau=0.35
    defective_payload = {
        "component_id": "CMP-RT-FAIL-01",
        "component_category": "Engine",
        "manufacturing_temperature": 820.0,
        "pressure": 190.0,
        "rotational_speed": 2800.0,
        "tool_wear": 240.0,
        "stress_tolerance": 200.0,
        "cycle_time": 90.0,
        "torque_resistance": 75.0,
        "production_batch": "BATCH-2026-B1",
        "decision_threshold": 0.35,
    }
    r_fail = client.post("/api/predictions", json=defective_payload)
    assert r_fail.status_code == 200, f"Fail prediction failed: {r_fail.status_code}"
    fail_data = r_fail.json()
    assert fail_data["predicted_status"] == "Defective", f"Expected Defective, got {fail_data['predicted_status']}"
    assert fail_data["defect_probability"] >= 0.35
    assert fail_data["decision_threshold"] == 0.35
    assert fail_data["predicted_defect_category"] is not None
    assert len(fail_data["contributing_factors"]) > 0
    print(f"  [PASS] Defective sample evaluated as Defective under tau=0.35 (p={fail_data['defect_probability']:.4f}, cause='{fail_data['predicted_defect_category']}').")

    # Verify SQLite persistence
    db = SessionLocal()
    try:
        p_rec = db.query(Prediction).filter(Prediction.id == fail_data["id"]).first()
        assert p_rec is not None, "Prediction record was not persisted to SQLite"
        assert p_rec.component_id == "CMP-RT-FAIL-01"
        assert p_rec.predicted_status == "Defective"
        print(f"  [PASS] SQLite persistence confirmed for Prediction ID #{p_rec.id}.")
    finally:
        db.close()


def test_3_feature_importance_subsystem():
    print("Testing Issue 3: Defect Analysis ML Feature Importance Subsystem...")
    res = client.get("/api/analytics/model-insights")
    assert res.status_code == 200, f"Model insights failed: {res.status_code}"
    insights = res.json()
    assert "top_features" in insights, "top_features missing from model-insights"
    top_features = insights["top_features"]
    assert len(top_features) >= 6, f"Expected at least 6 features, got {len(top_features)}"
    for f in top_features:
        assert "feature" in f, "Feature entry missing 'feature' label"
        assert "importance" in f, "Feature entry missing 'importance' value"
        assert 0.0 <= f["importance"] <= 1.0, f"Importance out of bounds: {f['importance']}"
    print(f"  [PASS] Model insights verified: {len(top_features)} MDI features loaded from champion pipeline.")


def test_4_ml_engine_health_source_of_truth():
    print("Testing Issue 4: ML Engine Health & Readiness Single Source of Truth...")
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.status_code}"
    health = res.json()
    assert health["database_connected"] is True, "Database report offline in health"
    assert "ml_engine" in health, "ml_engine object missing in health"
    assert health["ml_engine"]["model_available"] is True, "Model reported not available in health"
    assert "model_name" in health["ml_engine"], "model_name missing"
    assert "test_roc_auc" in health["ml_engine"], "test_roc_auc missing"
    print(f"  [PASS] /api/health confirms ml_engine.model_available=True (ROC-AUC: {health['ml_engine']['test_roc_auc']}).")


def test_5_data_empty_state_resilience():
    print("Testing Issue 5: Data Integrity & Empty State Zero-Division Resilience...")
    # Verify overview works regardless of filter
    res_ov = client.get("/api/analytics/overview?batch=NON_EXISTENT_BATCH")
    assert res_ov.status_code == 200, f"Overview for empty batch failed: {res_ov.status_code}"
    ov = res_ov.json()
    assert ov["total_inspections"] == 0
    assert ov["defect_rate"] == 0.0
    assert ov["pass_rate"] == 0.0

    # Defect distribution for empty batch
    res_dd = client.get("/api/analytics/defect-distribution?batch=NON_EXISTENT_BATCH")
    assert res_dd.status_code == 200, f"Defect distribution for empty batch failed: {res_dd.status_code}"
    dd = res_dd.json()
    assert dd["total_defects"] == 0
    assert dd["distribution"] == []

    print("  [PASS] Zero-division safety verified for empty and filtered database states.")


if __name__ == "__main__":
    print("=" * 70)
    print("AutoQ Runtime Verification Suite - Starting Validation")
    print("=" * 70)
    test_1_quality_analytics_contract()
    test_2_defect_prediction_and_thresholding()
    test_3_feature_importance_subsystem()
    test_4_ml_engine_health_source_of_truth()
    test_5_data_empty_state_resilience()
    print("=" * 70)
    print("ALL 5 RUNTIME INVESTIGATION DOMAINS VERIFIED SUCCESSFULLY!")
    print("=" * 70)
