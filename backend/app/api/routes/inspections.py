from typing import Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.inspection import (
    CSVUploadResponse,
    InspectionCreate,
    InspectionListResponse,
    InspectionResponse,
    InspectionUpdate,
)
from app.services.inspection_service import inspection_service

router = APIRouter()


@router.get(
    "",
    response_model=InspectionListResponse,
    summary="List Inspection Records",
    description="Retrieves paginated automotive inspection records filtered by status, category, batch, or component ID.",
)
def list_inspections(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, description="Filter by result outcome ('Passed' or 'Defective')"),
    category: Optional[str] = Query(None, description="Filter by component category"),
    batch: Optional[str] = Query(None, description="Filter by production batch code"),
    component_id: Optional[str] = Query(None, description="Filter by unique component ID"),
    db: Session = Depends(get_db),
):
    items, total = inspection_service.get_inspections(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        category=category,
        batch=batch,
        component_id=component_id,
    )
    return InspectionListResponse(
        items=items,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
    )


@router.get(
    "/{inspection_id}",
    response_model=InspectionResponse,
    summary="Get Inspection Record by ID",
    description="Retrieves a specific inspection record by its primary key.",
)
def get_inspection(
    inspection_id: str,
    db: Session = Depends(get_db),
):
    return inspection_service.get_inspection_by_id(db=db, inspection_id=inspection_id)


@router.post(
    "",
    response_model=InspectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Inspection Record",
    description="Validates and registers a new component inspection record in SQLite.",
)
def create_inspection(
    payload: InspectionCreate,
    db: Session = Depends(get_db),
):
    return inspection_service.create_inspection(db=db, payload=payload)


@router.put(
    "/{inspection_id}",
    response_model=InspectionResponse,
    summary="Update Inspection Record",
    description="Updates existing parameters or observations for an inspection record.",
)
def update_inspection(
    inspection_id: str,
    payload: InspectionUpdate,
    db: Session = Depends(get_db),
):
    return inspection_service.update_inspection(
        db=db, inspection_id=inspection_id, payload=payload
    )


@router.delete(
    "/{inspection_id}",
    summary="Delete Inspection Record",
    description="Removes an inspection record from the database.",
)
def delete_inspection(
    inspection_id: str,
    db: Session = Depends(get_db),
):
    return inspection_service.delete_inspection(db=db, inspection_id=inspection_id)


@router.post(
    "/upload",
    response_model=CSVUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch CSV File Ingestion & Persistence",
    description="Inspects, validates, and batch-inserts component inspection records from CSV into SQLite.",
)
@router.post(
    "/upload-csv",
    response_model=CSVUploadResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def upload_inspection_csv(
    file: UploadFile = File(..., description="Automotive inspection CSV file"),
    db: Session = Depends(get_db),
):
    return await inspection_service.process_csv_upload(db=db, file=file)
