"""
Seed script to populate initial sample students and attendance logs.
Run:
    python seed_data.py
"""
import os
import random
from datetime import date, datetime, timedelta
import cv2
import numpy as np

from backend.config import settings
from backend.database import SessionLocal, Base, engine, init_db
from backend.models import Student, Attendance, Teacher
from backend.face_engine import face_engine
from backend import crud

SAMPLE_TEACHERS = [
    {
        "teacher_id": "T101",
        "name": "Dr. Amit Sharma",
        "email": "amit.sharma@college.edu",
        "password": "password123",
        "department": "Computer Science",
        "section": "Semester 6 - Sec A",
        "subject": "Machine Learning"
    },
    {
        "teacher_id": "T102",
        "name": "Prof. Neha Gupta",
        "email": "neha.gupta@college.edu",
        "password": "password123",
        "department": "Computer Science",
        "section": "Semester 6 - Sec A",
        "subject": "Database Management Systems"
    },
    {
        "teacher_id": "T103",
        "name": "Dr. Rohan Patel",
        "email": "rohan.patel@college.edu",
        "password": "password123",
        "department": "Information Technology",
        "section": "Semester 6 - Sec B",
        "subject": "Cloud Computing"
    },
    {
        "teacher_id": "T104",
        "name": "Prof. Ananya Iyer",
        "email": "ananya.iyer@college.edu",
        "password": "password123",
        "department": "Electronics",
        "section": "Semester 4 - Sec A",
        "subject": "Embedded Systems"
    }
]

SAMPLE_STUDENTS = [
    {
        "student_id": "21CS001",
        "name": "Aarav Sharma",
        "department": "Computer Science",
        "course": "B.Tech",
        "semester": "Semester 6 - Sec A",
    },
    {
        "student_id": "21CS014",
        "name": "Priya Patel",
        "department": "Computer Science",
        "course": "B.Tech",
        "semester": "Semester 6 - Sec A",
    },
    {
        "student_id": "21IT023",
        "name": "Rohan Verma",
        "department": "Information Technology",
        "course": "B.Tech",
        "semester": "Semester 6 - Sec B",
    },
    {
        "student_id": "22EC009",
        "name": "Ananya Iyer",
        "department": "Electronics",
        "course": "B.Tech",
        "semester": "Semester 4 - Sec A",
    },
    {
        "student_id": "23CA005",
        "name": "Vikram Singh",
        "department": "Computer Science",
        "course": "MCA",
        "semester": "Semester 2 - Sec A",
    }
]


