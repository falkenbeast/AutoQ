from fastapi import APIRouter
from app.core.config import settings
from app.database.connection import check_db_connection

router = APIRouter()


@router.get(
    "/health",
    summary="System Health Check",
    response_description="Returns operational health and system metadata",
)
async def health_check():
    """
    Returns the operational status, application name, API version,
    database connectivity readiness, and ML model engine availability.
    """
    db_connected = check_db_connection()
    from app.ml.inference.predictor import predictor
    model_ready = predictor.is_model_available()
    meta = predictor.get_metadata()

    return {
        "status": "healthy",
        "application": "AutoQ",
        "version": settings.VERSION,
        "database_connected": db_connected,
        "environment": "development" if settings.DEBUG else "production",
        "ml_engine": {
            "model_available": model_ready,
            "model_name": meta.get("model_name", "Random Forest Classifier"),
            "model_version": meta.get("model_version", "1.0.0"),
            "default_threshold": 0.50,
            "recommended_threshold": 0.35,
            "training_dataset": meta.get("dataset", {}).get("name", "AI4I 2020 Manufacturing Quality Benchmark"),
            "test_roc_auc": meta.get("champion_test_metrics", {}).get("roc_auc", 0.9830),
        },
    }

