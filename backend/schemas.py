from pydantic import BaseModel
from typing import Optional, List
from datetime import date as DateType, time as TimeType, datetime


class StudentBase(BaseModel):
    student_id: str
    name: str
    department: str
    course: str
    semester: str


class StudentCreate(StudentBase):
    pass


class StudentResponse(StudentBase):
    id: int
    photo_path: str
    created_at: datetime

    class Config:
        from_attributes = True


class TeacherBase(BaseModel):
    name: str
    email: str
    department: str
    section: str
    subject: str


class TeacherRegister(TeacherBase):
    password: str
    teacher_id: Optional[str] = None


class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    section: Optional[str] = None
    subject: Optional[str] = None
    password: Optional[str] = None


class TeacherLogin(BaseModel):
    branch: Optional[str] = None
    department: Optional[str] = None
    section: Optional[str] = None
    email: Optional[str] = None
    login: Optional[str] = None
    username: Optional[str] = None
    password: str

    @property
    def identifier(self) -> str:
        return (self.email or self.login or self.username or "").strip()


class TeacherResponse(TeacherBase):
    id: int
    teacher_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class AdminLogin(BaseModel):
    email: str
    password: str


class AdminResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    role: str = "admin"

    class Config:
        from_attributes = True


class AdminStatsResponse(BaseModel):
    total_teachers: int
    total_students: int
    total_departments: int
    total_attendance_today: int
    system_status: str



class AttendanceResponse(BaseModel):
    id: int
    student_id: str
    student_name: str
    date: DateType
    time: TimeType
    status: str
    subject: Optional[str] = "General"
    teacher_name: Optional[str] = "Teacher"
    department: Optional[str] = None
    course: Optional[str] = None
    semester: Optional[str] = None
    section: Optional[str] = None

    class Config:
        from_attributes = True


class AttendanceStats(BaseModel):
    total_students: int
    present_today: int
    attendance_percentage: float
    today_date: str
    department: Optional[str] = None
    section: Optional[str] = None
    subject: Optional[str] = None


class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class RecognizedFace(BaseModel):
    student_id: Optional[str] = None
    name: Optional[str] = None
    department: Optional[str] = None
    course: Optional[str] = None
    semester: Optional[str] = None
    subject: Optional[str] = None
    teacher_name: Optional[str] = None
    status: str  # "marked", "already_marked", "cooldown", "unknown", "wrong_class"
    confidence: float
    message: str
    is_wrong_class: Optional[bool] = False
    box: Optional[BoundingBox] = None


class RecognitionResult(BaseModel):
    faces_detected: int
    results: List[RecognizedFace]
    cooldown_seconds: int
    gate_status: str  # "ready", "cooldown", "idle"


class TrainStatusResponse(BaseModel):
    status: str
    total_students: int
    trained_faces: int
    message: str
    timestamp: datetime
