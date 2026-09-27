"""
Test Suite for Admin Login, Teacher Management (Add, Edit/Change, Delete),
and Teacher Login with Branch, Section, Email, and Password.
"""
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_admin_and_teacher_manage_flow():
    print("\n--- 1. Testing Admin Login with Email & Password ---")
    # Invalid password
    res = client.post("/api/admin/login", json={"email": "admin@college.edu", "password": "wrongpassword"})
    assert res.status_code == 401
    print("Admin login with wrong password rejected with 401.")

    # Valid admin credentials
    res = client.post("/api/admin/login", json={"email": "admin@college.edu", "password": "admin123"})
    assert res.status_code == 200
    admin_data = res.json()
    assert admin_data["email"] == "admin@college.edu"
    assert admin_data["role"] == "admin"
    print(f"Admin logged in successfully: {admin_data['name']} ({admin_data['email']})")

    # Admin Stats
    res = client.get("/api/admin/stats")
    assert res.status_code == 200
    stats = res.json()
    assert "total_teachers" in stats
    assert "total_students" in stats
    print(f"Admin stats: Teachers={stats['total_teachers']}, Students={stats['total_students']}")

    print("\n--- 2. Testing Teacher Management in Admin Portal (Create, Change/Edit, Delete) ---")
    # Clean up test teacher if existing
    test_tid = "TTEST88"
    client.delete(f"/api/teachers/{test_tid}")

    # Create teacher
    create_payload = {
        "teacher_id": test_tid,
        "name": "Prof. Test Einstein",
        "email": "einstein@college.edu",
        "department": "Computer Science",
        "section": "Semester 6 - Sec A",
        "subject": "Theory of Computation",
        "password": "secret_pass_123"
    }
    res = client.post("/api/teachers/register", json=create_payload)
    assert res.status_code in [200, 201]
    created = res.json()
    assert created["teacher_id"] == test_tid
    assert created["name"] == "Prof. Test Einstein"
    print(f"Created teacher: {created['name']} ({created['subject']})")

    # Teacher Change / Edit: update subject and name
    update_payload = {
        "name": "Prof. Albert Einstein",
        "subject": "Advanced Quantum Computing",
        "section": "Semester 6 - Sec A",
        "department": "Computer Science"
    }
    res = client.put(f"/api/teachers/{test_tid}", json=update_payload)
    assert res.status_code == 200
    updated = res.json()
    assert updated["name"] == "Prof. Albert Einstein"
    assert updated["subject"] == "Advanced Quantum Computing"
    print(f"Teacher changed successfully: {updated['name']} -> {updated['subject']}")

    print("\n--- 3. Testing Teacher Login with Branch, Section, Email, and Password ---")
    # Matching Branch, Section, Email, and Password
    login_payload = {
        "branch": "Computer Science",
        "section": "Semester 6 - Sec A",
        "email": "einstein@college.edu",
        "password": "secret_pass_123"
    }
    res = client.post("/api/teachers/login", json=login_payload)
    assert res.status_code == 200
    t_login = res.json()
    assert t_login["email"] == "einstein@college.edu"
    assert t_login["department"] == "Computer Science"
    print(f"Teacher logged in with branch and section successfully: {t_login['name']}")

    # Branch Mismatch Test
    mismatch_branch = {
        "branch": "Mechanical",
        "section": "Semester 6 - Sec A",
        "email": "einstein@college.edu",
        "password": "secret_pass_123"
    }
    res = client.post("/api/teachers/login", json=mismatch_branch)
    assert res.status_code == 401
    assert "Branch mismatch" in res.json()["detail"]
    print("Branch mismatch correctly rejected with 401.")

    # Section Mismatch Test
    mismatch_sec = {
        "branch": "Computer Science",
        "section": "Semester 4 - Sec B",
        "email": "einstein@college.edu",
        "password": "secret_pass_123"
    }
    res = client.post("/api/teachers/login", json=mismatch_sec)
    assert res.status_code == 401
    assert "Section mismatch" in res.json()["detail"]
    print("Section mismatch correctly rejected with 401.")

    # Delete teacher
    res = client.delete(f"/api/teachers/{test_tid}")
    assert res.status_code == 200
    print(f"Teacher {test_tid} successfully deleted by admin.")

    # Verify teacher is gone
    res = client.get(f"/api/teachers/{test_tid}")
    assert res.status_code == 404
    print("Deleted teacher verified non-existent.")

    print("\n>>> ALL ADMIN TEACHER MANAGE & TEACHER LOGIN TESTS PASSED SUCCESSFULLY! <<<\n")


if __name__ == "__main__":
    test_admin_and_teacher_manage_flow()
