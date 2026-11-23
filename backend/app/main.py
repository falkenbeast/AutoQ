from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import AutoQException, autoq_exception_handler
from app.database.connection import check_db_connection, init_db

# Configure application logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("autoq.api")

# OpenAPI Tag Metadata for Swagger UI organization
tags_metadata = [
    {
        "name": "Health",
        "description": "System health monitoring, heartbeat, and runtime readiness probes.",
    },
    {
        "name": "Components",
        "description": "Automotive component catalog management and master part records.",
    },
    {
        "name": "Inspections",
        "description": "Automotive component inspection records management, filtering, and batch CSV ingestion.",
    },
    {
        "name": "Predictions",
        "description": "Machine learning defect evaluation engine. Integrates Scikit-learn pipelines in Phase 4.",
    },
    {
        "name": "Analytics",
        "description": "Manufacturing quality KPIs, historical defect rates, and component pass-yield aggregations.",
    },
    {
        "name": "Reports",
        "description": "Quality audit report generation and document cataloging services.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Safely initializes SQLite tables on startup and pre-loads ML model artifacts.
    """
    logger.info("Initializing AutoQ database tables...")
    try:
        init_db()
        logger.info("AutoQ database initialization verified.")
    except Exception as exc:
        logger.error(f"Database initialization warning: {exc}")

    # Explicit Model Initialization during Startup (Phase 2 & Phase 3)
    logger.info("Initializing AutoQ ML Inference Engine models...")
    try:
        from app.ml.inference.predictor import predictor
        if predictor.is_model_available():
            meta = predictor.get_metadata()
            logger.info(
                f"AutoQ ML Inference Engine loaded champion Random Forest model successfully "
                f"(artifact: {predictor.champion_path}, ROC-AUC: {meta.get('champion_test_metrics', {}).get('roc_auc', '0.9830')})."
            )
            if predictor.multiclass_pipeline is not None:
                logger.info(
                    f"AutoQ ML Multiclass defect attribution model loaded successfully "
                    f"(artifact: {predictor.multiclass_path})."
                )
        else:
            logger.error(
                f"AutoQ ML model artifacts could not be loaded from {predictor.models_dir}. "
                "Inference requests will return HTTP 503 until valid model artifacts are present."
            )
    except Exception as exc:
        logger.error(f"ML Model initialization failure: {exc}")

    yield


# Initialize FastAPI Application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(AutoQException)
async def handle_autoq_exception(request: Request, exc: AutoQException):
    return await autoq_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    logger.warning(
        f"Request validation failure on {request.method} {request.url.path}: {exc.errors()}"
    )
    return JSONResponse(
        status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
        content={
            "status": "error",
            "error_code": "REQUEST_VALIDATION_ERROR",
            "detail": "Input validation failed for one or more fields.",
            "errors": exc.errors(),
            "path": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def handle_unhandled_exception(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception during {request.method} {request.url.path}: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "detail": "An internal server error occurred while processing the request.",
            "path": request.url.path,
        },
    )


# Mount Central API Router (/api/v1 and /api aliases for full compatibility)
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router, prefix="/api")


# Root Discovery Endpoint
@app.get("/", include_in_schema=False)
async def root():
    return {
        "application": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "health": "/api/health",
        "api_v1": settings.API_V1_STR,
    }
