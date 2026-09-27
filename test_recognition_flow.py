"""
End-to-End Face Recognition & Gate Cooldown Verification Script.
"""
import io
import time
import base64
import urllib.request
import cv2
import numpy as np
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend import crud

client = TestClient(app)

def run_recognition_flow_test():
    print("\n" + "=" * 60)
    print(" TESTING END-TO-END FACE RECOGNITION & COOLDOWN GATE")
    print("=" * 60)

    # 1. Download OpenCV sample face test image (Lena)
    url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/lena.jpg"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        face_bytes = resp.read()

    # Clean up test student if existed
    db = SessionLocal()
    crud.delete_student(db, "21CS999")
    db.close()

    # 2. Register Student with Face Photo via /api/students
    print("\n[Step 1] Registering student '21CS999' with face photo...")
    files = {
        "photo": ("lena.jpg", io.BytesIO(face_bytes), "image/jpeg")
    }
    data = {
        "student_id": "21CS999",
        "name": "Lena Forsen",
        "department": "Computer Science",
        "course": "B.Tech",
        "semester": "Semester 6 - Sec A"
    }

    reg_resp = client.post("/api/students", data=data, files=files)
    assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"
    print("[PASS] Student registered successfully! Face detected and embedding extracted.")

    # 3. Simulate camera frame sending to /api/recognize/frame
    print("\n[Step 2] Sending live camera frame with recognized face...")
    b64_frame = "data:image/jpeg;base64," + base64.b64encode(face_bytes).decode("utf-8")
    
    rec_resp = client.post("/api/recognize/frame", json={"image": b64_frame})
    assert rec_resp.status_code == 200, f"Recognition endpoint failed: {rec_resp.text}"
    rec_data = rec_resp.json()
    assert rec_data["faces_detected"] >= 1
    face_res = rec_data["results"][0]
    print(f"       Recognized: {face_res['name']} ({face_res['student_id']})")
    print(f"       Status: {face_res['status']} | Confidence: {face_res['confidence']}")
    print(f"       Message: {face_res['message']}")
    print(f"       Bounding Box: {face_res['box']}")
    assert face_res["status"] == "marked", f"Expected marked, got {face_res['status']}"
    assert face_res["student_id"] == "21CS999"
    print("[PASS] Face recognized and Attendance Marked as Present!")

    # 4. Immediate repeated frame (should trigger Cooldown Buffer)
    print("\n[Step 3] Sending repeated frame immediately while student is in front of camera...")
    rec_resp2 = client.post("/api/recognize/frame", json={"image": b64_frame})
    assert rec_resp2.status_code == 200
    rec_data2 = rec_resp2.json()
    face_res2 = rec_data2["results"][0]
    print(f"       Status: {face_res2['status']}")
    print(f"       Message: {face_res2['message']}")
    assert face_res2["status"] == "cooldown", f"Expected cooldown, got {face_res2['status']}"
    print("[PASS] Cooldown buffer properly active! Student not spammed.")

    # 5. Test unknown face rejection
    print("\n[Step 4] Testing unknown face rejection...")
    # Generate blank image (no registered face)
    blank_img = np.zeros((300, 300, 3), dtype=np.uint8)
    _, blank_enc = cv2.imencode(".jpg", blank_img)
    blank_b64 = "data:image/jpeg;base64," + base64.b64encode(blank_enc.tobytes()).decode("utf-8")
    rec_blank = client.post("/api/recognize/frame", json={"image": blank_b64})
    assert rec_blank.status_code == 200
    assert rec_blank.json()["faces_detected"] == 0
    print("[PASS] Blank frame correctly detects 0 faces.")

    # 6. Cleanup
    db = SessionLocal()
    crud.delete_student(db, "21CS999")
    db.close()

    print("\n" + "=" * 60)
    print(" ALL RECOGNITION & COOLDOWN TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    run_recognition_flow_test()
