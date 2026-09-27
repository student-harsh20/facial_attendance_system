# =======================================================
# Production Dockerfile for Facial Attendance System
# =======================================================
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOST=0.0.0.0

# Set container working directory
WORKDIR /app

# Install minimal system dependencies required by OpenCV & healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project source code and assets
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY models/ ./models/
COPY seed_data.py run.py ./

# Ensure data and uploads directories exist
RUN mkdir -p data uploads/students

# Expose application port
EXPOSE 8000

# Container health monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Launch production ASGI server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
