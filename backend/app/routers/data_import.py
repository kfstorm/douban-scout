"""Data import API endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies.auth import verify_api_key
from app.limiter import limiter
from app.schemas import ImportStatus
from app.services.import_service import import_service

router = APIRouter(prefix="/import", tags=["import"], dependencies=[Depends(verify_api_key)])


class ImportRequest(BaseModel):
    """Import request schema."""

    source_path: str


@router.post("", response_model=ImportStatus)
@limiter.limit(settings.rate_limit_import)
def start_import(
    request: Request,
    import_request: ImportRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> ImportStatus:
    """Start importing data from SQLite file."""
    # Validate path exists
    if not Path(import_request.source_path).exists():
        raise HTTPException(
            status_code=404, detail=f"Source file not found: {import_request.source_path}"
        )

    try:
        return import_service.start_import(import_request.source_path)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.get("/status", response_model=ImportStatus)
@limiter.limit(settings.rate_limit_import)
def get_import_status(request: Request) -> ImportStatus:
    """Get current import status."""
    return import_service.status
