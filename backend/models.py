import json
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, Date, Time, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    course = Column(String(100), nullable=False)
    semester = Column(String(50), nullable=False)
    photo_path = Column(String(255), nullable=False)
    # Face encoding stored as JSON string of 128 float values
    encoding_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to attendance records
    attendances = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")

    def get_encoding(self):
        """Parse encoding_json back into a list of floats."""
        try:
            return json.loads(self.encoding_json)
        except Exception:
            return []


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    teacher_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    department = Column(String(100), nullable=False, index=True)  # Branch
    section = Column(String(50), nullable=False, index=True)     # Section / Semester
    subject = Column(String(100), nullable=False, index=True)    # Subject taught
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String(50), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False, index=True)
    student_name = Column(String(100), nullable=False)
    subject = Column(String(100), default="General", nullable=False, index=True)
    teacher_name = Column(String(100), default="Teacher", nullable=False)
    department = Column(String(100), nullable=True, index=True)  # Branch
    section = Column(String(50), nullable=True, index=True)     # Section / Semester
    date = Column(Date, nullable=False, index=True)
    time = Column(Time, nullable=False)
    status = Column(String(20), default="Present", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to student
    student = relationship("Student", back_populates="attendances")

    # Enforce strictly: ONE ATTENDANCE PER STUDENT PER SUBJECT PER DAY
    __table_args__ = (
        UniqueConstraint("student_id", "date", "subject", name="uq_student_attendance_per_subject_day"),
    )


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), default="Administrator", nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

