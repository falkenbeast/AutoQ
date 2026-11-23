from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    DefectDistributionResponse,
    InspectionTrendsResponse,
    QualityPerformanceResponse,
)
from app.services.analytics_service import analytics_service

router = APIRouter()


@router.get(
    "/overview",
    response_model=AnalyticsOverviewResponse,
    summary="Manufacturing Quality Overview KPIs",
    description="Calculates total inspections, passed, defective components, and overall defect rate from SQLite records.",
)
def get_overview(
    batch: Optional[str] = Query(None, description="Filter by production batch code"),
    date_range: Optional[str] = Query(None, description="Time period filter"),
    db: Session = Depends(get_db),
):
    return analytics_service.get_overview(db=db, batch=batch, date_range=date_range)


@router.get(
    "/inspection-trends",
    response_model=InspectionTrendsResponse,
    summary="Inspection Volume & Defect Rate Trends",
    description="Returns time-series daily inspection counts and defect rates calculated from SQLite.",
)
@router.get(
    "/trends",
    response_model=InspectionTrendsResponse,
    summary="Inspection Volume & Defect Rate Trends (Alias)",
    description="Alias endpoint for inspection-trends.",
)
def get_inspection_trends(
    days: int = Query(14, ge=1, le=90, description="Number of historical days to aggregate"),
    batch: Optional[str] = Query(None, description="Filter by production batch code"),
    db: Session = Depends(get_db),
):
    return analytics_service.get_inspection_trends(db=db, days=days, batch=batch)


@router.get(
    "/batches",
    summary="Batch Comparison Analytics",
    description="Aggregates pass/defect statistics grouped by manufacturing batch code from SQLite.",
)
@router.get(
    "/batch-comparison",
    summary="Batch Comparison Analytics (Alias)",
    description="Aggregates pass/defect statistics grouped by manufacturing batch code from SQLite.",
    include_in_schema=False,
)
def get_batch_comparison(db: Session = Depends(get_db)):
    return analytics_service.get_batch_comparison(db=db)


@router.get(
    "/model-insights",
    summary="ML Model Insights & Feature Importance",
    description="Returns feature importance, evaluation metrics, and decision boundaries from the trained model metadata.",
)
def get_model_insights():
    return analytics_service.get_model_insights()


@router.get(
    "/defect-distribution",
    response_model=DefectDistributionResponse,
    summary="Defect Category Distribution",
    description="Calculates defect counts and percentage distribution across failure categories from SQLite.",
)
def get_defect_distribution(
    batch: Optional[str] = Query(None, description="Filter by production batch code"),
    db: Session = Depends(get_db),
):
    return analytics_service.get_defect_distribution(db=db, batch=batch)


@router.get(
    "/quality-performance",
    response_model=QualityPerformanceResponse,
    summary="Quality Performance by Component Family",
    description="Aggregates passed vs. defective counts and pass rates grouped by automotive subsystem from SQLite.",
)
def get_quality_performance(
    batch: Optional[str] = Query(None, description="Filter by production batch code"),
    db: Session = Depends(get_db),
):
    return analytics_service.get_quality_performance(db=db, batch=batch)
