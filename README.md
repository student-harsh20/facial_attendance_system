# Face Recognition Based Attendance System
> **College Minor Project** &bull; Real-time AI Face Recognition & Attendance Management with Cooldown Gate Architecture.

---

## 🌟 Overview

The **Face Recognition Based Attendance System** is an automated attendance management platform designed specifically for college/institutional entry gates. Using computer vision and deep learning face embeddings, the system identifies registered students through a browser camera, marks their attendance, enforces a **single attendance per day** rule at both application and database levels, and provides an intelligent **entry-gate recognition buffer / cooldown** to prevent duplicate captures as students pass the camera.

---

## 🚀 Key Features

1. **Interactive Dashboard**: Real-time metrics for total registered students, today's present count, attendance percentage, and recent activity logs.
2. **Student Registration**: Register students with Roll Number, Name, Department, Course, Semester, and Face Photo (file upload or webcam snapshot). Photos are validated with deep neural nets to ensure exactly one face is present.
3. **Deep Learning Face Recognition**: Powered by OpenCV's state-of-the-art **YuNet** face detector and **SFace** (128-dimensional embedding model). Zero C++ compile issues on Windows/Linux/macOS!
4. **Reliable Once-Per-Day Attendance**: Strict database-level unique constraint `(student_id, date)` ensures zero duplicate attendance records, even under concurrent requests.
5. **Entry-Gate Recognition Buffer / Cooldown**:
   - Configurable cooldown timer (e.g. 5–10 seconds).
   - After marking attendance for Student A, temporarily ignores Student A while they move away from the camera.
   - Immediately ready to recognize a *different* Student B without blocking them.
   - Shows live gate status messages: *"Attendance marked for Rahul"*, *"Please wait..."*, *"Ready for next student"*.
6. **Student Directory**: Search and filter students by Roll Number, Name, or Department with instant profile preview and deletion capabilities.
7. **Attendance Records & Filters**: Filter attendance history by date, department, course, or student name.
8. **Instant CSV Export**: Download single-day or filtered attendance logs as `.csv` files for administrative reporting.
9. **Train / Update Face Data**: Synchronize and update in-memory face encodings cache at the click of a button with genuine status and counts.

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend** | Python 3.11+, FastAPI, Uvicorn | High-performance async REST API |
| **Face Recognition** | OpenCV (YuNet + SFace) | Real-time face detection, alignment, and 128-d embeddings |
| **Processing** | NumPy | Vectorized cosine similarity matching |
| **Database** | SQLite + SQLAlchemy ORM | Relational data persistence with strict unique constraints |
| **Data Export** | Python csv / Pandas | Streaming CSV generation |
| **Frontend** | HTML5, CSS3, Modern JavaScript | Responsive dashboard, WebRTC camera feed, and overlays |
| **Environment** | `python-dotenv`, `pydantic-settings` | Centralized environment configurations |
| **Deployment** | Vercel (Frontend), Render/Railway (Backend) | Cloud deployment readiness |

---

## 📂 Project Structure

```text
facial_attendance_system/
├── backend/
│   ├── __init__.py
│   ├── config.py              # Pydantic Settings, paths, and environment loader
│   ├── database.py            # SQLAlchemy engine, session maker, get_db
│   ├── models.py              # Student & Attendance models with UniqueConstraint
│   ├── schemas.py             # Pydantic request/response validation schemas
│   ├── crud.py                # Database queries and atomic attendance marking
│   ├── face_engine.py         # YuNet detection, SFace 128-d feature extraction & matching
│   ├── cooldown.py            # Entry-gate buffer and per-student cooldown tracker
│   └── routers/
│       ├── students.py        # /api/students endpoints (CRUD)
│       ├── attendance.py      # /api/attendance endpoints (records, stats, CSV export)
│       ├── recognize.py       # /api/recognize endpoints (live frame processing & settings)
│       └── face_data.py       # /api/face endpoints (cache training & synchronization)
├── frontend/
│   ├── index.html             # Single-page application interface
│   ├── css/
│   │   └── style.css          # Responsive design & modern aesthetics
│   └── js/
│       ├── api.js             # API service layer (supports local & Vercel setups)
│       ├── camera.js          # WebRTC camera, canvas bounding boxes, audio chime
│       ├── dashboard.js       # Live dashboard metrics & recent logs
│       ├── students.js        # Student registration & webcam capture
│       ├── attendance.js      # Attendance records table & CSV export
│       └── main.js            # Tab navigation, toasts, and training trigger
├── models/
│   ├── face_detection_yunet.onnx       # YuNet ONNX model (232 KB)
│   └── face_recognition_sface.onnx     # SFace ONNX model (38.7 MB)
├── data/
│   ├── attendance.db          # SQLite database file
│   └── encodings_cache.pkl    # Cached face encodings
├── uploads/
│   └── students/              # Registered student portrait photos
├── .env                       # Environment configuration
├── .env.example               # Example configuration template
├── requirements.txt           # Python dependencies
├── run.py                     # One-click server launcher with auto browser open
├── seed_data.py               # Sample data populator for testing
├── test_all.py                # System & API integration test suite
├── test_recognition_flow.py   # End-to-end face recognition verification script
└── vercel.json                # Frontend deployment routing for Vercel
```

