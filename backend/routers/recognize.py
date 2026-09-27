import base64
from datetime import date
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.config import settings
from backend import crud, schemas
from backend.face_engine import face_engine
from backend.cooldown import cooldown_manager

router = APIRouter(prefix="/api/recognize", tags=["Face Recognition"])


class FramePayload(BaseModel):
    # Base64 encoded image string (e.g. data:image/jpeg;base64,...)
    image: str
    subject: Optional[str] = "General"
    teacher_name: Optional[str] = "Teacher"
    department: Optional[str] = None  # Expected class branch
    section: Optional[str] = None     # Expected class section


class CooldownUpdatePayload(BaseModel):
    cooldown_seconds: int


@router.get("/settings")
def get_cooldown_settings():
    """Retrieve current cooldown and gate status settings."""
    gate_info = cooldown_manager.get_gate_status()
    return {
        "cooldown_seconds": cooldown_manager.cooldown_seconds,
        "similarity_threshold": settings.SIMILARITY_THRESHOLD,
        **gate_info
    }


@router.post("/settings")
def update_cooldown_settings(payload: CooldownUpdatePayload):
    """Dynamically adjust recognition cooldown/buffer time in seconds."""
    if payload.cooldown_seconds < 1 or payload.cooldown_seconds > 60:
        raise HTTPException(status_code=400, detail="Cooldown must be between 1 and 60 seconds.")
    cooldown_manager.update_cooldown_duration(payload.cooldown_seconds)
    return {
        "status": "success",
        "cooldown_seconds": cooldown_manager.cooldown_seconds,
        "message": f"Recognition cooldown updated to {payload.cooldown_seconds} seconds."
    }


@router.post("/frame", response_model=schemas.RecognitionResult)
def process_frame(payload: FramePayload, db: Session = Depends(get_db)):
    """
    Process a video camera frame:
    1. Decode base64 image
    2. Detect all faces
    3. Generate 128-d embeddings
    4. Match with registered students
    5. Verify class membership (if teacher class specified)
    6. Enforce Cooldown buffer & Per-Subject Attendance rule
    7. Return bounding boxes, recognized status, and gate messages
    """
    raw_b64 = payload.image
    if "," in raw_b64:
        # Strip data:image/...;base64, prefix
        raw_b64 = raw_b64.split(",", 1)[1]

    try:
        image_bytes = base64.b64decode(raw_b64)
        img_bgr = face_engine.decode_image_bytes(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image frame: {e}")

    # Detect faces in frame
    face_detections = face_engine.detect_faces(img_bgr)

    results = []
    today = date.today()
    clean_subject = (payload.subject or "General").strip()
    clean_teacher = (payload.teacher_name or "Teacher").strip()

    for face in face_detections:
        x, y, w, h = int(face[0]), int(face[1]), int(face[2]), int(face[3])
        # Boundaries clamp
        img_h, img_w = img_bgr.shape[:2]
        x = max(0, x)
        y = max(0, y)
        w = min(w, img_w - x)
        h = min(h, img_h - y)

        if w < 16 or h < 16:
            continue

        bbox = schemas.BoundingBox(x=x, y=y, width=w, height=h)

        # Extract 128-d face embedding
        try:
            query_feat = face_engine.extract_embedding(img_bgr, face)
        except Exception:
            continue

        # Match against registered students
        matched_student, confidence = face_engine.match_face(query_feat)
        safe_confidence = round(max(0.0, float(confidence)), 3)

        if matched_student is None:
            # UNKNOWN FACE: Must NOT receive attendance
            results.append(schemas.RecognizedFace(
                student_id=None,
                name=None,
                department=None,
                course=None,
                semester=None,
                subject=clean_subject,
                teacher_name=clean_teacher,
                status="unknown",
                confidence=safe_confidence,
                message="Unknown Face - Access Denied / Not Registered",
                box=bbox
            ))
            continue

        student_id = matched_student["student_id"]
        student_name = matched_student["name"]
        student_dept = matched_student.get("department")
        student_sem = matched_student.get("semester")

        # Class membership check (if teacher class specified)
        is_wrong_class = False
        if payload.department and payload.department.strip() and payload.department != "All":
            if student_dept != payload.department.strip():
                is_wrong_class = True
        if payload.section and payload.section.strip() and payload.section != "All":
            sec_clean = payload.section.strip()
            sem_val = student_sem or ""
            if sec_clean not in sem_val and sem_val != sec_clean:
                is_wrong_class = True

        if is_wrong_class:
            results.append(schemas.RecognizedFace(
                student_id=student_id,
                name=student_name,
                department=student_dept,
                course=matched_student.get("course"),
                semester=student_sem,
                subject=clean_subject,
                teacher_name=clean_teacher,
                status="wrong_class",
                confidence=safe_confidence,
                message=f"Wrong Class: {student_name} is in {student_dept} ({student_sem}), not your class!",
                is_wrong_class=True,
                box=bbox
            ))
            continue

        # Check 1: Recognition Cooldown / Buffer
        in_cooldown, remaining = cooldown_manager.is_in_cooldown(student_id)
        if in_cooldown:
            results.append(schemas.RecognizedFace(
                student_id=student_id,
                name=student_name,
                department=student_dept,
                course=matched_student.get("course"),
                semester=student_sem,
                subject=clean_subject,
                teacher_name=clean_teacher,
                status="cooldown",
                confidence=safe_confidence,
                message=f"Please wait... (Buffer active for {student_name}: {remaining}s)",
                box=bbox
            ))
            continue

        # Check 2: One Attendance Per Day For This Subject
        already_present = crud.has_attendance_today(db, student_id, today, subject=clean_subject)
        if already_present:
            # Set short cooldown so system doesn't spam message repeatedly
            cooldown_manager.mark_success(student_id, student_name)
            results.append(schemas.RecognizedFace(
                student_id=student_id,
                name=student_name,
                department=student_dept,
                course=matched_student.get("course"),
                semester=student_sem,
                subject=clean_subject,
                teacher_name=clean_teacher,
                status="already_marked",
                confidence=safe_confidence,
                message=f"{student_name} ({student_id}) already marked for {clean_subject} today!",
                box=bbox
            ))
            continue

        # 3. Mark Attendance (Reliable with Database Constraint)
        record, is_new = crud.mark_attendance(
            db=db,
            student_id=student_id,
            student_name=student_name,
            subject=clean_subject,
            teacher_name=clean_teacher,
            department=student_dept or payload.department,
            section=student_sem or payload.section,
            target_date=today
        )
        # Activate student cooldown / buffer
        cooldown_manager.mark_success(student_id, student_name)

        if is_new:
            results.append(schemas.RecognizedFace(
                student_id=student_id,
                name=student_name,
                department=student_dept,
                course=matched_student.get("course"),
                semester=student_sem,
                subject=clean_subject,
                teacher_name=clean_teacher,
                status="marked",
                confidence=safe_confidence,
                message=f"Attendance marked for {student_name} in {clean_subject}!",
                box=bbox
            ))
        else:
            results.append(schemas.RecognizedFace(
                student_id=student_id,
                name=student_name,
                department=student_dept,
                course=matched_student.get("course"),
                semester=student_sem,
                subject=clean_subject,
                teacher_name=clean_teacher,
                status="already_marked",
                confidence=safe_confidence,
                message=f"{student_name} is already marked for {clean_subject} today.",
                box=bbox
            ))

    gate_info = cooldown_manager.get_gate_status()

    return schemas.RecognitionResult(
        faces_detected=len(face_detections),
        results=results,
        cooldown_seconds=cooldown_manager.cooldown_seconds,
        gate_status=gate_info["gate_status"]
    )
