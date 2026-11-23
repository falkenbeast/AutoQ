from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse

HTTP_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)


class AutoQException(Exception):
    """Base exception for all AutoQ application errors."""

    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_SERVER_ERROR",
        extra: Optional[dict] = None,
    ):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        self.extra = extra or {}


class EntityNotFoundException(AutoQException):
    """Raised when a requested resource is not found."""

    def __init__(self, entity_name: str, entity_id: Any):
        super().__init__(
            detail=f"{entity_name} with identifier '{entity_id}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
        )


class ModelNotTrainedException(AutoQException):
    """
    Raised when an ML inference request is made but no trained model artifact exists.
    Adheres to the AutoQ rule: do not return fabricated prediction values.
    """

    def __init__(self, detail: Optional[str] = None):
        super().__init__(
            detail=detail or (
                "The machine learning defect prediction model is not yet trained or available. "
                "Trained models are scheduled for deployment in Phase 4."
            ),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="MODEL_NOT_TRAINED",
            extra={"model_status": "MODEL_NOT_TRAINED", "pipeline": "RandomForestClassifier"},
        )


class FeatureNotImplementedException(AutoQException):
    """
    Raised for database-dependent or future phase operations that are intentionally
    deferred per project architecture guidelines (e.g. database persistence in Phase 4).
    """

    def __init__(self, feature_name: str, target_phase: str = "Phase 4"):
        super().__init__(
            detail=(
                f"The operation '{feature_name}' is scheduled for implementation in {target_phase}. "
                f"Underlying database persistence or pipeline will be activated in {target_phase}."
            ),
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            error_code="FEATURE_NOT_IMPLEMENTED",
            extra={"target_phase": target_phase, "feature": feature_name},
        )


class InvalidCSVException(AutoQException):
    """Raised when an uploaded inspection CSV file has an invalid schema or corrupted contents."""

    def __init__(self, detail: str, errors: Optional[list] = None):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_CSV_FILE",
            extra={"validation_errors": errors or []},
        )


class ValidationException(AutoQException):
    """Raised when business validation rules fail."""

    def __init__(self, detail: str, field: Optional[str] = None):
        super().__init__(
            detail=detail,
            status_code=HTTP_422,
            error_code="BUSINESS_VALIDATION_ERROR",
            extra={"field": field} if field else {},
        )


async def autoq_exception_handler(request: Request, exc: AutoQException) -> JSONResponse:
    """Centralized exception handler for all AutoQException instances."""
    content = {
        "status": "error",
        "error_code": exc.error_code,
        "detail": exc.detail,
        "path": request.url.path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if exc.extra:
        content["extra"] = exc.extra

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
    )
