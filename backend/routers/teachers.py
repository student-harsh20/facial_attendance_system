import secrets
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import crud, schemas

router = APIRouter(prefix="/api/teachers", tags=["Teachers"])


@router.post("/register", response_model=schemas.TeacherResponse, status_code=status.HTTP_201_CREATED)
def register_teacher(payload: schemas.TeacherRegister, db: Session = Depends(get_db)):
    """Register a new teacher assigned to a specific Branch, Section, and Subject."""
    clean_email = payload.email.strip().lower()
    existing = crud.get_teacher_by_email(db, clean_email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A teacher with email '{clean_email}' is already registered."
        )

    # Generate teacher_id if not provided
    tid = payload.teacher_id
    if not tid or not tid.strip():
        # E.g. T101, T102
        count = len(crud.get_teachers(db)) + 1
        tid = f"T{100 + count}"

    # Check if teacher_id is unique
    if crud.get_teacher_by_id(db, tid):
        tid = f"T{secrets.token_hex(2).upper()}"

    teacher = crud.create_teacher(
        db=db,
        teacher_id=tid,
        name=payload.name,
        email=clean_email,
        password=payload.password,
        department=payload.department,
        section=payload.section,
        subject=payload.subject
    )
    return teacher


@router.post("/login", response_model=schemas.TeacherResponse)
def login_teacher(payload: schemas.TeacherLogin, db: Session = Depends(get_db)):
    """
    Teacher login with branch, section, email/login ID, and password.
    Returns teacher profile containing branch, section, and subject.
    """
    login_id = payload.identifier
    if not login_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher email or ID is required."
        )

    branch = payload.branch or payload.department
    teacher, error_msg = crud.verify_teacher_credentials(
        db=db,
        email_or_id=login_id,
        password=payload.password,
        branch=branch,
        section=payload.section
    )
    if error_msg:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg
        )

    return teacher


@router.get("", response_model=List[schemas.TeacherResponse])
def list_teachers(db: Session = Depends(get_db)):
    """List all registered teachers for quick selection and administration."""
    return crud.get_teachers(db)


@router.get("/{teacher_id}", response_model=schemas.TeacherResponse)
def get_teacher(teacher_id: str, db: Session = Depends(get_db)):
    """Retrieve details of a specific teacher."""
    teacher = crud.get_teacher_by_id(db, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found.")
    return teacher


@router.put("/{teacher_id}", response_model=schemas.TeacherResponse)
def update_teacher_endpoint(teacher_id: str, payload: schemas.TeacherUpdate, db: Session = Depends(get_db)):
    """
    Admin Teacher Change functionality:
    Update an existing teacher's name, email, branch/department, section, subject, or password.
    """
    teacher = crud.get_teacher_by_id(db, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail=f"Teacher '{teacher_id}' not found.")

    try:
        updated = crud.update_teacher(
            db=db,
            teacher_id=teacher_id,
            name=payload.name,
            email=payload.email,
            department=payload.department,
            section=payload.section,
            subject=payload.subject,
            password=payload.password
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update teacher: {e}")

    return updated


@router.delete("/{teacher_id}")
def delete_teacher_endpoint(teacher_id: str, db: Session = Depends(get_db)):
    """
    Admin Teacher Manage functionality:
    Delete a teacher profile by ID.
    """
    success = crud.delete_teacher(db, teacher_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Teacher '{teacher_id}' not found.")
    return {
        "status": "success",
        "message": f"Teacher '{teacher_id}' was successfully removed."
    }

