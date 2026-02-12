from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.import_service import import_service
from app.schemas import ImportStatus
from pydantic import BaseModel
import os

router = APIRouter(prefix="/import", tags=["import"])


class ImportRequest(BaseModel):
    source_path: str


@router.post("", response_model=ImportStatus)
def start_import(request: ImportRequest, db: Session = Depends(get_db)):
    # Validate path exists
    if not os.path.exists(request.source_path):
        raise HTTPException(
            status_code=404, detail=f"Source file not found: {request.source_path}"
        )

    return import_service.start_import(request.source_path)


@router.get("/status", response_model=ImportStatus)
def get_import_status():
    return import_service.status
