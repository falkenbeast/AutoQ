from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.prediction import (
    PredictionListResponse,
    PredictionRequest,
    PredictionResponse,
)
from app.services.prediction_service import prediction_service

router = APIRouter()


@router.post(
    "",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Component Defect Probability",
    description=(
        "Evaluates manufacturing inspection parameters using the AutoQ machine learning engine. "
        "Returns an explicit MODEL_NOT_TRAINED status when the model artifact has not yet been trained."
    ),
)
def predict_defect(
    payload: PredictionRequest,
    db: Session = Depends(get_db),
):
    return prediction_service.predict_defect(db=db, payload=payload)


@router.get(
    "",
    response_model=PredictionListResponse,
    summary="List Prediction History",
    description="Retrieves a paginated list of historical ML prediction evaluations from SQLite.",
)
def list_predictions(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    component_id: Optional[str] = Query(None, description="Filter by component ID"),
    db: Session = Depends(get_db),
):
    items, total = prediction_service.get_predictions(
        db=db, skip=skip, limit=limit, component_id=component_id
    )
    return PredictionListResponse(
        items=items,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
    )


@router.get(
    "/{prediction_id}",
    response_model=PredictionResponse,
    summary="Get Prediction by ID",
    description="Retrieves evaluation details for a specific prediction transaction.",
)
def get_prediction(
    prediction_id: str,
    db: Session = Depends(get_db),
):
    return prediction_service.get_prediction_by_id(db=db, prediction_id=prediction_id)
