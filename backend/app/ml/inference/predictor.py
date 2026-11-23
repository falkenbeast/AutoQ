"""
AutoQ - Real-time ML Defect Prediction and Inference Engine
Provides thread-safe model loading, schema validation, probability calibration extraction,
and secondary multi-class root-cause defect attribution.
"""
import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import joblib
import numpy as np
import pandas as pd

from app.ml.inference.mapping import FeatureMappingLayer


class DefectPredictor:
    """
    Production inference engine loading serialized champion Random Forest pipeline
    and secondary multi-class defect attribution models.
    """

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def _resolve_models_dir(cls, user_dir: Optional[str] = None) -> str:
        """Robustly locates the trained_models directory regardless of working directory."""
        if user_dir and os.path.isdir(user_dir):
            return os.path.abspath(user_dir)

        try:
            from app.core.config import settings
            if settings.MODEL_STORAGE_PATH and os.path.isdir(settings.MODEL_STORAGE_PATH):
                return os.path.abspath(str(settings.MODEL_STORAGE_PATH))
        except Exception:
            pass

        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        # Current file is in backend/app/ml/inference -> 3 levels up is backend
        candidate_backend = os.path.abspath(os.path.join(current_file_dir, "..", "..", "..", "trained_models"))
        if os.path.isdir(candidate_backend):
            return candidate_backend

        candidate_rel = os.path.abspath(os.path.join("backend", "trained_models"))
        if os.path.isdir(candidate_rel):
            return candidate_rel

        candidate_local = os.path.abspath("trained_models")
        if os.path.isdir(candidate_local):
            return candidate_local

        return candidate_backend

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DefectPredictor, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, models_dir: Optional[str] = None):
        if self._initialized:
            return

        self.models_dir = self._resolve_models_dir(models_dir)
        self.champion_path = os.path.join(self.models_dir, "defect_classifier_pipeline.joblib")
        self.multiclass_path = os.path.join(self.models_dir, "multiclass_defect_classifier.joblib")
        self.metadata_path = os.path.join(self.models_dir, "model_metadata.json")

        self.mapping_layer = FeatureMappingLayer()
        self.champion_pipeline = None
        self.multiclass_pipeline = None
        self.metadata = {}

        self._load_artifacts()
        self._initialized = True

    def _load_artifacts(self):
        """Loads serialized models and metadata using guaranteed absolute paths."""
        import logging
        log = logging.getLogger("autoq.ml.inference")

        self.models_dir = self._resolve_models_dir(self.models_dir)
        self.champion_path = os.path.join(self.models_dir, "defect_classifier_pipeline.joblib")
        self.multiclass_path = os.path.join(self.models_dir, "multiclass_defect_classifier.joblib")
        self.metadata_path = os.path.join(self.models_dir, "model_metadata.json")

        champion_file = self.champion_path
        if not os.path.exists(champion_file):
            alt_champ = os.path.join(self.models_dir, "defect_classifier.joblib")
            if os.path.exists(alt_champ):
                champion_file = alt_champ

        if os.path.exists(champion_file):
            try:
                self.champion_pipeline = joblib.load(champion_file)
                clf = getattr(self.champion_pipeline, "named_steps", {}).get("classifier", self.champion_pipeline)
                if hasattr(clf, "n_jobs"):
                    clf.n_jobs = 1
                log.info(f"[DefectPredictor] Loaded champion binary pipeline from: {champion_file}")
            except Exception as e:
                log.error(f"[DefectPredictor] Failed to load champion model from {champion_file}: {e}")

        if os.path.exists(self.multiclass_path):
            try:
                self.multiclass_pipeline = joblib.load(self.multiclass_path)
                clf = getattr(self.multiclass_pipeline, "named_steps", {}).get("classifier", self.multiclass_pipeline)
                if hasattr(clf, "n_jobs"):
                    clf.n_jobs = 1
                log.info(f"[DefectPredictor] Loaded multiclass attribution pipeline from: {self.multiclass_path}")
            except Exception as e:
                log.error(f"[DefectPredictor] Failed to load multiclass model from {self.multiclass_path}: {e}")

        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                log.info(f"[DefectPredictor] Loaded model metadata from: {self.metadata_path}")
            except Exception as e:
                log.error(f"[DefectPredictor] Failed to load metadata from {self.metadata_path}: {e}")

    def is_model_available(self) -> bool:
        """Returns True if the champion pipeline is loaded and ready for inference."""
        if self.champion_pipeline is None:
            self._load_artifacts()
        return self.champion_pipeline is not None

    def get_metadata(self) -> Dict[str, Any]:
        """Returns training metadata and model specifications."""
        return self.metadata

    def predict(
        self,
        raw_input: Dict[str, Any],
        decision_threshold: float = 0.50,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end inference on a single component inspection payload:
        1. Validates and maps input parameters to feature vector.
        2. Computes defect probability via predict_proba.
        3. Evaluates binary quality status (Passed vs. Defective).
        4. Queries secondary model for root-cause failure mode attribution if defective.
        5. Analyzes key contributing factors and produces actionable QA recommendation.
        """
        if not self.is_model_available():
            raise RuntimeError(
                "AutoQ ML Inference Engine is uninitialized. "
                "Ensure Phase 6 model training has been completed."
            )

        # 1. Feature Mapping & Strict Validation
        feature_df = self.mapping_layer.map_request_to_features(raw_input, strict=True)

        # 2. Probability Estimation
        probabilities = self.champion_pipeline.predict_proba(feature_df)[0]
        # Class 0: Passed, Class 1: Defective
        defect_prob = float(probabilities[1])
        pass_prob = float(probabilities[0])

        # 3. Decision Boundary
        is_defective = defect_prob >= decision_threshold
        predicted_status = "Defective" if is_defective else "Passed"

        # Confidence: Distance from uncertainty threshold (0.50) scaled to [0.5, 1.0]
        confidence = float(max(defect_prob, pass_prob))

        # 4. Secondary Multiclass Attribution
        predicted_defect_category = "No Defect"
        if is_defective and self.multiclass_pipeline is not None:
            try:
                multi_pred = self.multiclass_pipeline.predict(feature_df)[0]
                if multi_pred != "No Defect":
                    predicted_defect_category = str(multi_pred)
                else:
                    predicted_defect_category = "General Manufacturing Non-Conformance"
            except Exception:
                predicted_defect_category = "General Manufacturing Non-Conformance"

        # 5. Contributing Factor Analysis
        contributing_factors = self._analyze_contributing_factors(feature_df.iloc[0], defect_prob)

        # 6. Actionable Recommendation
        recommendation = self._generate_recommendation(
            predicted_status=predicted_status,
            defect_prob=defect_prob,
            defect_category=predicted_defect_category,
            contributing_factors=contributing_factors,
        )

        return {
            "model_version": self.metadata.get("model_version", "1.0.0"),
            "model_name": self.metadata.get("model_name", "Random Forest Classifier"),
            "model_status": "INFERENCE_COMPLETE",
            "predicted_status": predicted_status,
            "defect_probability": round(defect_prob, 4),
            "confidence": round(confidence, 4),
            "predicted_defect_category": predicted_defect_category,
            "decision_threshold_applied": decision_threshold,
            "contributing_factors": contributing_factors,
            "recommendation": recommendation,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _analyze_contributing_factors(
        self,
        features: pd.Series,
        defect_prob: float,
    ) -> List[Dict[str, Any]]:
        """Identifies key physical parameters elevating defect risk."""
        factors = []

        # Check Spindle Power (Watts)
        pwr = features.get("mechanical_power", 0.0)
        if pwr < 3500.0 or pwr > 9000.0:
            impact = 0.35 if pwr > 9000.0 else 0.28
            factors.append({
                "factor_name": "Mechanical Spindle Power",
                "impact_weight": round(impact, 2),
                "description": f"Spindle mechanical power ({pwr:.0f} W) outside stable operating regime [3500W, 9000W].",
            })

        # Check Thermal Gradient (Delta T)
        delta_t = features.get("temp_difference", 0.0)
        speed = features.get("rotational_speed", 1500.0)
        if delta_t < 8.6 and speed < 1380.0:
            factors.append({
                "factor_name": "Thermal Dissipation Gradient",
                "impact_weight": 0.32,
                "description": f"Insufficient heat dissipation (ΔT = {delta_t:.1f} K) at low spindle speed ({speed:.0f} rpm).",
            })

        # Check Overstrain Fatigue
        overstrain = features.get("overstrain_index", 0.0)
        if overstrain > 11000.0:
            factors.append({
                "factor_name": "Overstrain Stress Coupling",
                "impact_weight": 0.30,
                "description": f"Tool wear-torque interaction ({overstrain:.0f} min·Nm) exceeds critical material fracture limit.",
            })

        # Check Progressive Tool Wear
        tool_wear = features.get("tool_wear", 0.0)
        if tool_wear >= 200.0:
            factors.append({
                "factor_name": "Cumulative Tool Wear",
                "impact_weight": 0.22,
                "description": f"Tool cutting insert duration ({tool_wear:.0f} min) exceeds recommended replacement life.",
            })

        if not factors and defect_prob > 0.30:
            factors.append({
                "factor_name": "Coupled Process Telemetry",
                "impact_weight": 0.15,
                "description": "Marginal parameter variations combined across torque and temperature readings.",
            })

        return factors

    def _generate_recommendation(
        self,
        predicted_status: str,
        defect_prob: float,
        defect_category: str,
        contributing_factors: List[Dict[str, Any]],
    ) -> str:
        """Formulates actionable shop-floor quality engineering directive."""
        if predicted_status == "Passed":
            if defect_prob < 0.15:
                return "Component conforms to specification. Cleared for downstream assembly."
            else:
                return "Component passed within tolerance. Monitor machining cell telemetry for minor drift."

        # Defective
        if "Heat Dissipation" in defect_category:
            return "REJECT: High thermal dissipation risk. Inspect machining coolant pressure and tool nozzle alignment."
        elif "Power" in defect_category:
            return "REJECT: Drive power anomaly. Calibrate milling spindle motor torque and verify workpiece feed rate."
        elif "Overstrain" in defect_category:
            return "REJECT: Critical mechanical overstrain detected. Replace cutting tool insert and check alloy hardness."
        elif "Tool Wear" in defect_category:
            return "REJECT: Tool wear limit exceeded. Halt machining cycle and install fresh cutting tooling immediately."
        else:
            return f"REJECT: Component defect probability ({defect_prob*100:.1f}%) exceeds safety threshold. Route part to QA quarantine."


# Global singleton instance
predictor = DefectPredictor()
