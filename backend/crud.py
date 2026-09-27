import json
import hashlib
import secrets
from datetime import date, datetime, time
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from sqlalchemy.exc import IntegrityError
from backend.models import Student, Attendance, Teacher, Admin


# ---------------- Security / Password Hashing ---------------- #

def hash_password(password: str) -> str:
    """Hash password using salt and SHA-256."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored salt:hash."""
    try:
        salt, hashed = stored_hash.split(":")
        check = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return secrets.compare_digest(hashed, check)
    except Exception:
        return False


# ---------------- Teacher Operations ---------------- #

def get_teacher_by_id(db: Session, teacher_id: str) -> Optional[Teacher]:
    """Retrieve teacher by teacher_id code."""
    return db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()


def get_teacher_by_email(db: Session, email: str) -> Optional[Teacher]:
    """Retrieve teacher by email."""
    return db.query(Teacher).filter(Teacher.email.ilike(email.strip())).first()


def get_teacher_by_login(db: Session, login: str) -> Optional[Teacher]:
    """Retrieve teacher by either teacher_id or email."""
    clean = login.strip()
    return db.query(Teacher).filter(
        or_(
            Teacher.teacher_id == clean,
            Teacher.email.ilike(clean)
        )
    ).first()


def create_teacher(
    db: Session,
    teacher_id: str,
    name: str,
    email: str,
    password: str,
    department: str,
    section: str,
    subject: str
) -> Teacher:
    """Register a new teacher profile."""
    pwd_hash = hash_password(password)
    teacher = Teacher(
        teacher_id=teacher_id.strip(),
        name=name.strip(),
        email=email.strip().lower(),
        department=department.strip(),
        section=section.strip(),
        subject=subject.strip(),
        password_hash=pwd_hash,
        created_at=datetime.now()
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


def get_teachers(db: Session) -> List[Teacher]:
    """Retrieve all teachers."""
    return db.query(Teacher).order_by(Teacher.name.asc()).all()


def verify_teacher_credentials(
    db: Session,
    email_or_id: str,
    password: str,
    branch: Optional[str] = None,
    section: Optional[str] = None
) -> Tuple[Optional[Teacher], Optional[str]]:
    """
    Verify teacher credentials with branch, section, email/login, and password.
    Returns (Teacher, error_message). If successful, error_message is None.
    """
    clean_id = (email_or_id or "").strip()
    if not clean_id:
        return None, "Teacher email or login ID is required."

    teacher = get_teacher_by_login(db, clean_id)
    if not teacher:
        return None, f"Teacher with ID/Email '{clean_id}' was not found."

    if not verify_password(password, teacher.password_hash):
        return None, "Invalid password. Please check your credentials."

    # Validate branch / department if provided
    if branch and branch.strip() and branch.strip() != "All":
        b_clean = branch.strip().lower()
        t_dept = teacher.department.strip().lower()
        if b_clean != t_dept and b_clean not in t_dept and t_dept not in b_clean:
            return None, f"Branch mismatch: Teacher is assigned to '{teacher.department}', not '{branch}'."

    # Validate section if provided
    if section and section.strip() and section.strip() != "All":
        s_clean = section.strip().lower()
        t_sec = teacher.section.strip().lower()
        if s_clean != t_sec and s_clean not in t_sec and t_sec not in s_clean:
            return None, f"Section mismatch: Teacher is assigned to '{teacher.section}', not '{section}'."

    return teacher, None


def update_teacher(
    db: Session,
    teacher_id: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    subject: Optional[str] = None,
    password: Optional[str] = None
) -> Optional[Teacher]:
    """Update teacher details (Name, Email, Branch, Section, Subject, Password)."""
    teacher = get_teacher_by_id(db, teacher_id)
    if not teacher:
        return None

    if name is not None and name.strip():
        teacher.name = name.strip()

    if email is not None and email.strip():
        clean_email = email.strip().lower()
        other = get_teacher_by_email(db, clean_email)
        if other and other.id != teacher.id:
            raise ValueError(f"Email '{clean_email}' is already registered to another teacher.")
        teacher.email = clean_email

    if department is not None and department.strip():
        teacher.department = department.strip()

    if section is not None and section.strip():
        teacher.section = section.strip()

    if subject is not None and subject.strip():
        teacher.subject = subject.strip()

    if password is not None and password.strip():
        teacher.password_hash = hash_password(password.strip())

    db.commit()
    db.refresh(teacher)
    return teacher


def delete_teacher(db: Session, teacher_id: str) -> bool:
    """Delete a teacher by ID."""
    teacher = get_teacher_by_id(db, teacher_id)
    if not teacher:
        return False
    db.delete(teacher)
    db.commit()
    return True



# ---------------- Student Operations ---------------- #

def get_student_by_id(db: Session, student_id: str) -> Optional[Student]:
    """Retrieve a student by their unique student_id / roll number."""
    return db.query(Student).filter(Student.student_id == student_id).first()


def get_students(
    db: Session,
    search: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    skip: int = 0,
    limit: int = 500
) -> List[Student]:
    """List registered students with optional search and class/section filters."""
    query = db.query(Student)

    if department and department.strip() and department != "All":
        query = query.filter(Student.department == department.strip())

    if section and section.strip() and section != "All":
        sec_clean = section.strip()
        query = query.filter(
            or_(
                Student.semester.ilike(f"%{sec_clean}%"),
                Student.semester == sec_clean
            )
        )

    if search and search.strip():
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Student.student_id.ilike(search_filter),
                Student.name.ilike(search_filter),
                Student.department.ilike(search_filter),
                Student.course.ilike(search_filter),
                Student.semester.ilike(search_filter)
            )
        )
    return query.order_by(Student.name.asc()).offset(skip).limit(limit).all()


