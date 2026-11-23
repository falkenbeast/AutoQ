"""
AutoQ - Data Loader Module
Responsible for loading the raw manufacturing dataset, validating file integrity,
and ensuring immutable read operations.
"""
import hashlib
import json
import os
from typing import Optional, Tuple
import pandas as pd


class RawDataLoader:
    """
    Safely loads and verifies raw dataset integrity against the dataset manifest.
    Guarantees raw files are read-only and never modified.
    """

    DEFAULT_RAW_PATH = os.path.join("backend", "datasets", "raw", "ai4i2020.csv")
    DEFAULT_MANIFEST_PATH = os.path.join("backend", "datasets", "raw", "dataset_manifest.json")

    def __init__(
        self,
        raw_path: Optional[str] = None,
        manifest_path: Optional[str] = None,
    ):
        self.raw_path = raw_path or self.DEFAULT_RAW_PATH
        self.manifest_path = manifest_path or self.DEFAULT_MANIFEST_PATH

    def verify_checksum(self) -> Tuple[bool, str, Optional[str]]:
        """
        Computes SHA-256 of the local raw dataset and compares it against manifest.
        Returns: (is_valid, computed_hash, expected_hash)
        """
        if not os.path.exists(self.raw_path):
            raise FileNotFoundError(f"Raw dataset not found at {self.raw_path}")

        with open(self.raw_path, "rb") as f:
            data = f.read()
        computed_hash = hashlib.sha256(data).hexdigest()

        expected_hash = None
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                expected_hash = manifest.get("sha256_checksum")

        is_valid = (expected_hash is None) or (computed_hash == expected_hash)
        return is_valid, computed_hash, expected_hash

    def load_raw_data(self, verify_hash: bool = True) -> pd.DataFrame:
        """
        Loads the raw CSV dataset into a pandas DataFrame after integrity validation.
        """
        if verify_hash:
            is_valid, computed, expected = self.verify_checksum()
            if not is_valid:
                raise ValueError(
                    f"Dataset checksum mismatch! Expected {expected}, got {computed}."
                )

        df = pd.read_csv(self.raw_path)
        return df


def load_raw_dataset(raw_path: Optional[str] = None) -> pd.DataFrame:
    """Convenience helper to load raw dataset."""
    loader = RawDataLoader(raw_path=raw_path)
    return loader.load_raw_data()

