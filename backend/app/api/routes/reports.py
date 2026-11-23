from pathlib import Path
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.report import (
    ReportGenerateRequest,
    ReportListResponse,
    ReportResponse,
)
from app.services.report_service import report_service

router = APIRouter()


@router.get(
    "",
    response_model=ReportListResponse,
    summary="List Quality Reports",
    description="Retrieves a list of archived quality inspection audit report metadata from SQLite.",
)
def list_reports(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    db: Session = Depends(get_db),
):
    items, total = report_service.get_reports(db=db, skip=skip, limit=limit)
    formatted_items = []
    for r in items:
        file_size_bytes = 0
        if r.file_path:
            fp = Path(r.file_path)
            if fp.is_file():
                file_size_bytes = fp.stat().st_size
            else:
                alt = report_service.report_dir / fp.name
                if alt.is_file():
                    file_size_bytes = alt.stat().st_size

        size_formatted = f"{(file_size_bytes / 1024):.1f} KB" if file_size_bytes < 1024 * 1024 else f"{(file_size_bytes / (1024 * 1024)):.1f} MB"
        ext = "PDF" if (r.file_path and r.file_path.endswith(".pdf")) else "CSV"
        formatted_items.append(
            ReportResponse(
                id=r.id,
                report_id=f"REP-{r.id:04d}",
                title=r.report_name,
                report_name=r.report_name,
                report_type=r.report_type,
                generated_date=r.generated_at,
                generated_at=r.generated_at,
                report_status=r.report_status,
                format=ext,
                file_path=r.file_path,
                file_size=size_formatted,
                file_size_bytes=file_size_bytes,
                download_url=f"/api/reports/{r.id}/download",
                message="Report metadata record from SQLite.",
            )
        )
    return ReportListResponse(
        reports=formatted_items,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
    )


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
@router.post(
    "/generate",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Quality Audit Report",
    description="Generates physical CSV or PDF audit report from database records and saves metadata in SQLite.",
)
def generate_report(
    payload: ReportGenerateRequest,
    db: Session = Depends(get_db),
):
    r = report_service.generate_report(db=db, payload=payload)
    file_size_bytes = 0
    if r.file_path:
        fp = Path(r.file_path)
        if fp.is_file():
            file_size_bytes = fp.stat().st_size
        else:
            alt = report_service.report_dir / fp.name
            if alt.is_file():
                file_size_bytes = alt.stat().st_size

    size_formatted = f"{(file_size_bytes / 1024):.1f} KB" if file_size_bytes < 1024 * 1024 else f"{(file_size_bytes / (1024 * 1024)):.1f} MB"
    fmt = payload.format.value.upper()
    return ReportResponse(
        id=r.id,
        report_id=f"REP-{r.id:04d}",
        title=r.report_name,
        report_name=r.report_name,
        report_type=r.report_type,
        generated_date=r.generated_at,
        generated_at=r.generated_at,
        report_status=r.report_status,
        format=fmt,
        file_path=r.file_path,
        file_size=size_formatted,
        file_size_bytes=file_size_bytes,
        download_url=f"/api/reports/{r.id}/download",
        message=f"Physical {fmt} report generated and stored in backend/reports/.",
    )


@router.get(
    "/{report_id}/download",
    summary="Download Physical Report File",
    description="Streams the generated CSV or PDF audit report file from backend/reports/.",
)
def download_report_file(
    report_id: str,
    db: Session = Depends(get_db),
):
    file_path, filename, media_type = report_service.get_report_file_for_download(db=db, report_id=report_id)
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type,
    )


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get Report Metadata by ID",
    description="Retrieves status and metadata for a specific quality audit report from SQLite.",
)
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
):
    r = report_service.get_report_by_id(db=db, report_id=report_id)
    return ReportResponse(
        id=r.id,
        report_id=f"REP-{r.id:04d}",
        title=r.report_name,
        report_name=r.report_name,
        report_type=r.report_type,
        generated_date=r.generated_at,
        generated_at=r.generated_at,
        report_status=r.report_status,
        format="PDF" if (r.file_path and r.file_path.endswith(".pdf")) else "CSV",
        file_path=r.file_path,
        message="Report metadata loaded from SQLite.",
    )

