"""
Comprehensive System & API Verification Test Suite.
"""
import sys
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import settings

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200, f"Health check failed: {response.text}"
    data = response.json()
    assert data["status"] == "healthy"
    print("[PASS] test_health passed:", data)


def test_dashboard_stats():
    response = client.get("/api/attendance/stats")
    assert response.status_code == 200, f"Stats failed: {response.text}"
    data = response.json()
    assert "total_students" in data
    assert "present_today" in data
    assert "attendance_percentage" in data
    print("[PASS] test_dashboard_stats passed:", data)


def test_list_students():
    response = client.get("/api/students")
    assert response.status_code == 200, f"List students failed: {response.text}"
    students = response.json()
    assert isinstance(students, list)
    print(f"[PASS] test_list_students passed: found {len(students)} students")


def test_attendance_records_and_filters():
    response = client.get("/api/attendance")
    assert response.status_code == 200, f"Attendance list failed: {response.text}"
    records = response.json()
    assert isinstance(records, list)
    print(f"[PASS] test_attendance_records passed: found {len(records)} records")

    # Filter test
    dept_response = client.get("/api/attendance?department=Computer%20Science")
    assert dept_response.status_code == 200
    print("[PASS] test_attendance_filter passed")


def test_csv_export():
    response = client.get("/api/attendance/export-csv")
    assert response.status_code == 200, f"CSV export failed: {response.text}"
    assert "text/csv" in response.headers["content-type"]
    assert "Content-Disposition" in response.headers
    content = response.text
    lines = content.strip().split("\n")
    assert len(lines) >= 1
    assert "Student ID,Student Name,Subject,Teacher" in lines[0]
    print(f"[PASS] test_csv_export passed: CSV generated with {len(lines)} lines")


def test_teacher_auth():
    # 1. List teachers
    list_res = client.get("/api/teachers")
    assert list_res.status_code == 200
    teachers = list_res.json()
    assert len(teachers) >= 1
    print(f"[PASS] test_teacher_auth passed: found {len(teachers)} registered teachers")

    # 2. Login teacher
    login_payload = {
        "username": "amit.sharma@college.edu",
        "password": "password123"
    }
    login_res = client.post("/api/teachers/login", json=login_payload)
    assert login_res.status_code == 200, f"Teacher login failed: {login_res.text}"
    teacher = login_res.json()
    assert teacher["name"] == "Dr. Amit Sharma"
    assert teacher["department"] == "Computer Science"
    assert teacher["subject"] == "Machine Learning"
    print(f"[PASS] test_teacher_auth: successfully logged in {teacher['name']} ({teacher['subject']})")


def test_cooldown_settings():
    get_res = client.get("/api/recognize/settings")
    assert get_res.status_code == 200
    orig_val = get_res.json()["cooldown_seconds"]

    post_res = client.post("/api/recognize/settings", json={"cooldown_seconds": 8})
    assert post_res.status_code == 200
    assert post_res.json()["cooldown_seconds"] == 8

    # Reset
    client.post("/api/recognize/settings", json={"cooldown_seconds": orig_val})
    print("[PASS] test_cooldown_settings passed: cooldown dynamic configuration verified")


def test_train_face_data():
    response = client.post("/api/face/train")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "trained_faces" in data
    print(f"[PASS] test_train_face_data passed: {data['trained_faces']} faces synchronized")


def test_frontend_served():
    # Verify index.html
    response = client.get("/")
    assert response.status_code == 200
    assert "Face Recognition Attendance System" in response.text or "FaceAttend" in response.text

    # Verify CSS stylesheet
    css_res = client.get("/css/style.css")
    assert css_res.status_code == 200, f"Failed loading css/style.css: {css_res.status_code}"

    # Verify JavaScript bundles
    for js_name in ["api.js", "auth.js", "admin.js", "camera.js", "dashboard.js", "students.js", "attendance.js", "main.js"]:
        js_res = client.get(f"/js/{js_name}")
        assert js_res.status_code == 200, f"Failed loading js/{js_name}: {js_res.status_code}"

    # Verify fallback avatar asset
    asset_res = client.get("/assets/avatar.png")
    assert asset_res.status_code == 200, f"Failed loading assets/avatar.png: {asset_res.status_code}"

    print("[PASS] test_frontend_served passed: index.html and all CSS/JS/Assets served with 200 OK")


if __name__ == "__main__":
    from test_admin_teacher_manage_flow import test_admin_and_teacher_manage_flow

    print("\n" + "=" * 50)
    print(" RUNNING AUTOMATED SYSTEM INTEGRATION TESTS")
    print("=" * 50)
    test_health()
    test_dashboard_stats()
    test_list_students()
    test_attendance_records_and_filters()
    test_csv_export()
    test_teacher_auth()
    test_admin_and_teacher_manage_flow()
    test_cooldown_settings()
    test_train_face_data()
    test_frontend_served()
    print("=" * 50)
    print(" ALL TESTS PASSED SUCCESSFULLY! 100% OPERATIONAL")
    print("=" * 50 + "\n")

