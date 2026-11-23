from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ReportTypeEnum(str, Enum):
    DEFECT_ANALYSIS = "Defect Analysis"
    INSPECTION_SUMMARY = "Inspection Summary"
    QUALITY_PERFORMANCE = "Quality Performance"
    TOLERANCE_COMPLIANCE = "Tolerance Compliance"
    BATCH_AUDIT = "Batch Audit"


class ReportFormatEnum(str, Enum):
    PDF = "PDF"
    CSV = "CSV"


class ReportGenerateRequest(BaseModel):
    """Specification request for generating an audit report."""

    report_type: ReportTypeEnum = Field(
        ...,
        description="Type of quality report to compile",
        examples=["Defect Analysis"],
    )
    batch: Optional[str] = Field(
        default="ALL",
        description="Target manufacturing batch filter",
        examples=["BATCH-2026-A2"],
    )
    target_batch: Optional[str] = Field(
        default=None,
        description="Target manufacturing batch filter alias",
    )
    date_range: Optional[str] = Field(
        default="Last 14 Days",
        description="Time horizon for the report data aggregation",
        examples=["Last 14 Days"],
    )
    format: ReportFormatEnum = Field(
        default=ReportFormatEnum.PDF,
        description="Export format: PDF audit report or CSV raw table",
        examples=["PDF"],
    )
    generated_by: Optional[str] = Field(
        default="Lead Quality Engineer",
        description="User or subsystem generating the report",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional report purpose description",
    )

    @field_validator("format", mode="before")
    @classmethod
    def normalize_format(cls, v):
        if isinstance(v, str):
            return v.strip().upper()
        return v

    @field_validator("report_type", mode="before")
    @classmethod
    def normalize_type(cls, v):
        if isinstance(v, str):
            clean = v.strip().title()
            valid_types = {
                "Defect Analysis": ReportTypeEnum.DEFECT_ANALYSIS,
                "Inspection Summary": ReportTypeEnum.INSPECTION_SUMMARY,
                "Quality Performance": ReportTypeEnum.QUALITY_PERFORMANCE,
                "Tolerance Compliance": ReportTypeEnum.TOLERANCE_COMPLIANCE,
                "Batch Audit": ReportTypeEnum.BATCH_AUDIT,
            }
            if clean in valid_types:
                return valid_types[clean]
        return v


class DownloadInformation(BaseModel):
    """Details for retrieving or streaming a generated report artifact."""

    file_name: str
    content_type: str
    download_url: Optional[str] = None
    is_available: bool = Field(
        default=False,
        description="Whether the physical binary is rendered (Phase 5 target)",
    )
    scheduled_phase: str = "Phase 5"


class ReportResponse(BaseModel):
    """Metadata schema for a quality inspection report."""

    id: Optional[int] = None
    report_id: Optional[Union[str, int]] = Field(
        default=None,
        description="Unique report identifier",
        examples=["REP-2026-1101"],
    )
    title: Optional[str] = Field(
        default=None,
        description="Report title",
        examples=["Defect Analysis - Batch 2026-A2"],
    )
    report_name: Optional[str] = None
    report_type: str
    target_batch: Optional[str] = None
    generated_date: Optional[datetime] = None
    generated_at: Optional[datetime] = None
    generated_by: str = Field(default="Lead Quality Engineer")
    report_status: str = Field(
        default="COMPLETED",
        description="Report lifecycle state: 'COMPLETED', 'GENERATED', or 'FAILED'",
    )
    format: str = "PDF"
    file_path: Optional[str] = None
    file_size: Optional[str] = None
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None
    download_information: Optional[DownloadInformation] = None
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReportListResponse(BaseModel):
    """Schema for listing archived reports."""
    reports: List[ReportResponse]
    total: int
    page: int
    page_size: int
