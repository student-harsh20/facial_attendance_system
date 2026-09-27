/**
 * Students Management Controller
 * Handles student registration (with photo upload or live webcam snap), listing, search, and deletion.
 */
const StudentsController = (() => {
  let formEl, fileInputEl, previewImgEl, studentsTableBodyEl, searchInputEl;
  let webcamModalEl, webcamVideoEl, webcamCanvasEl, webcamStream = null;
  let capturedBlob = null;

  const init = () => {
    formEl = document.getElementById("add-student-form");
    fileInputEl = document.getElementById("student-photo-input");
    previewImgEl = document.getElementById("photo-preview-img");
    studentsTableBodyEl = document.getElementById("students-tbody");
    searchInputEl = document.getElementById("students-search-input");

    webcamModalEl = document.getElementById("webcam-modal");
    webcamVideoEl = document.getElementById("snap-video");
    webcamCanvasEl = document.getElementById("snap-canvas");

    // File input change -> preview
    if (fileInputEl) {
      fileInputEl.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (file) {
          capturedBlob = file;
          const reader = new FileReader();
          reader.onload = (evt) => {
            previewImgEl.src = evt.target.result;
            previewImgEl.style.display = "block";
          };
          reader.readAsDataURL(file);
        }
      });
    }

    // Form submit
    if (formEl) {
      formEl.addEventListener("submit", handleFormSubmit);
    }

    // Search input
    if (searchInputEl) {
      let debounceTimeout = null;
      searchInputEl.addEventListener("input", (e) => {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
          loadStudents(e.target.value);
        }, 300);
      });
    }

    // Webcam snap buttons
    const btnOpenSnap = document.getElementById("btn-open-snap-webcam");
    if (btnOpenSnap) btnOpenSnap.addEventListener("click", openWebcamModal);

    const btnSnapCapture = document.getElementById("btn-snap-capture");
    if (btnSnapCapture) btnSnapCapture.addEventListener("click", captureWebcamPhoto);

    const btnCloseSnap = document.getElementById("btn-close-snap-modal");
    if (btnCloseSnap) btnCloseSnap.addEventListener("click", closeWebcamModal);

    const classFilterEl = document.getElementById("students-class-filter");
    if (classFilterEl) {
      classFilterEl.addEventListener("change", () => {
        loadStudents(searchInputEl ? searchInputEl.value : "");
      });
    }

    loadStudents();
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();

    const studentId = document.getElementById("reg-student-id").value.trim();
    const name = document.getElementById("reg-name").value.trim();
    const department = document.getElementById("reg-department").value;
    const course = document.getElementById("reg-course").value;
    const semester = document.getElementById("reg-semester").value.trim();

    if (!studentId || !name || !department || !course || !semester) {
      Toast.show("Please fill in all student details.", "warning");
      return;
    }

    if (!capturedBlob) {
      Toast.show("Please upload a photo or capture one using your webcam.", "warning");
      return;
    }

    const submitBtn = document.getElementById("btn-register-submit");
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>Validating Face & Registering...</span>`;

    const formData = new FormData();
    formData.append("student_id", studentId);
    formData.append("name", name);
    formData.append("department", department);
    formData.append("course", course);
    formData.append("semester", semester);
    formData.append("photo", capturedBlob, `${studentId}.jpg`);

    try {
      const result = await API.registerStudent(formData);
      Toast.show(`Student '${result.name}' successfully registered!`, "success");
      formEl.reset();
      capturedBlob = null;
      previewImgEl.src = "";
      previewImgEl.style.display = "none";

      // Restore active teacher's department & section
      const teacher = window.Auth ? Auth.getCurrentTeacher() : null;
      if (teacher) {
        const dEl = document.getElementById("reg-department");
        const sEl = document.getElementById("reg-semester");
        if (dEl && teacher.department) dEl.value = teacher.department;
        if (sEl && teacher.section) sEl.value = teacher.section;
      }

      loadStudents();
      if (window.DashboardController) {
        DashboardController.refreshStats();
      }
    } catch (err) {
      Toast.show(`Registration Failed: ${err.message}`, "danger");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    }
  };

  const loadStudents = async (search = "") => {
    if (!studentsTableBodyEl) return;
    try {
      const teacher = window.Auth ? Auth.getCurrentTeacher() : null;
      const classFilterEl = document.getElementById("students-class-filter");
      const onlyMyClass = classFilterEl ? classFilterEl.checked : true;

      const params = { search };
      if (teacher && onlyMyClass) {
        params.department = teacher.department;
        params.section = teacher.section;
      }

      const students = await API.getStudents(params);
      if (students.length === 0) {
        const msg = (teacher && onlyMyClass)
          ? `No students found in ${teacher.department} (${teacher.section}). Uncheck "My Class Only" to view all.`
          : `No students found matching your query.`;
        studentsTableBodyEl.innerHTML = `
          <tr>
            <td colspan="7" class="empty-state">${msg}</td>
          </tr>
        `;
        return;
      }

      studentsTableBodyEl.innerHTML = students
        .map((s) => {
          const photoUrl = s.photo_path ? `${API.getBaseUrl()}${s.photo_path}` : "assets/avatar.png";
          const createdStr = s.created_at ? new Date(s.created_at).toLocaleDateString() : "—";
          return `
          <tr>
            <td>
              <img src="${photoUrl}" alt="${s.name}" class="student-avatar" onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(s.name)}&background=random'" />
            </td>
            <td><strong>${s.student_id}</strong></td>
            <td>${s.name}</td>
            <td>${s.department}</td>
            <td>${s.course}</td>
            <td>${s.semester}</td>
            <td>
              <button class="btn btn-outline btn-sm" onclick="StudentsController.viewStudent('${s.student_id}')">View</button>
              <button class="btn btn-danger btn-sm" onclick="StudentsController.deleteStudent('${s.student_id}')">Delete</button>
            </td>
          </tr>
        `;
        })
        .join("");
    } catch (err) {
      studentsTableBodyEl.innerHTML = `<tr><td colspan="7" class="empty-state">Failed to load students: ${err.message}</td></tr>`;
    }
  };

  const viewStudent = async (studentId) => {
    try {
      const s = await API.getStudent(studentId);
      const photoUrl = s.photo_path ? `${API.getBaseUrl()}${s.photo_path}` : "";
      const modal = document.getElementById("view-student-modal");
      document.getElementById("view-modal-name").textContent = s.name;
      document.getElementById("view-modal-id").textContent = s.student_id;
      document.getElementById("view-modal-dept").textContent = s.department;
      document.getElementById("view-modal-course").textContent = s.course;
      document.getElementById("view-modal-sem").textContent = s.semester;
      document.getElementById("view-modal-photo").src = photoUrl;
      modal.classList.add("show");
    } catch (err) {
      Toast.show(err.message, "danger");
    }
  };

  const deleteStudent = async (studentId) => {
    if (!confirm(`Are you sure you want to delete student '${studentId}'? All attendance records will be removed.`)) {
      return;
    }
    try {
      await API.deleteStudent(studentId);
      Toast.show(`Student '${studentId}' removed.`, "success");
      loadStudents();
      if (window.DashboardController) {
        DashboardController.refreshStats();
      }
    } catch (err) {
      Toast.show(err.message, "danger");
    }
  };

  // Webcam Snapshot Modal Helpers
  const openWebcamModal = async () => {
    if (!webcamModalEl) return;
    webcamModalEl.classList.add("show");
    try {
      webcamStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 480, height: 480, facingMode: "user" },
      });
      webcamVideoEl.srcObject = webcamStream;
      await webcamVideoEl.play();
    } catch (err) {
      Toast.show(`Webcam access error: ${err.message}`, "danger");
      closeWebcamModal();
    }
  };

  const captureWebcamPhoto = () => {
    if (!webcamVideoEl || !webcamCanvasEl) return;
    const w = webcamVideoEl.videoWidth || 480;
    const h = webcamVideoEl.videoHeight || 480;
    webcamCanvasEl.width = w;
    webcamCanvasEl.height = h;
    const snapCtx = webcamCanvasEl.getContext("2d");
    snapCtx.drawImage(webcamVideoEl, 0, 0, w, h);

    webcamCanvasEl.toBlob((blob) => {
      capturedBlob = blob;
      previewImgEl.src = URL.createObjectURL(blob);
      previewImgEl.style.display = "block";
      Toast.show("Face photo captured! Ready for registration.", "success");
      closeWebcamModal();
    }, "image/jpeg", 0.9);
  };

  const closeWebcamModal = () => {
    if (webcamStream) {
      webcamStream.getTracks().forEach((track) => track.stop());
      webcamStream = null;
    }
    if (webcamVideoEl) webcamVideoEl.srcObject = null;
    if (webcamModalEl) webcamModalEl.classList.remove("show");
  };

  return {
    init,
    loadStudents,
    viewStudent,
    deleteStudent,
    closeWebcamModal,
  };
})();

window.StudentsController = StudentsController;