def create_placeholder_face_image(name: str, path: str):
    """Create a colored avatar image for sample students."""
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    # Background color based on name hash
    color = (
        (hash(name) % 150) + 50,
        ((hash(name) // 7) % 150) + 50,
        ((hash(name) // 13) % 150) + 50
    )
    img[:] = color

    # Draw simple face shape
    cv2.circle(img, (150, 150), 90, (230, 230, 230), -1)
    cv2.putText(
        img,
        name.split()[0][:2].upper(),
        (90, 175),
        cv2.FONT_HERSHEY_SIMPLEX,
        2.2,
        (40, 40, 40),
        4,
        cv2.LINE_AA
    )
    cv2.imwrite(path, img)


def run_seed():
    print("[Seed] Initializing database...")
    init_db()
    db = SessionLocal()

    today = date.today()
    yesterday = today - timedelta(days=1)

    print("[Seed] Ensuring default Administrator account...")
    admin = crud.ensure_default_admin(db)
    print(f"  + Admin: {admin.email} (Ready)")

    print(f"[Seed] Adding {len(SAMPLE_TEACHERS)} sample teachers...")
    for t_data in SAMPLE_TEACHERS:
        existing_t = crud.get_teacher_by_email(db, t_data["email"])
        if not existing_t:
            crud.create_teacher(
                db=db,
                teacher_id=t_data["teacher_id"],
                name=t_data["name"],
                email=t_data["email"],
                password=t_data["password"],
                department=t_data["department"],
                section=t_data["section"],
                subject=t_data["subject"]
            )
            print(f"  + Added Teacher: {t_data['name']} ({t_data['subject']} - {t_data['department']} {t_data['section']})")
        else:
            print(f"  - Teacher {t_data['name']} already exists.")

    print(f"[Seed] Adding {len(SAMPLE_STUDENTS)} sample students...")
    for item in SAMPLE_STUDENTS:
        existing = db.query(Student).filter(Student.student_id == item["student_id"]).first()
        if existing:
            print(f"  - Student {item['student_id']} ({item['name']}) already exists.")
            continue

        photo_filename = f"{item['student_id']}.jpg"
        photo_disk_path = str(settings.UPLOADS_DIR / photo_filename)
        create_placeholder_face_image(item["name"], photo_disk_path)

        # Generate a distinct synthetic 128-d embedding
        np.random.seed(abs(hash(item["student_id"])) % (2**32))
        dummy_embedding = np.random.randn(128).astype(np.float32)
        dummy_embedding = (dummy_embedding / np.linalg.norm(dummy_embedding)).tolist()

        student = Student(
            student_id=item["student_id"],
            name=item["name"],
            department=item["department"],
            course=item["course"],
            semester=item["semester"],
            photo_path=f"/uploads/students/{photo_filename}",
            encoding_json=str(dummy_embedding),
            created_at=datetime.now()
        )
        db.add(student)
        db.commit()
        print(f"  + Registered {item['name']} ({item['student_id']})")

    # Add sample attendance for yesterday & today with subject and teacher tags
    print("[Seed] Adding sample attendance records with subject assignments...")
    students = db.query(Student).all()

    for idx, stu in enumerate(students):
        # Choose teacher and subject based on student's branch and semester
        assigned_subject = "Machine Learning"
        assigned_teacher = "Dr. Amit Sharma"
        if "Information Technology" in stu.department:
            assigned_subject = "Cloud Computing"
            assigned_teacher = "Dr. Rohan Patel"
        elif "Electronics" in stu.department:
            assigned_subject = "Embedded Systems"
            assigned_teacher = "Prof. Ananya Iyer"

        # Mark present today
        if idx % 2 == 0:
            existing_today = db.query(Attendance).filter(
                Attendance.student_id == stu.student_id,
                Attendance.date == today,
                Attendance.subject == assigned_subject
            ).first()
            if not existing_today:
                att_time = (datetime.now() - timedelta(minutes=random.randint(10, 120))).time()
                db.add(Attendance(
                    student_id=stu.student_id,
                    student_name=stu.name,
                    subject=assigned_subject,
                    teacher_name=assigned_teacher,
                    department=stu.department,
                    section=stu.semester,
                    date=today,
                    time=att_time,
                    status="Present",
                    created_at=datetime.now()
                ))

        # Add yesterday attendance
        existing_yesterday = db.query(Attendance).filter(
            Attendance.student_id == stu.student_id,
            Attendance.date == yesterday,
            Attendance.subject == assigned_subject
        ).first()
        if not existing_yesterday:
            db.add(Attendance(
                student_id=stu.student_id,
                student_name=stu.name,
                subject=assigned_subject,
                teacher_name=assigned_teacher,
                department=stu.department,
                section=stu.semester,
                date=yesterday,
                time=(datetime.now() - timedelta(hours=24, minutes=random.randint(5, 50))).time(),
                status="Present",
                created_at=datetime.now() - timedelta(days=1)
            ))

    db.commit()

    # Synchronize face engine encodings
    face_engine.train_or_reload_encodings(db)
    db.close()

    print("[Seed] Successfully seeded sample teachers and student data!")
    print("      Now you can open http://localhost:8000 and log in as any teacher.")


if __name__ == "__main__":
    run_seed()
