from fastapi import APIRouter
from app.api.routes import (
    analytics,
    components,
    health,
    inspections,
    predictions,
    reports,
)

api_router = APIRouter()

# Register sub-routers with clear tags
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(components.router, prefix="/components", tags=["Components"])
api_router.include_router(inspections.router, prefix="/inspections", tags=["Inspections"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
