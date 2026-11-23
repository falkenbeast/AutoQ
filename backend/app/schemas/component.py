from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ComponentBase(BaseModel):
    component_id: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique automotive component code (e.g. CMP-BRK-401)",
        examples=["CMP-BRK-401"],
    )
    component_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Descriptive component name",
        examples=["Ventilated Brake Caliper Mount"],
    )
    component_category: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Automotive component subsystem category",
        examples=["Braking System"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional technical specifications or assembly notes",
    )

    @field_validator("component_id", mode="before")
    @classmethod
    def clean_component_id(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().upper()
        return v

    @field_validator("component_name", "component_category", mode="before")
    @classmethod
    def clean_text(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v


class ComponentCreate(ComponentBase):
    """Schema for registering a new automotive component."""
    pass


class ComponentUpdate(BaseModel):
    """Schema for updating an existing component."""
    component_name: Optional[str] = Field(None, min_length=2, max_length=150)
    component_category: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)


class ComponentResponse(ComponentBase):
    """Schema for component API response."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComponentListResponse(BaseModel):
    """Schema for paginated list of components."""
    items: List[ComponentResponse]
    total: int
    page: int
    page_size: int

