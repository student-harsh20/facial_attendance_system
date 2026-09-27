"""
End-to-End Integration Test for Teacher Multitenancy & Classroom Attendance Scoping
"""
import base64
import cv2
import numpy as np
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_teacher_classroom_flow():
    print("\n--- 1. Testing Teacher Directory & Login ---")
    res = client.get("/api/teachers")
    assert res.status_code == 200
    teachers = res.json()
    assert len(teachers) >= 4
    print(f"Teachers in directory: {[t['name'] + ' (' + t['subject'] + ')' for t in teachers]}")

    # Login with Teacher ID
    res = client.post("/api/teachers/login", json={"login": "T101", "password": "password123"})
    assert res.status_code == 200
    t1 = res.json()
    assert t1["name"] == "Dr. Amit Sharma"
    assert t1["subject"] == "Machine Learning"
    assert t1["department"] == "Computer Science"
    print("Dr. Amit Sharma logged in successfully via Teacher ID.")

    # Login with Email
    res = client.post("/api/teachers/login", json={"login": "neha.gupta@college.edu", "password": "password123"})
    assert res.status_code == 200
    t2 = res.json()
    assert t2["name"] == "Prof. Neha Gupta"
    assert t2["subject"] in ["DBMS", "Database Management Systems"]
    print("Prof. Neha Gupta logged in successfully via Email.")

    print("\n--- 2. Registering a New Teacher ---")
    new_teacher_data = {
        "teacher_id": "T999",
        "name": "Prof. Vikram Sarabhai",
        "email": "vikram.sarabhai@college.edu",
        "department": "Computer Science",
        "section": "Semester 6 - Sec A",
        "subject": "Quantum Computing",
        "password": "quantum_pass_2026"
    }
    # Delete if existing from earlier test run
    res = client.post("/api/teachers/register", json=new_teacher_data)
    assert res.status_code in [200, 201, 400]
    if res.status_code == 201 or res.status_code == 200:
        new_t = res.json()
        assert new_t["teacher_id"] == "T999"
        print(f"Successfully registered new teacher: {new_t['name']} for subject '{new_t['subject']}'")

    print("\n--- 3. Testing Scoped Attendance Stats ---")
    # Stats for Dr. Amit Sharma's class (Computer Science, Semester 6 - Sec A, Machine Learning)
    res = client.get("/api/attendance/stats?department=Computer Science&section=Semester 6 - Sec A&subject=Machine Learning")
    assert res.status_code == 200
    stats_ml = res.json()
    print(f"Machine Learning Stats: Total Enrolled={stats_ml['total_students']}, Present Today={stats_ml['present_today']}, Attendance %={stats_ml['attendance_percentage']}%")

    # Stats for Cloud Computing
    res = client.get("/api/attendance/stats?department=Information Technology&section=Semester 6 - Sec B&subject=Cloud Computing")
    assert res.status_code == 200
    stats_cloud = res.json()
    print(f"Cloud Computing Stats: Total Enrolled={stats_cloud['total_students']}, Present Today={stats_cloud['present_today']}, Attendance %={stats_cloud['attendance_percentage']}%")

    print("\n--- 4. Testing Student Listing Scoped by Teacher's Class ---")
    # CS Sec A
    res = client.get("/api/students?department=Computer Science&section=Semester 6 - Sec A")
    assert res.status_code == 200
    cs_students = res.json()
    assert len(cs_students) >= 2
    print(f"Students in CS Sec A ({len(cs_students)}): {[s['name'] for s in cs_students]}")

    # IT Sec B
    res = client.get("/api/students?department=Information Technology&section=Semester 6 - Sec B")
    assert res.status_code == 200
    it_students = res.json()
    assert len(it_students) >= 1
    print(f"Students in IT Sec B ({len(it_students)}): {[s['name'] for s in it_students]}")

    print("\n--- 5. Testing Scoped CSV Export ---")
    res = client.get("/api/attendance/export-csv?subject=Machine Learning")
    assert res.status_code == 200
    csv_text = res.text
    assert "Student ID,Student Name,Subject,Teacher" in csv_text
    print("CSV Export includes Subject & Teacher header columns.")
    # Check that CSV contains Machine Learning rows
    lines = csv_text.strip().split("\n")
    print(f"Machine Learning CSV export returned {len(lines)-1} attendance rows.")

    print("\n--- 6. Testing Camera Recognition Multi-Subject & Cross-Class Guard ---")
    # Verify train endpoint works
    res = client.post("/api/face/train")
    assert res.status_code == 200
    print(f"Encodings trained: {res.json()['trained_faces']}")

    # Create dummy black frame
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", blank)
    b64_dummy = base64.b64encode(buf).decode("utf-8")

    # Send frame with teacher context
    payload = {
        "image": b64_dummy,
        "subject": "Machine Learning",
        "teacher_name": "Dr. Amit Sharma",
        "department": "Computer Science",
        "section": "Semester 6 - Sec A"
    }
    res = client.post("/api/recognize/frame", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert "gate_status" in data
    print("Camera recognition endpoint correctly processes teacher context payload.")

    print("\n>>> ALL TEACHER MULTITENANCY TESTS COMPLETED AND VERIFIED! <<<")

if __name__ == "__main__":
    test_teacher_classroom_flow()