---

## ⚙️ Quickstart Installation

### 1. Clone or Open Project
```bash
cd d:/facial_attendance_system
```

### 2. Set Up Python Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configuration (`.env`)
The `.env` file is pre-configured with default values. You can customize:
```env
PROJECT_NAME="Facial Attendance System"
DATABASE_URL="sqlite:///./data/attendance.db"
RECOGNITION_COOLDOWN_SECONDS=6
SIMILARITY_THRESHOLD=0.363
YUNET_SCORE_THRESHOLD=0.6
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=["*"]
```

---

## 🧪 Testing the Project

### Optional: Seed Demo Students & Attendance
To populate mock students and historical logs for dashboard demonstration:
```bash
python seed_data.py
```

### Run Automated Test Suites
1. **API & Integration Tests**:
   ```bash
   python test_all.py
   ```
2. **End-to-End Face Recognition & Cooldown Gate Test**:
   ```bash
   python test_recognition_flow.py
   ```

---

## ▶️ Running the Application

Start the application with a single command:
```bash
python run.py
```
* **Web Application UI**: [http://localhost:8000](http://localhost:8000) (opens automatically in your browser)
* **Interactive API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔍 Feature Walkthrough

### 1. Registering a Student
1. Go to the **Add Student** tab.
2. Enter Roll Number (e.g. `21CS042`), Name, Department, Course, and Semester.
3. Either upload a clear photo or click **Capture from Webcam** to take a live photo.
4. Click **Register Student**. The system validates that exactly one face is present, extracts the 128-dimensional embedding, and immediately updates the live recognition engine.

### 2. Marking Attendance at the Gate
1. Go to the **Gate Camera** tab and click **Start Camera**.
2. Allow browser camera permissions.
3. When a student stands in front of the camera:
   - Green bounding box appears with the student's name and Roll Number.
   - Attendance is instantly marked as `Present` for today's date.
   - A success chime plays and the entry appears on the **Live Activity Feed**.
   - The **Recognition Cooldown Buffer** starts (e.g., 6 seconds) with the status *"Attendance marked for Rahul. Please wait..."*.
   - If Rahul stays in front of the camera, duplicate attendance is ignored.
   - As soon as Rahul moves away, the gate displays *"Ready for next student"*.
   - If another student steps in, they are recognized without delay.

### 3. Viewing Records & Exporting CSV
1. Go to the **Attendance Records** tab.
2. Select any date from the calendar or filter by department/course.
3. Click **Download CSV** to instantly download `attendance_YYYY-MM-DD.csv`.

### 4. Updating Face Data Cache
- Click the **⚡ Train / Update Face Data** button in the top navigation bar at any time to re-synchronize face encodings from the database.

---

## 🌐 Production & Cloud Deployment

This repository is pre-configured and 100% production-ready for deployment:
* **Docker & Docker Compose**: Included [Dockerfile](Dockerfile) and [docker-compose.yml](docker-compose.yml) with persistent volumes.
* **Render.com**: 1-click blueprint deployment with [render.yaml](render.yaml) (free tier with automatic HTTPS).
* **Railway / Heroku**: Pre-configured [Procfile](Procfile).
* **Linux VPS / EC2**: Systemd and Nginx reverse proxy configuration.

👉 **For complete, step-by-step instructions, see the [Comprehensive Deployment Guide (DEPLOYMENT.md)](DEPLOYMENT.md).**

---

## 📜 License & Academic Usage
Built as a college minor project demonstrating the integration of FastAPI, OpenCV Deep Learning models, and modern responsive web development.
