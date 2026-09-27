from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import schemas
from backend.face_engine import face_engine

router = APIRouter(prefix="/api/face", tags=["Face Data Training"])


@router.post("/train", response_model=schemas.TrainStatusResponse)
def train_face_data(db: Session = Depends(get_db)):
    """
    Train / update face encodings from registered students.
    - Iterates over all registered students in the database
    - Re-synchronizes in-memory embeddings matrix
    - Saves cache to disk
    - Returns real counts and status
    """
    result = face_engine.train_or_reload_encodings(db)
    return schemas.TrainStatusResponse(
        status=result["status"],
        total_students=result["total_students"],
        trained_faces=result["trained_faces"],
        message=result["message"],
        timestamp=datetime.now()
    )


@router.get("/status")
def get_face_data_status():
    """Retrieve current in-memory face data cache status."""
    return {
        "status": "ready" if face_engine._initialized else "uninitialized",
        "trained_students_count": len(face_engine.known_students),
        "encodings_count": len(face_engine.known_encodings)
    }
