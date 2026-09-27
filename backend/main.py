import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response

from backend.config import settings, BASE_DIR, UPLOADS_DIR
from backend.database import engine, Base, SessionLocal, init_db
from backend.face_engine import face_engine
from backend.routers import students, attendance, recognize, face_data, teachers, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup & shutdown lifecycle management:
    - Auto-create SQLite database tables if not existing
    - Initialize face recognition models and cache
    """
    print("[Lifecycle] Initializing database tables...")
    init_db()

    print("[Lifecycle] Initializing Face Engine & ONNX models...")
    face_engine.initialize()

    print("[Lifecycle] Synchronizing face encodings cache...")
    db = SessionLocal()
    try:
        face_engine.load_cache_or_db(db)
    finally:
        db.close()

    print(f"[Lifecycle] Application '{settings.PROJECT_NAME}' started successfully!")
    yield
    print("[Lifecycle] Shutting down application.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="College Minor Project - Face Recognition Based Attendance System with Cooldown Gate",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for external frontend or local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(admin.router)
app.include_router(teachers.router)
app.include_router(students.router)
app.include_router(attendance.router)
app.include_router(recognize.router)
app.include_router(face_data.router)



@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "cooldown_seconds": settings.RECOGNITION_COOLDOWN_SECONDS,
        "registered_students_cached": len(face_engine.known_students)
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


# Mount uploads directory for student photos
uploads_parent = BASE_DIR / "uploads"
uploads_parent.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_parent)), name="uploads")

# Mount frontend directory for seamless local running
frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    css_dir = frontend_dir / "css"
    if css_dir.exists():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
    js_dir = frontend_dir / "js"
    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")
    assets_dir = frontend_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend_root():
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "Frontend index.html not found"}
