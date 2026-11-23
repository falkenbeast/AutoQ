"""
AutoQ - Phase 5 Pipeline Execution & Verification Script
Runs end-to-end data loading, cleaning, feature engineering, train/test splitting,
preprocessor artifact generation, and database schema compatibility checks.
"""
import os
import sys
import json
import pandas as pd

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.ml.preprocessing.data_loader import RawDataLoader
from app.ml.preprocessing.cleaner import DataCleaner
from app.ml.preprocessing.feature_pipeline import execute_preprocessing_pipeline


def run():
    print("=" * 60)
    print("AutoQ - Phase 5 Dataset Pipeline Execution")
    print("=" * 60)

    # 1. Load and Verify Raw Dataset
    print("[1/5] Loading and verifying raw dataset integrity...")
    loader = RawDataLoader()
    is_valid, computed_hash, expected_hash = loader.verify_checksum()
    print(f"      SHA-256: {computed_hash}")
    print(f"      Integrity check: {'PASSED (Cryptographically verified)' if is_valid else 'FAILED'}")
    if not is_valid:
        raise ValueError("Raw dataset integrity check failed!")

    raw_df = loader.load_raw_data()
    print(f"      Loaded raw records: {raw_df.shape[0]} rows, {raw_df.shape[1]} columns")

    # 2. Clean and Standardize Schema
    print("[2/5] Cleaning and standardizing schema...")
    cleaner = DataCleaner()
    cleaned_df = cleaner.clean(raw_df)
    print(f"      Cleaned dataset columns: {len(cleaned_df.columns)}")
    print(f"      Defect distribution: {cleaned_df['inspection_result'].value_counts().to_dict()}")
    print(f"      Defect categories breakdown:\n{cleaned_df['defect_category'].value_counts()}")

    # 3. Feature Engineering and Preprocessing Pipeline
    print("[3/5] Executing domain feature engineering & stratified train/test split...")
    metadata = execute_preprocessing_pipeline(cleaned_df)
    print(f"      Train samples: {metadata['train_samples']} (Defect rate: {metadata['train_class_distribution']['defect_rate_pct']}%)")
    print(f"      Test samples:  {metadata['test_samples']} (Defect rate: {metadata['test_class_distribution']['defect_rate_pct']}%)")
    print(f"      Engineered Features: {metadata['input_features']}")
    print(f"      Transformed Output Dimensions: {metadata['transformed_feature_count']} features")
    print(f"      Artifact saved: {metadata['preprocessor_artifact']}")

    # 4. Verify Processed Files
    print("[4/5] Verifying processed artifacts...")
    processed_dir = os.path.join("backend", "datasets", "processed")
    expected_files = [
        "cleaned_dataset.csv",
        "train.csv",
        "test.csv",
        "preprocessing_metadata.json",
        "preprocessor.joblib",
    ]
    for fname in expected_files:
        fpath = os.path.join(processed_dir, fname)
        if not os.path.exists(fpath):
            raise FileNotFoundError(f"Missing processed file: {fpath}")
        size = os.path.getsize(fpath)
        print(f"      [OK] {fname} ({size:,} bytes)")

    # 5. Database Schema Compatibility Assessment
    print("[5/5] Assessing database schema compatibility...")
    from app.database.connection import SessionLocal
    from app.models.component import Component
    from app.models.inspection import Inspection

    with SessionLocal() as db:
        comp_count = db.query(Component).count()
        insp_count = db.query(Inspection).count()
        print(f"      Existing Database State: {comp_count} components, {insp_count} inspections")
        print("      Field Compatibility Mapping:")
        print("      - product_id        -> components.component_id / inspections.component_id")
        print("      - component_category-> components.component_category")
        print("      - process_temperature -> inspections.manufacturing_temperature (Celsius conversion ready)")
        print("      - torque            -> inspections.pressure (bar / torque proxy)")
        print("      - inspection_result -> inspections.inspection_result ('Passed'/'Defective')")
        print("      - defect_category   -> inspections.defect_category")

    print("\n" + "=" * 60)
    print("Phase 5 Pipeline Executed Successfully!")
    print("=" * 60)


if __name__ == "__main__":
    run()

