/**
 * Main Application Orchestrator
 * Manages tab switching, global toasts, modals, and the "Train/Update Face Data" feature.
 */

// Global Toast Notification Manager
const Toast = (() => {
  const container = document.getElementById("toast-container");

  const show = (message, type = "info", duration = 4000) => {
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    let icon = "ℹ️";
    if (type === "success") icon = "✅";
    if (type === "danger") icon = "⚠️";
    if (type === "warning") icon = "🔔";

    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      toast.style.transition = "all 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, duration);
  };

  return { show };
})();

window.Toast = Toast;

document.addEventListener("DOMContentLoaded", async () => {
  // Initialize Teacher Authentication & Classroom Session
  if (window.Auth) await Auth.init();

  // Initialize Controllers
  if (window.AdminController) AdminController.init();
  if (window.DashboardController) DashboardController.init();
  if (window.CameraController) CameraController.init();
  if (window.StudentsController) StudentsController.init();
  if (window.AttendanceController) AttendanceController.init();

  // Tab Navigation
  const navBtns = document.querySelectorAll(".nav-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  navBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");

      navBtns.forEach((b) => b.classList.remove("active"));
      tabContents.forEach((t) => t.classList.remove("active"));

      btn.classList.add("active");
      const targetEl = document.getElementById(`tab-${targetTab}`);
      if (targetEl) targetEl.classList.add("active");

      // Auto-stop camera if navigating away from camera tab
      if (targetTab !== "camera" && window.CameraController) {
        CameraController.stopCamera();
      }

      // Refresh data on specific tab activations
      if (targetTab === "admin-teachers" && window.AdminController) {
        AdminController.loadTeachers();
      } else if (targetTab === "admin-overview" && window.AdminController) {
        AdminController.loadAdminOverviewStats();
      } else if (targetTab === "dashboard" && window.DashboardController) {
        DashboardController.refreshStats();
      } else if (targetTab === "camera" && window.CameraController) {
        CameraController.loadSettings();
      } else if (targetTab === "students" && window.StudentsController) {
        StudentsController.loadStudents();
      } else if (targetTab === "attendance" && window.AttendanceController) {
        AttendanceController.loadAttendance();
      }
    });
  });


  // Train/Update Face Data Action Button
  const btnTrainFace = document.getElementById("btn-train-face");
  if (btnTrainFace) {
    btnTrainFace.addEventListener("click", async () => {
      const originalHtml = btnTrainFace.innerHTML;
      btnTrainFace.disabled = true;
      btnTrainFace.innerHTML = `<span>⚡ Synchronizing Encodings...</span>`;

      try {
        const result = await API.trainFaceData();
        Toast.show(
          `Face Data Updated! ${result.trained_faces} student faces synchronized.`,
          "success",
          5000
        );
      } catch (err) {
        Toast.show(`Training/Update Failed: ${err.message}`, "danger");
      } finally {
        btnTrainFace.disabled = false;
        btnTrainFace.innerHTML = originalHtml;
      }
    });
  }

  // Camera start / stop buttons
  const btnStartCam = document.getElementById("btn-start-camera");
  if (btnStartCam) {
    btnStartCam.addEventListener("click", () => CameraController.startCamera());
  }

  const btnStopCam = document.getElementById("btn-stop-camera");
  if (btnStopCam) {
    btnStopCam.addEventListener("click", () => CameraController.stopCamera());
  }

  // Modal close handlers
  document.querySelectorAll(".modal-close, .modal-backdrop").forEach((el) => {
    el.addEventListener("click", (e) => {
      if (e.target === el || el.classList.contains("modal-close")) {
        document.querySelectorAll(".modal-backdrop").forEach((m) => m.classList.remove("show"));
        if (window.StudentsController && window.StudentsController.closeWebcamModal) {
          window.StudentsController.closeWebcamModal();
        }
      }
    });
  });
});