def create_student(
    db: Session,
    student_id: str,
    name: str,
    department: str,
    course: str,
    semester: str,
    photo_path: str,
    encoding: List[float]
) -> Student:
    """Register a new student with their face encoding."""
    encoding_str = json.dumps(encoding)
    new_student = Student(
        student_id=student_id.strip(),
        name=name.strip(),
        department=department.strip(),
        course=course.strip(),
        semester=semester.strip(),
        photo_path=photo_path,
        encoding_json=encoding_str,
        created_at=datetime.now()
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student


def delete_student(db: Session, student_id: str) -> bool:
    """Delete a student and cascade delete associated attendances."""
    student = get_student_by_id(db, student_id)
    if not student:
        return False
    db.delete(student)
    db.commit()
    return True


# ---------------- Attendance Operations ---------------- #

def has_attendance_today(
    db: Session,
    student_id: str,
    target_date: Optional[date] = None,
    subject: Optional[str] = "General"
) -> bool:
    """Check if attendance already exists for the given student, date, and subject."""
    if target_date is None:
        target_date = date.today()
    query = db.query(Attendance).filter(
        Attendance.student_id == student_id,
        Attendance.date == target_date
    )
    if subject and subject.strip() and subject != "All":
        query = query.filter(Attendance.subject == subject.strip())

    return query.first() is not None


def mark_attendance(
    db: Session,
    student_id: str,
    student_name: str,
    subject: str = "General",
    teacher_name: str = "Teacher",
    department: Optional[str] = None,
    section: Optional[str] = None,
    target_date: Optional[date] = None,
    target_time: Optional[time] = None
) -> Tuple[Optional[Attendance], bool]:
    """
    Mark student attendance for the specific subject and date.
    Returns (Attendance, is_new: bool).
    """
    if target_date is None:
        target_date = date.today()
    if target_time is None:
        target_time = datetime.now().time()

    clean_subject = (subject or "General").strip()
    clean_teacher = (teacher_name or "Teacher").strip()

    # 1. Pre-check: Does record already exist for this student + date + subject?
    existing = db.query(Attendance).filter(
        Attendance.student_id == student_id,
        Attendance.date == target_date,
        Attendance.subject == clean_subject
    ).first()

    if existing:
        return existing, False

    # 2. Insert new record
    new_record = Attendance(
        student_id=student_id,
        student_name=student_name,
        subject=clean_subject,
        teacher_name=clean_teacher,
        department=department,
        section=section,
        date=target_date,
        time=target_time,
        status="Present",
        created_at=datetime.now()
    )
    try:
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return new_record, True
    except IntegrityError:
        db.rollback()
        existing = db.query(Attendance).filter(
            Attendance.student_id == student_id,
            Attendance.date == target_date,
            Attendance.subject == clean_subject
        ).first()
        return existing, False


def get_attendance_records(
    db: Session,
    target_date: Optional[date] = None,
    department: Optional[str] = None,
    course: Optional[str] = None,
    section: Optional[str] = None,
    subject: Optional[str] = None,
    search: Optional[str] = None
) -> List[dict]:
    """
    Retrieve attendance records joined with Student details with flexible class filters.
    """
    query = db.query(Attendance, Student).outerjoin(Student, Attendance.student_id == Student.student_id)

    if target_date:
        query = query.filter(Attendance.date == target_date)
    if department and department.strip() and department != "All":
        query = query.filter(
            or_(
                Attendance.department == department.strip(),
                Student.department == department.strip()
            )
        )
    if course and course.strip() and course != "All":
        query = query.filter(Student.course == course.strip())
    if section and section.strip() and section != "All":
        sec_clean = section.strip()
        query = query.filter(
            or_(
                Attendance.section == sec_clean,
                Student.semester.ilike(f"%{sec_clean}%"),
                Student.semester == sec_clean
            )
        )
    if subject and subject.strip() and subject != "All":
        query = query.filter(Attendance.subject == subject.strip())

    if search and search.strip():
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Attendance.student_id.ilike(search_filter),
                Attendance.student_name.ilike(search_filter),
                Attendance.subject.ilike(search_filter),
                Attendance.teacher_name.ilike(search_filter)
            )
        )

    results = query.order_by(desc(Attendance.date), desc(Attendance.time)).all()

    formatted = []
    for att, stu in results:
        formatted.append({
            "id": att.id,
            "student_id": att.student_id,
            "student_name": att.student_name,
            "date": att.date,
            "time": att.time,
            "status": att.status,
            "subject": att.subject or "General",
            "teacher_name": att.teacher_name or "Teacher",
            "department": stu.department if stu else (att.department or "N/A"),
            "course": stu.course if stu else "N/A",
            "semester": stu.semester if stu else (att.section or "N/A"),
            "section": att.section or (stu.semester if stu else "N/A"),
        })
    return formatted


