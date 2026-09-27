import os
import cv2
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.config import settings
from backend import crud, schemas
from backend.face_engine import face_engine

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.post("", response_model=schemas.StudentResponse, status_code=status.HTTP_201_CREATED)
async def register_student(
    student_id: str = Form(..., description="Student Roll Number / Unique ID"),
    name: str = Form(..., description="Student Full Name"),
    department: str = Form(..., description="Department"),
    course: str = Form(..., description="Course"),
    semester: str = Form(..., description="Semester/Section"),
    photo: UploadFile = File(..., description="Student Face Photo"),
    db: Session = Depends(get_db)
):
    """
    Register a new student with face photo:
    - Validates photo and detects face
    - Ensures exactly one face is present
    - Generates 128-d face embedding
    - Stores student and encoding
    - Immediately updates live face recognition engine
    """
    clean_id = student_id.strip()
    if not clean_id:
        raise HTTPException(status_code=400, detail="Student ID cannot be empty.")

    # Check if student ID already registered
    existing = crud.get_student_by_id(db, clean_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Student with ID '{clean_id}' is already registered as '{existing.name}'."
        )

    # Read uploaded photo bytes
    try:
        photo_bytes = await photo.read()
        if len(photo_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded photo is empty.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read image upload: {e}")

    # Process and validate face photo with YuNet and SFace
    try:
        img_bgr, embedding, bbox = face_engine.process_registration_photo(photo_bytes)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing face in image: {e}")

    # Save photo to disk
    sanitized_id = "".join(c for c in clean_id if c.isalnum() or c in ("-", "_"))
    photo_filename = f"{sanitized_id}.jpg"
    photo_path = os.path.join(str(settings.UPLOADS_DIR), photo_filename)

    try:
        cv2.imwrite(photo_path, img_bgr)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save student photo on disk: {e}")

    relative_photo_path = f"/uploads/students/{photo_filename}"

    # Store in database
    student = crud.create_student(
        db=db,
        student_id=clean_id,
        name=name.strip(),
        department=department.strip(),
        course=course.strip(),
        semester=semester.strip(),
        photo_path=relative_photo_path,
        encoding=embedding
    )

    # Immediately refresh face engine so recognition works on next frame
    face_engine.train_or_reload_encodings(db)

    return student


@router.get("", response_model=List[schemas.StudentResponse])
def list_students(
    search: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    skip: int = 0,
    limit: int = 500,
    db: Session = Depends(get_db)
):
    """List registered students with optional search and class/section filters."""
    return crud.get_students(
        db=db,
        search=search,
        department=department,
        section=section,
        skip=skip,
        limit=limit
    )


@router.get("/{student_id}", response_model=schemas.StudentResponse)
def get_student(student_id: str, db: Session = Depends(get_db)):
    """Retrieve details of a registered student."""
    student = crud.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    return student


@router.delete("/{student_id}")
def delete_student(student_id: str, db: Session = Depends(get_db)):
    """Delete a student and their photo, then update face encodings."""
    student = crud.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    # Remove photo file if exists
    if student.photo_path:
        local_path = os.path.join(str(settings.BASE_DIR), student.photo_path.lstrip("/"))
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass

    crud.delete_student(db, student_id)

    # Update in-memory encodings
    face_engine.train_or_reload_encodings(db)

    return {"status": "success", "message": f"Student '{student_id}' deleted successfully."}
