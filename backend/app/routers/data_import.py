"""Data import API endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import verify_api_key
from app.schemas import ImportStatus
from app.services.import_service import import_service

router = APIRouter(prefix="/import", tags=["import"], dependencies=[Depends(verify_api_key)])


class ImportRequest(BaseModel):
    """Import request schema."""

    source_path: str


@router.post("", response_model=ImportStatus)
def start_import(
    request: ImportRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> ImportStatus:
    """Start importing data from SQLite file."""
    # Validate path exists
    if not Path(request.source_path).exists():
        raise HTTPException(status_code=404, detail=f"Source file not found: {request.source_path}")

    return import_service.start_import(request.source_path)


@router.get("/status", response_model=ImportStatus)
def get_import_status() -> ImportStatus:
    """Get current import status."""
    return import_service.status
