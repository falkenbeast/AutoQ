import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import EntityNotFoundException, ModelNotTrainedException, ValidationException
from app.models.prediction import Prediction
from app.schemas.prediction import (
    PredictionListResponse,
    PredictionRequest,
    PredictionResponse,
)

logger = logging.getLogger("autoq.services.prediction")


class PredictionService:
    """
    Service responsible for machine learning defect predictions and database history.
    Enforces strict architectural rules:
    - Never fabricates fake predictions or stores mock ML results into SQLite.
    - If a trained model is not present, returns an explicit MODEL_NOT_TRAINED response.
    - Persists actual inference records when a genuine model is loaded.
    """

    def __init__(self):
        self.model_dir = Path(settings.MODEL_STORAGE_PATH)
        self.model_path = self.model_dir / "defect_classifier.joblib"

    def is_model_available(self) -> bool:
        """Checks if a serialized machine learning model exists on disk and is ready."""
        from app.ml.inference.predictor import predictor
        if predictor.is_model_available():
            return True
        candidate1 = self.model_dir / "defect_classifier_pipeline.joblib"
        candidate2 = self.model_dir / "defect_classifier.joblib"
        return (candidate1.is_file() and os.path.getsize(candidate1) > 0) or (
            candidate2.is_file() and os.path.getsize(candidate2) > 0
        )

    def predict_defect(
        self,
        db: Session,
        payload: PredictionRequest,
    ) -> PredictionResponse:
        """
        Evaluates automotive component inspection parameters using genuine ML models.
        Raises ModelNotTrainedException (HTTP 503) if the model artifacts are absent or unavailable.
        """
        from datetime import datetime, timezone
        from app.ml.inference.predictor import predictor

        if not self.is_model_available():
            logger.error(
                f"Defect prediction requested for {payload.component_id}, but ML model artifacts are not available."
            )
            raise ModelNotTrainedException(
                "AutoQ Machine Learning defect prediction model is currently unavailable. "
                "Trained model artifacts could not be loaded from storage."
            )

        thresh = payload.decision_threshold if payload.decision_threshold is not None else 0.50
        try:
            inf_result = predictor.predict(payload.model_dump(), decision_threshold=thresh)
        except ValueError as ve:
            raise ValidationException(str(ve))
        except RuntimeError as re:
            raise ModelNotTrainedException(str(re))

        db_record = self.save_prediction(
            db=db,
            component_id=payload.component_id,
            inspection_id=payload.inspection_id,
            predicted_status=inf_result["predicted_status"],
            defect_probability=inf_result["defect_probability"],
            model_version=inf_result["model_version"],
            model_status="INFERENCE_COMPLETE",
            contributing_factors=inf_result["contributing_factors"],
            recommendation=inf_result["recommendation"],
            component_category=payload.component_category,
        )

        return PredictionResponse(
            id=db_record.id,
            prediction_id=db_record.id,
            component_id=payload.component_id,
            inspection_id=payload.inspection_id,
            model_version=inf_result["model_version"],
            model_status="INFERENCE_COMPLETE",
            predicted_status=inf_result["predicted_status"],
            predicted_quality=inf_result["predicted_status"],
            predicted_defect_category=inf_result.get("predicted_defect_category"),
            defect_probability=inf_result["defect_probability"],
            confidence=inf_result["confidence"],
            decision_threshold=thresh,
            contributing_factors=inf_result["contributing_factors"],
            recommendation=inf_result["recommendation"],
            evaluated_at=datetime.fromisoformat(inf_result["evaluated_at"]),
            message=f"Live Machine Learning defect prediction complete. Quality state evaluated as {inf_result['predicted_status']}.",
        )

    def save_prediction(
        self,
        db: Session,
        component_id: Optional[str],
        inspection_id: Optional[int],
        predicted_status: str,
        defect_probability: float,
        model_version: str = "1.0.0",
        model_status: str = "INFERENCE_COMPLETE",
        contributing_factors: Optional[Any] = None,
        recommendation: Optional[str] = None,
        component_category: Optional[str] = None,
    ) -> Prediction:
        """Persists genuine ML inference evaluations into SQLite."""
        if component_id:
            from app.services.component_service import component_service
            component_service.get_or_create_component(
                db=db,
                component_id=component_id,
                component_name=component_id,
                component_category=component_category or "Powertrain",
            )

        record = Prediction(
            component_id=component_id,
            inspection_id=inspection_id,
            predicted_status=predicted_status,
            defect_probability=defect_probability,
            model_version=model_version,
            model_status=model_status,
            contributing_factors=contributing_factors,
            recommendation=recommendation,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info(f"Persisted genuine ML prediction: id={record.id} for component={component_id}")
        return record

    def get_predictions(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        component_id: Optional[str] = None,
    ) -> Tuple[List[Prediction], int]:
        """Queries historical prediction records from SQLite."""
        query = db.query(Prediction)
        if component_id:
            query = query.filter(Prediction.component_id == component_id.strip().upper())

        total = query.count()
        items = query.order_by(Prediction.created_at.desc(), Prediction.id.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_prediction_by_id(
        self,
        db: Session,
        prediction_id: Union[int, str],
    ) -> Prediction:
        """Retrieves a single prediction evaluation record by ID."""
        try:
            int_id = int(str(prediction_id).replace("PRED-", "").strip())
        except ValueError:
            raise EntityNotFoundException("Prediction", prediction_id)

        pred = db.query(Prediction).filter(Prediction.id == int_id).first()
        if not pred:
            raise EntityNotFoundException("Prediction", prediction_id)
        return pred


prediction_service = PredictionService()
