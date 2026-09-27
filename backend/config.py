import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List

BASE_DIR_PATH = Path(__file__).resolve().parent.parent
MODELS_DIR_PATH = BASE_DIR_PATH / "models"
UPLOADS_DIR_PATH = BASE_DIR_PATH / "uploads" / "students"
DATA_DIR_PATH = BASE_DIR_PATH / "data"

# Auto-create necessary directories
UPLOADS_DIR_PATH.mkdir(parents=True, exist_ok=True)
DATA_DIR_PATH.mkdir(parents=True, exist_ok=True)
MODELS_DIR_PATH.mkdir(parents=True, exist_ok=True)

BASE_DIR = BASE_DIR_PATH
MODELS_DIR = MODELS_DIR_PATH
UPLOADS_DIR = UPLOADS_DIR_PATH
DATA_DIR = DATA_DIR_PATH


class Settings(BaseSettings):
    PROJECT_NAME: str = "Facial Attendance System"
    DATABASE_URL: str = f"sqlite:///{DATA_DIR_PATH / 'attendance.db'}"
    RECOGNITION_COOLDOWN_SECONDS: int = 6
    SIMILARITY_THRESHOLD: float = 0.363
    YUNET_SCORE_THRESHOLD: float = 0.6
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["*"]

    # Directory paths
    UPLOADS_DIR: Path = UPLOADS_DIR_PATH
    DATA_DIR: Path = DATA_DIR_PATH
    BASE_DIR: Path = BASE_DIR_PATH

    # Model paths
    YUNET_MODEL_PATH: str = str(MODELS_DIR_PATH / "face_detection_yunet.onnx")
    SFACE_MODEL_PATH: str = str(MODELS_DIR_PATH / "face_recognition_sface.onnx")
    ENCODINGS_CACHE_PATH: str = str(DATA_DIR_PATH / "encodings_cache.pkl")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()
