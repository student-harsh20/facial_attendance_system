import io
import csv
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import crud, schemas

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])


@router.get("", response_model=List[schemas.AttendanceResponse])
def get_attendance(
    target_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    department: Optional[str] = Query(None, description="Filter by Department/Branch"),
    course: Optional[str] = Query(None, description="Filter by Course"),
    section: Optional[str] = Query(None, description="Filter by Section/Semester"),
    subject: Optional[str] = Query(None, description="Filter by Subject"),
    search: Optional[str] = Query(None, description="Search by ID, Name, or Subject"),
    db: Session = Depends(get_db)
):
    """Retrieve attendance records with flexible filtering by class, subject, and date."""
    parsed_date = None
    if target_date:
        try:
            parsed_date = datetime.strptime(target_date.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    records = crud.get_attendance_records(
        db=db,
        target_date=parsed_date,
        department=department,
        course=course,
        section=section,
        subject=subject,
        search=search
    )
    return records


@router.get("/stats", response_model=schemas.AttendanceStats)
def get_stats(
    target_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    department: Optional[str] = Query(None, description="Teacher Branch/Department"),
    section: Optional[str] = Query(None, description="Teacher Section"),
    subject: Optional[str] = Query(None, description="Subject taught"),
    db: Session = Depends(get_db)
):
    """Retrieve dashboard statistics scoped to teacher class and subject."""
    parsed_date = None
    if target_date:
        try:
            parsed_date = datetime.strptime(target_date.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    return crud.get_attendance_stats(
        db=db,
        target_date=parsed_date,
        department=department,
        section=section,
        subject=subject
    )


@router.get("/export-csv")
def export_csv(
    target_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (leave empty for today)"),
    department: Optional[str] = Query(None),
    course: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Export attendance records as a downloadable CSV file.
    Includes Subject, Teacher, Student ID, Name, Branch, Course, Section, Date, Time, Status.
    """
    parsed_date = None
    if target_date:
        try:
            parsed_date = datetime.strptime(target_date.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    else:
        parsed_date = date.today()

    records = crud.get_attendance_records(
        db=db,
        target_date=parsed_date,
        department=department,
        course=course,
        section=section,
        subject=subject
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # CSV Header
    writer.writerow([
        "Student ID",
        "Student Name",
        "Subject",
        "Teacher",
        "Department / Branch",
        "Course",
        "Semester / Section",
        "Date",
        "Time",
        "Status"
    ])

    for r in records:
        writer.writerow([
            r["student_id"],
            r["student_name"],
            r.get("subject", "General"),
            r.get("teacher_name", "Teacher"),
            r["department"],
            r["course"],
            r.get("section") or r.get("semester", ""),
            r["date"].strftime("%Y-%m-%d") if r["date"] else "",
            r["time"].strftime("%H:%M:%S") if r["time"] else "",
            r["status"]
        ])

    output.seek(0)
    clean_subj = "".join(c for c in (subject or "all") if c.isalnum() or c in ("-", "_"))
    date_str = parsed_date.strftime("%Y-%m-%d") if parsed_date else "all"
    filename = f"attendance_{clean_subj}_{date_str}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