def get_attendance_stats(
    db: Session,
    target_date: Optional[date] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    subject: Optional[str] = None
) -> dict:
    """Calculate dashboard statistics scoped to teacher class/subject if provided."""
    if target_date is None:
        target_date = date.today()

    # 1. Total students count (scoped to department/section if provided)
    stu_query = db.query(Student)
    if department and department.strip() and department != "All":
        stu_query = stu_query.filter(Student.department == department.strip())
    if section and section.strip() and section != "All":
        sec_clean = section.strip()
        stu_query = stu_query.filter(
            or_(
                Student.semester.ilike(f"%{sec_clean}%"),
                Student.semester == sec_clean
            )
        )
    total_students = stu_query.count()

    # 2. Present today count (scoped to date, subject, and class)
    att_query = db.query(Attendance).filter(Attendance.date == target_date)
    if subject and subject.strip() and subject != "All":
        att_query = att_query.filter(Attendance.subject == subject.strip())
    if department and department.strip() and department != "All":
        att_query = att_query.filter(
            or_(
                Attendance.department == department.strip(),
                Attendance.student_id.in_(
                    db.query(Student.student_id).filter(Student.department == department.strip())
                )
            )
        )
    if section and section.strip() and section != "All":
        sec_clean = section.strip()
        att_query = att_query.filter(
            or_(
                Attendance.section == sec_clean,
                Attendance.student_id.in_(
                    db.query(Student.student_id).filter(
                        or_(
                            Student.semester.ilike(f"%{sec_clean}%"),
                            Student.semester == sec_clean
                        )
                    )
                )
            )
        )
    present_today = att_query.count()

    percentage = 0.0
    if total_students > 0:
        percentage = round((present_today / total_students) * 100, 1)

    return {
        "total_students": total_students,
        "present_today": present_today,
        "attendance_percentage": percentage,
        "today_date": target_date.strftime("%Y-%m-%d"),
        "department": department,
        "section": section,
        "subject": subject
    }


# ---------------- Admin Operations ---------------- #

def get_admin_by_email(db: Session, email: str) -> Optional[Admin]:
    """Retrieve administrator by email."""
    return db.query(Admin).filter(Admin.email.ilike(email.strip())).first()


def create_admin(db: Session, name: str, email: str, password: str) -> Admin:
    """Create a new administrator."""
    pwd_hash = hash_password(password)
    admin = Admin(
        name=name.strip(),
        email=email.strip().lower(),
        password_hash=pwd_hash,
        created_at=datetime.utcnow()
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def ensure_default_admin(db: Session) -> Admin:
    """Ensure at least one default administrator exists."""
    default_email = "admin@college.edu"
    admin = get_admin_by_email(db, default_email)
    if not admin:
        # Check if any admin exists
        first_admin = db.query(Admin).first()
        if not first_admin:
            admin = create_admin(
                db=db,
                name="System Administrator",
                email=default_email,
                password="admin123"
            )
        else:
            admin = first_admin
    return admin


def verify_admin_login(db: Session, email: str, password: str) -> Optional[Admin]:
    """Verify administrator login credentials."""
    clean_email = email.strip().lower()
    admin = get_admin_by_email(db, clean_email)
    if not admin:
        # Check if default admin needs auto-initialization
        if clean_email == "admin@college.edu":
            admin = ensure_default_admin(db)
        else:
            return None

    if verify_password(password, admin.password_hash):
        return admin
    return None


def get_admin_stats(db: Session) -> dict:
    """Retrieve system-wide summary statistics for administrator dashboard."""
    total_teachers = db.query(Teacher).count()
    total_students = db.query(Student).count()
    distinct_depts = db.query(Student.department).distinct().count()
    today = date.today()
    today_attendance = db.query(Attendance).filter(Attendance.date == today).count()

    return {
        "total_teachers": total_teachers,
        "total_students": total_students,
        "total_departments": max(distinct_depts, 1),
        "total_attendance_today": today_attendance,
        "system_status": "Operational & Secure"
    }

