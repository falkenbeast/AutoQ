from typing import List, Optional
from pydantic import BaseModel, Field


class AnalyticsOverviewResponse(BaseModel):
    """Manufacturing quality high-level KPIs."""

    total_inspections: int = Field(..., description="Total count of inspected components", examples=[1482])
    passed_components: int = Field(..., description="Count of passed components", examples=[1348])
    defective_components: int = Field(..., description="Count of flagged defective components", examples=[134])
    total_passed: Optional[int] = None
    total_defective: Optional[int] = None
    defect_rate: float = Field(..., description="Calculated percentage defect rate (%)", examples=[9.04])
    pass_rate: float = Field(..., description="Calculated first-pass yield percentage (%)", examples=[90.96])
    defect_rate_percentage: Optional[float] = None
    pass_rate_percentage: Optional[float] = None
    batches_evaluated: Optional[int] = 0
    highest_yield_batch: Optional[str] = None
    target_defect_rate: float = Field(default=10.0, description="Quality tolerance threshold (%)")
    status: str = Field(default="NOMINAL", description="Quality compliance status")
    message: Optional[str] = None


class InspectionTrendItem(BaseModel):
    """Daily or periodic inspection volume point."""

    date: str = Field(..., description="Date or period label", examples=["2026-11-18"])
    inspections: int = Field(..., description="Total inspections performed", examples=[128])
    passed: int = Field(..., description="Passed components count", examples=[118])
    defective: int = Field(..., description="Defective components count", examples=[10])
    defect_rate: float = Field(..., description="Defect rate percentage (%)", examples=[7.8])


class InspectionTrendsResponse(BaseModel):
    """Timeline data of inspection volumes and defect rates."""

    period: str = Field(default="Last 14 Days")
    trends: List[InspectionTrendItem]
    message: Optional[str] = None


class DefectDistributionItem(BaseModel):
    """Proportion and count of a specific defect category."""

    category: str = Field(..., description="Defect category name", examples=["Structural Porosity"])
    count: int = Field(..., description="Defect occurrences", examples=[48])
    percentage: float = Field(..., description="Percentage of total defects (%)", examples=[35.8])


class DefectDistributionResponse(BaseModel):
    """Defect category breakdown response."""

    total_defects: int = Field(..., description="Total count of recorded defects", examples=[134])
    distribution: List[DefectDistributionItem]
    categories: Optional[List[dict]] = None
    message: Optional[str] = None


class QualityPerformanceItem(BaseModel):
    """Quality pass/fail counts by component family."""

    category: str = Field(..., description="Component family", examples=["Brake Caliper"])
    passed: int = Field(..., description="Passed count", examples=[310])
    defective: int = Field(..., description="Defective count", examples=[28])
    pass_rate: float = Field(..., description="Pass percentage (%)", examples=[91.7])


class QualityPerformanceResponse(BaseModel):
    """Quality performance aggregated across automotive components."""

    performance: List[QualityPerformanceItem]
    message: Optional[str] = None

