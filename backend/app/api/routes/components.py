from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.component import (
    ComponentCreate,
    ComponentListResponse,
    ComponentResponse,
    ComponentUpdate,
)
from app.services.component_service import component_service

router = APIRouter()


@router.get(
    "",
    response_model=ComponentListResponse,
    summary="List Automotive Components",
    description="Retrieves a paginated list of cataloged automotive components.",
)
def list_components(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    category: Optional[str] = Query(None, description="Filter by subsystem category"),
    db: Session = Depends(get_db),
):
    items, total = component_service.get_components(
        db, skip=skip, limit=limit, category=category
    )
    return ComponentListResponse(
        items=items,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
    )


@router.post(
    "",
    response_model=ComponentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Automotive Component",
    description="Registers a new automotive component in the master catalog.",
)
def create_component(
    payload: ComponentCreate,
    db: Session = Depends(get_db),
):
    return component_service.create_component(db, payload)


@router.get(
    "/{component_id}",
    response_model=ComponentResponse,
    summary="Get Component by Code or ID",
    description="Retrieves detailed component specifications by unique code (e.g. CMP-BRK-401) or ID.",
)
def get_component(
    component_id: str,
    db: Session = Depends(get_db),
):
    return component_service.get_component_by_id(db, component_id)

