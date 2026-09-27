import os
import pickle
import urllib.request
import numpy as np
import cv2
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.config import settings
from backend.models import Student


class FaceEngine:
    """
    High-performance Deep Learning Face Recognition Engine.
    Uses OpenCV DNN with:
    - YuNet (State-of-the-Art ultra-lightweight real-time Face Detector)
    - SFace (Tsinghua/CAS 128-dimensional Deep Neural Net Face Recognizer)
    """

    def __init__(self):
        self.detector = None
        self.recognizer = None
        # Cache for registered student encodings
        self.known_encodings: List[np.ndarray] = []  # List of 1D float32 arrays (128,)
        self.known_students: List[Dict[str, Any]] = []  # List of student metadata dicts
        self._initialized = False

    def ensure_models_exist(self):
        """Auto-download YuNet and SFace models if not already present."""
        os.makedirs(os.path.dirname(settings.YUNET_MODEL_PATH), exist_ok=True)

        models_info = [
            (
                settings.YUNET_MODEL_PATH,
                "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
                "YuNet Face Detector"
            ),
            (
                settings.SFACE_MODEL_PATH,
                "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
                "SFace Face Recognizer"
            )
        ]

        headers = {"User-Agent": "Mozilla/5.0"}
        for file_path, url, name in models_info:
            if not os.path.exists(file_path) or os.path.getsize(file_path) < 1000:
                print(f"[FaceEngine] Downloading {name} model from GitHub...")
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as resp, open(file_path, "wb") as f:
                    f.write(resp.read())
                print(f"[FaceEngine] Downloaded {name} ({os.path.getsize(file_path)} bytes)")

    def initialize(self):
        """Initialize the ONNX deep learning models."""
        if self._initialized:
            return

        self.ensure_models_exist()

        print("[FaceEngine] Loading YuNet detector and SFace recognizer...")
        # Create YuNet face detector with default 320x320 input size
        self.detector = cv2.FaceDetectorYN.create(
            model=settings.YUNET_MODEL_PATH,
            config="",
            input_size=(320, 320),
            score_threshold=settings.YUNET_SCORE_THRESHOLD,
            nms_threshold=0.3,
            top_k=5000
        )

        # Create SFace deep neural network recognizer
        self.recognizer = cv2.FaceRecognizerSF.create(
            model=settings.SFACE_MODEL_PATH,
            config=""
        )

        self._initialized = True
        print("[FaceEngine] Models loaded successfully!")

    def decode_image_bytes(self, image_bytes: bytes) -> np.ndarray:
        """Decode raw image bytes to an OpenCV BGR numpy array."""
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Failed to decode image. Invalid image file or corrupt data.")
        return img

    def detect_faces(self, img_bgr: np.ndarray, score_threshold: Optional[float] = None) -> List[np.ndarray]:
        """
        Detect faces in image.
        Returns list of face rows [x, y, w, h, x_re, y_re, x_le, y_le, x_nt, y_nt, x_rcm, y_rcm, x_lcm, y_lcm, score].
        """
        self.initialize()
        h, w = img_bgr.shape[:2]
        self.detector.setInputSize((w, h))
        if score_threshold is not None:
            self.detector.setScoreThreshold(score_threshold)
        else:
            self.detector.setScoreThreshold(settings.YUNET_SCORE_THRESHOLD)

        _, faces = self.detector.detect(img_bgr)
        if faces is None:
            return []
        return [face for face in faces]

    def extract_embedding(self, img_bgr: np.ndarray, face_data: np.ndarray) -> np.ndarray:
        """
        Align face using facial landmarks and extract 128-dimensional L2-normalized embedding.
        Returns: 1D float32 numpy array of length 128.
        """
        self.initialize()
        aligned_face = self.recognizer.alignCrop(img_bgr, face_data)
        feature = self.recognizer.feature(aligned_face)  # shape (1, 128)
        # Normalize to unit vector for robust cosine similarity
        norm = np.linalg.norm(feature)
        if norm > 1e-6:
            feature = feature / norm
        return feature.flatten().astype(np.float32)

    def process_registration_photo(self, image_bytes: bytes) -> Tuple[np.ndarray, List[float], Dict[str, int]]:
        """
        Validate student registration photo:
        1. Ensure image is decodable
        2. Validate EXACTLY 1 face is present
        3. Extract 128-d face embedding
        4. Return (image_bgr, embedding_list, bounding_box_dict)
        """
        img_bgr = self.decode_image_bytes(image_bytes)
        faces = self.detect_faces(img_bgr)

        # Fallback with slightly relaxed threshold if no face detected initially
        if len(faces) == 0:
            faces = self.detect_faces(img_bgr, score_threshold=max(0.4, settings.YUNET_SCORE_THRESHOLD - 0.2))

        if len(faces) == 0:
            raise ValueError("No face detected in the photo. Please provide a clear, well-lit portrait.")
        if len(faces) > 1:
            raise ValueError(f"Multiple faces ({len(faces)}) detected. Please provide a photo with only the student.")

        face = faces[0]
        # Bounding box coordinates
        x, y, w, h = int(face[0]), int(face[1]), int(face[2]), int(face[3])
        # Clamp to image boundaries
        img_h, img_w = img_bgr.shape[:2]
        x = max(0, x)
        y = max(0, y)
        w = min(w, img_w - x)
        h = min(h, img_h - y)

        embedding = self.extract_embedding(img_bgr, face)

        return img_bgr, embedding.tolist(), {"x": x, "y": y, "width": w, "height": h}

    def train_or_reload_encodings(self, db: Session) -> Dict[str, Any]:
        """
        Reload all registered students from the database and refresh in-memory encodings cache.
        Also persists to data/encodings_cache.pkl.
        """
        self.initialize()
        students = db.query(Student).all()
        total_students = len(students)

        new_encodings: List[np.ndarray] = []
        new_students: List[Dict[str, Any]] = []
        trained_count = 0

        for student in students:
            encoding_list = student.get_encoding()
            if encoding_list and len(encoding_list) == 128:
                feat = np.array(encoding_list, dtype=np.float32)
                norm = np.linalg.norm(feat)
                if norm > 1e-6:
                    feat = feat / norm
                new_encodings.append(feat)
                new_students.append({
                    "student_id": student.student_id,
                    "name": student.name,
                    "department": student.department,
                    "course": student.course,
                    "semester": student.semester,
                    "photo_path": student.photo_path
                })
                trained_count += 1
            else:
                photo_disk_path = None
                if student.photo_path:
                    rel = student.photo_path.lstrip("/\\")
                    candidate = settings.BASE_DIR / rel
                    if candidate.exists():
                        photo_disk_path = str(candidate)

                if photo_disk_path and os.path.exists(photo_disk_path):
                    # Fallback: re-extract from stored photo
                    try:
                        with open(photo_disk_path, "rb") as pf:
                            img = self.decode_image_bytes(pf.read())
                        f_list = self.detect_faces(img)
                        if len(f_list) > 0:
                            feat = self.extract_embedding(img, f_list[0])
                            new_encodings.append(feat)
                            new_students.append({
                                "student_id": student.student_id,
                                "name": student.name,
                                "department": student.department,
                                "course": student.course,
                                "semester": student.semester,
                                "photo_path": student.photo_path
                            })
                            trained_count += 1
                    except Exception as e:
                        print(f"[FaceEngine] Error processing photo for {student.student_id}: {e}")

        self.known_encodings = new_encodings
        self.known_students = new_students

        # Save cache file
        try:
            with open(settings.ENCODINGS_CACHE_PATH, "wb") as f:
                pickle.dump({"encodings": self.known_encodings, "students": self.known_students}, f)
        except Exception as e:
            print(f"[FaceEngine] Failed to save encodings cache: {e}")

        message = (
            f"Successfully updated face data: {trained_count} out of {total_students} "
            f"registered students ready for recognition."
        )
        return {
            "status": "success",
            "total_students": total_students,
            "trained_faces": trained_count,
            "message": message
        }

    def load_cache_or_db(self, db: Session):
        """Fast startup: load from cache file if valid, or sync from DB."""
        if os.path.exists(settings.ENCODINGS_CACHE_PATH):
            try:
                with open(settings.ENCODINGS_CACHE_PATH, "rb") as f:
                    data = pickle.load(f)
                    self.known_encodings = data.get("encodings", [])
                    self.known_students = data.get("students", [])
                    print(f"[FaceEngine] Loaded {len(self.known_encodings)} student encodings from cache.")
                    return
            except Exception as e:
                print(f"[FaceEngine] Could not load encodings cache, reloading from DB: {e}")

        self.train_or_reload_encodings(db)

    def match_face(self, query_feat: np.ndarray, threshold: Optional[float] = None) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Compare query embedding against all known student encodings using Cosine Similarity.
        Returns:
            (student_dict, confidence_score) if score >= threshold, else (None, confidence_score).
        """
        if not self.known_encodings or len(self.known_encodings) == 0:
            return None, 0.0

        if threshold is None:
            threshold = settings.SIMILARITY_THRESHOLD

        # Stack into matrix for vectorized calculation: shape (N, 128)
        known_matrix = np.array(self.known_encodings, dtype=np.float32)
        # Cosine similarity between normalized vectors = dot product
        similarities = np.dot(known_matrix, query_feat)

        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        if best_score >= threshold:
            return self.known_students[best_idx], best_score

        return None, best_score


# Global singleton instance
face_engine = FaceEngine()
