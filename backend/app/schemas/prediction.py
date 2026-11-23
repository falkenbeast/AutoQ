from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict


class PredictionRequest(BaseModel):
    """Input parameters for automotive component defect evaluation."""

    component_id: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Target automotive component ID to predict (e.g. CMP-TRB-809)",
        examples=["CMP-TRB-809"],
    )
    component_category: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Automotive subsystem category",
        examples=["Powertrain"],
    )
    component_name: Optional[str] = Field(
        default=None,
        description="Optional component name",
    )
    manufacturing_temperature: Optional[float] = Field(
        default=742.5,
        gt=0.0,
        lt=2500.0,
        description="Measured manufacturing temperature in °C",
        examples=[785.0],
    )
    pressure: Optional[float] = Field(
        default=145.0,
        gt=0.0,
        lt=1000.0,
        description="Measured injection pressure in bar",
        examples=[164.0],
    )
    air_temperature: Optional[float] = Field(
        default=None,
        description="Ambient air temperature in K",
    )
    process_temperature: Optional[float] = Field(
        default=None,
        description="Process machining temperature in K",
    )
    rotational_speed: Optional[float] = Field(
        default=None,
        description="Rotational tool speed in RPM",
    )
    torque: Optional[float] = Field(
        default=None,
        description="Spindle torque in Nm",
    )
    tool_wear: Optional[float] = Field(
        default=None,
        description="Cumulative tool wear time in minutes",
    )
    product_type: Optional[str] = Field(
        default=None,
        description="Component product type variant: 'L', 'M', or 'H'",
    )
    production_batch: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Production batch identifier",
        examples=["BATCH-2026-B1"],
    )
    inspection_id: Optional[int] = Field(
        default=None,
        description="Optional associated inspection record ID",
    )
    # Optional extended physical features for ML pipeline
    stress_tolerance: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Tensile stress tolerance in MPa",
    )
    cycle_time: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Casting cycle duration in seconds",
    )
    vibration_index: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Machine vibration index in mm/s",
    )
    torque_resistance: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Torsional resistance in Nm",
    )
    decision_threshold: Optional[float] = Field(
        default=0.50,
        ge=0.10,
        le=0.90,
        description="Classification decision threshold (default 0.50, recommended high-sensitivity 0.35)",
        examples=[0.35],
    )

    @field_validator("component_id", "production_batch", mode="before")
    @classmethod
    def format_codes(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().upper()
        return v


class ContributingFactor(BaseModel):
    factor_name: str
    impact_weight: float
    description: str


class PredictionResponse(BaseModel):
    """
    Response schema for defect prediction evaluation.
    If the ML model is not yet trained, model_status='MODEL_NOT_TRAINED'
    and prediction values remain None per AutoQ guidelines.
    """

    id: Optional[int] = None
    prediction_id: Optional[Union[str, int]] = Field(
        default=None,
        description="Unique evaluation transaction ID",
    )
    component_id: Optional[str] = None
    inspection_id: Optional[int] = None
    model_version: str = "1.0.0"
    model_status: str = Field(
        ...,
        description="Current status of the ML inference engine ('MODEL_NOT_TRAINED' or 'INFERENCE_COMPLETE')",
        examples=["MODEL_NOT_TRAINED"],
    )
    predicted_status: Optional[str] = Field(
        default=None,
        description="Outcome of prediction: 'Passed' or 'Defective' (None when model not trained)",
    )
    predicted_quality: Optional[str] = Field(
        default=None,
        description="Outcome of prediction alias: 'Passed' or 'Defective'",
    )
    predicted_defect_category: Optional[str] = Field(
        default=None,
        description="Secondary multi-class defect classification if defective",
        examples=["Heat Dissipation Failure"],
    )
    decision_threshold: Optional[float] = Field(
        default=0.50,
        description="Applied classification probability threshold",
        examples=[0.35],
    )
    defect_probability: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Calculated defect probability between 0.0 and 1.0 (None when model not trained)",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Model confidence level (None when model not trained)",
    )
    contributing_factors: Optional[Any] = Field(
        default=None,
        description="Key physical parameters influencing the prediction",
    )
    recommendation: Optional[str] = Field(
        default=None,
        description="Recommended quality assurance action",
    )
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    message: str = Field(
        default="Prediction evaluation record.",
        description="Operational context or architectural state explanation",
    )

    model_config = ConfigDict(from_attributes=True)


class PredictionListResponse(BaseModel):
    """List of logged prediction evaluations."""
    items: List[PredictionResponse]
    total: int
    page: int
    page_size: int
