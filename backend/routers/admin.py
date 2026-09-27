import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import crud, schemas

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.post("/login", response_model=schemas.AdminResponse)
def login_admin(payload: schemas.AdminLogin, db: Session = Depends(get_db)):
    """
    Administrator login by email and password.
    Enables teacher management and system oversight.
    """
    clean_email = payload.email.strip().lower()
    if not clean_email or not payload.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin email and password are required."
        )

    admin = crud.verify_admin_login(db, clean_email, payload.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrator credentials. Please check your email and password."
        )

    return admin


@router.get("/stats", response_model=schemas.AdminStatsResponse)
def get_admin_dashboard_stats(db: Session = Depends(get_db)):
    """Retrieve system-wide summary metrics for administrator overview."""
    stats = crud.get_admin_stats(db)
    return stats
