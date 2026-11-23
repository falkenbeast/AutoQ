"""
AutoQ Phase 3 & 4 Verification Test Suite.
Validates API route registration, Pydantic schemas, validation errors,
missing ML model handling, CSV processing, and CORS headers.
"""

import io
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn
from app.main import app

BASE_URL = "http://127.0.0.1:8000"


def send_request(
    path: str,
    method: str = "GET",
    data: dict = None,
    headers: dict = None,
    files: dict = None,
):
    url = f"{BASE_URL}{path}"
    req_headers = headers or {}

    body = None
    if data is not None and files is None:
        body = json.dumps(data).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    elif files is not None:
        boundary = "----WebKitFormBoundaryAutoQTest"
        req_headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        buf = io.BytesIO()
        for field_name, (filename, file_bytes, content_type) in files.items():
            buf.write(f"--{boundary}\r\n".encode("utf-8"))
            buf.write(
                f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode(
                    "utf-8"
                )
            )
            buf.write(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
            buf.write(file_bytes)
            buf.write(b"\r\n")
        buf.write(f"--{boundary}--\r\n".encode("utf-8"))
        body = buf.getvalue()

    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode("utf-8")
            try:
                parsed = json.loads(resp_body) if resp_body.strip() else None
            except Exception:
                parsed = resp_body
            return {
                "status_code": resp.status,
                "headers": {k.lower(): v for k, v in resp.headers.items()},
                "data": parsed,
            }
    except urllib.error.HTTPError as err:
        err_body = err.read().decode("utf-8")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = err_body
        return {
            "status_code": err.code,
            "headers": {k.lower(): v for k, v in err.headers.items()},
            "data": parsed,
        }


def run_tests():
    print("=" * 60)
    print("STARTING AUTOQ PHASE 3/4 ENDPOINT VERIFICATION SUITE")
    print("=" * 60)

    # 1. Health Check (Legacy Endpoint)
    res = send_request("/api/health")
    assert res["status_code"] == 200, f"Expected 200, got {res['status_code']}"
    assert res["data"]["status"] == "healthy"
    assert res["data"]["application"] == "AutoQ"
    print("✓ TEST 1: GET /api/health returned 200 OK (Backward Compatible)")

    # 2. Health Check (API v1 Endpoint)
    res = send_request("/api/v1/health")
    assert res["status_code"] == 200, f"Expected 200, got {res['status_code']}"
    assert res["data"]["status"] == "healthy"
    assert "database_connected" in res["data"]
    print("✓ TEST 2: GET /api/v1/health returned 200 OK")

    # 3. OpenAPI / Swagger Documentation
    res = send_request("/openapi.json")
    assert res["status_code"] == 200
    assert res["data"]["info"]["title"] == "AutoQ – Automotive Quality Intelligence API"
    assert res["data"]["info"]["version"] == "1.0.0"
    print("✓ TEST 3: GET /openapi.json returned 200 OK with correct Title & Version")

    # 4. Predictions: Model Not Trained Handling (Valid Input)
    prediction_payload = {
        "component_id": "CMP-TRB-809",
        "component_category": "Powertrain",
        "manufacturing_temperature": 785.0,
        "pressure": 164.0,
        "production_batch": "BATCH-2026-B1",
    }
    res = send_request("/api/v1/predictions", method="POST", data=prediction_payload)
    assert res["status_code"] == 200, f"Expected 200, got {res['status_code']}"
    assert res["data"]["model_status"] == "MODEL_NOT_TRAINED"
    assert res["data"]["predicted_status"] is None
    assert res["data"]["defect_probability"] is None
    assert "awaiting model training" in res["data"]["message"].lower()
    print("✓ TEST 4: POST /api/v1/predictions returned 200 with MODEL_NOT_TRAINED status")

    # 5. Predictions: Input Validation Error (Invalid / Out of bounds Temperature)
    invalid_prediction = {
        "component_id": "CMP-TRB-809",
        "component_category": "Powertrain",
        "manufacturing_temperature": -50.0,
        "pressure": 164.0,
        "production_batch": "BATCH-2026-B1",
    }
    res = send_request("/api/v1/predictions", method="POST", data=invalid_prediction)
    assert res["status_code"] == 422, f"Expected 422, got {res['status_code']}"
    assert res["data"]["error_code"] == "REQUEST_VALIDATION_ERROR"
    print("✓ TEST 5: POST /api/v1/predictions with negative temperature correctly rejected with 422")

    # 6. Inspections: Valid Input to Persistence Endpoint (HTTP 201 Created in Phase 4)
    inspection_payload = {
        "component_id": "CMP-BRK-999",
        "component_name": "Ventilated Brake Caliper Mount",
        "component_category": "Braking System",
        "manufacturing_temperature": 742.0,
        "pressure": 145.0,
        "production_batch": "BATCH-2026-A2",
        "inspection_result": "Passed",
    }
    res = send_request("/api/v1/inspections", method="POST", data=inspection_payload)
    assert res["status_code"] == 201, f"Expected 201 Created, got {res['status_code']}"
    assert res["data"]["component_id"] == "CMP-BRK-999"
    created_id = res["data"]["id"]
    print(f"✓ TEST 6: POST /api/v1/inspections created record (id={created_id}) in SQLite")

    # 7. Inspections: Validation Failure (Invalid Inspection Result String)
    invalid_inspection = {
        "component_id": "CMP-BRK-999",
        "component_name": "Ventilated Brake Caliper Mount",
        "component_category": "Braking System",
        "manufacturing_temperature": 742.0,
        "pressure": 145.0,
        "production_batch": "BATCH-2026-A2",
        "inspection_result": "UnknownStatus",
    }
    res = send_request("/api/v1/inspections", method="POST", data=invalid_inspection)
    assert res["status_code"] == 422, f"Expected 422, got {res['status_code']}"
    print("✓ TEST 7: POST /api/v1/inspections with invalid status correctly rejected with 422")

    # 8. CSV Upload Validation (Valid CSV File)
    valid_csv_bytes = (
        "component_id,component_name,component_category,manufacturing_temperature,pressure,production_batch,inspection_result\r\n"
        "CMP-BRK-801,Brake Caliper,Braking System,742.0,145.0,BATCH-2026-A2,Passed\r\n"
        "CMP-TRB-802,Turbo Housing,Powertrain,785.0,164.0,BATCH-2026-B1,Defective\r\n"
    ).encode("utf-8")

    res = send_request(
        "/api/v1/inspections/upload",
        method="POST",
        files={"file": ("inspections.csv", valid_csv_bytes, "text/csv")},
    )
    assert res["status_code"] == 200, f"Expected 200, got {res['status_code']}: {res['data']}"
    assert res["data"]["status"] == "COMPLETED"
    assert res["data"]["imported_rows"] == 2
    print("✓ TEST 8: POST /api/v1/inspections/upload validated and imported CSV rows")

    # 9. CSV Upload Validation (Invalid CSV Missing Required Headers)
    invalid_csv_bytes = "part_number,temperature,pressure\r\nCMP-001,700,120\r\n".encode("utf-8")
    res = send_request(
        "/api/v1/inspections/upload",
        method="POST",
        files={"file": ("invalid.csv", invalid_csv_bytes, "text/csv")},
    )
    assert res["status_code"] == 400, f"Expected 400, got {res['status_code']}"
    assert res["data"]["error_code"] == "INVALID_CSV_FILE"
    assert "missing required columns" in res["data"]["detail"].lower()
    print("✓ TEST 9: POST /api/v1/inspections/upload correctly rejected invalid CSV schema with 400")

    # 10. Reports: Generation Request (HTTP 202 Accepted)
    report_req = {
        "report_type": "Defect Analysis",
        "batch": "BATCH-2026-A2",
        "date_range": "Last 14 Days",
        "format": "PDF",
    }
    res = send_request("/api/v1/reports/generate", method="POST", data=report_req)
    assert res["status_code"] == 202, f"Expected 202, got {res['status_code']}"
    assert res["data"]["report_status"] == "PENDING_PHASE_5"
    print("✓ TEST 10: POST /api/v1/reports/generate returned 202 Accepted with metadata")

    # 11. Analytics: Database-Backed Overview (HTTP 200 in Phase 4)
    res = send_request("/api/v1/analytics/overview")
    assert res["status_code"] == 200, f"Expected 200, got {res['status_code']}"
    assert res["data"]["total_inspections"] >= 1
    assert "defect_rate" in res["data"]
    print(f"✓ TEST 11: GET /api/v1/analytics/overview computed metrics from SQLite: total={res['data']['total_inspections']}")

    # 12. CORS Preflight Check
    cors_headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    res = send_request("/api/v1/predictions", method="OPTIONS", headers=cors_headers)
    assert res["status_code"] == 200, f"Expected 200, got {res['status_code']}"
    assert res["headers"].get("access-control-allow-origin") == "http://localhost:5173"
    print("✓ TEST 12: OPTIONS CORS Preflight verified for http://localhost:5173")

    print("=" * 60)
    print("ALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(2)

    try:
        run_tests()
    finally:
        server.should_exit = True
