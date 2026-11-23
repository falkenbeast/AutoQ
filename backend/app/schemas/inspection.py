from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict


class InspectionResultEnum(str, Enum):
    PASSED = "Passed"
    DEFECTIVE = "Defective"


class InspectionBase(BaseModel):
    component_id: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique automotive component identifier (e.g. CMP-BRK-401)",
        examples=["CMP-BRK-401"],
    )
    component_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Descriptive automotive component name",
        examples=["Ventilated Brake Caliper Mount"],
    )
    component_category: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Automotive subsystem category (e.g. Braking System, Powertrain, Engine)",
        examples=["Braking System"],
    )
    manufacturing_temperature: float = Field(
        ...,
        gt=0.0,
        lt=2500.0,
        description="Measured manufacturing / casting temperature in degrees Celsius (°C)",
        examples=[742.5],
    )
    pressure: float = Field(
        ...,
        gt=0.0,
        lt=1000.0,
        description="Measured die injection / hydraulic pressure in bar",
        examples=[145.0],
    )
    production_batch: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Manufacturing production batch code (e.g. BATCH-2026-A2)",
        examples=["BATCH-2026-A2"],
    )
    inspection_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of the physical quality inspection",
    )
    inspection_result: InspectionResultEnum = Field(
        ...,
        description="Quality inspection result outcome. Strictly 'Passed' or 'Defective'.",
        examples=["Passed"],
    )
    defect_category: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Specific defect classification if defective (e.g. Structural Porosity, Surface Micro-cracks)",
        examples=["Structural Porosity"],
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Inspector observations and optical/ultrasonic scan findings",
        examples=["Dimensions within ±0.02mm tolerance limit."],
    )

    @field_validator("component_id", "production_batch", mode="before")
    @classmethod
    def strip_and_uppercase(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().upper()
        return v

    @field_validator("component_name", "component_category", mode="before")
    @classmethod
    def strip_text(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("inspection_result", mode="before")
    @classmethod
    def normalize_result(cls, v: str) -> str:
        if isinstance(v, str):
            v_norm = v.strip().capitalize()
            if v_norm in ["Passed", "Pass"]:
                return InspectionResultEnum.PASSED.value
            elif v_norm in ["Defective", "Fail", "Defect"]:
                return InspectionResultEnum.DEFECTIVE.value
        return v


class InspectionCreate(InspectionBase):
    """Schema for creating a new component inspection record."""
    pass


class InspectionUpdate(BaseModel):
    """Schema for updating an existing inspection record (all fields optional)."""
    component_name: Optional[str] = Field(None, min_length=2, max_length=150)
    component_category: Optional[str] = Field(None, min_length=2, max_length=100)
    manufacturing_temperature: Optional[float] = Field(None, gt=0.0, lt=2500.0)
    pressure: Optional[float] = Field(None, gt=0.0, lt=1000.0)
    production_batch: Optional[str] = Field(None, min_length=2, max_length=50)
    inspection_result: Optional[InspectionResultEnum] = None
    defect_category: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)


class InspectionResponse(InspectionBase):
    """Schema for inspection record response."""
    id: Union[int, str] = Field(..., description="Unique record ID", examples=[1, "AQ-2026-0941"])
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


class InspectionListResponse(BaseModel):
    """Schema for paginated inspection list query response."""
    items: List[InspectionResponse]
    total: int
    page: int
    page_size: int


class CSVUploadResponse(BaseModel):
    """Schema for batch CSV upload validation & ingestion response."""
    filename: str
    file_size_bytes: int
    total_rows: int
    valid_rows: int
    imported_rows: int = 0
    rejected_rows: int = 0
    errors: List[str] = []
    preview: List[dict] = []
    status: str
    message: str
