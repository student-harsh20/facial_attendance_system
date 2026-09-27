/**
 * Authentication & Role Manager
 * Manual Login Portal with Role Separation:
 * 1. Admin Login (by Email & Password):
 *    - Teacher Management (Add new teachers, Edit/Change existing teachers, Delete teachers)
 *    - System Overview & Full Attendance Audit
 * 2. Teacher Login (by Branch, Section, Email, and Password):
 *    - Only teachers registered by Admin can log in
 *    - Full student-related features (Dashboard, Gate Camera, Add Student, Student Database, Class Attendance)
 * 3. Logout button inside dashboard nav (No Switch button)
 */
const Auth = (() => {
  const STORAGE_KEY_ROLE = "FACIAL_ATTENDANCE_ROLE";
  const STORAGE_KEY_TEACHER = "FACIAL_ATTENDANCE_TEACHER";
  const STORAGE_KEY_ADMIN = "FACIAL_ATTENDANCE_ADMIN";

  let currentRole = null; // "teacher" | "admin" | null
  let currentTeacher = null;
  let currentAdmin = null;

  // DOM Elements
  let loginScreenEl, appViewEl;
  let navBannerEl, navTitleEl, navSubtitleEl, navBadgeEl, navAvatarEl, btnLogoutEl;
  let teacherLoginFormEl, adminLoginFormEl;

  const init = async () => {
    loginScreenEl = document.getElementById("login-screen");
    appViewEl = document.getElementById("app-view");

    navBannerEl = document.getElementById("nav-teacher-banner");
    navTitleEl = document.getElementById("nav-teacher-name");
    navSubtitleEl = document.getElementById("nav-teacher-class");
    navBadgeEl = document.getElementById("nav-teacher-subject");
    navAvatarEl = document.getElementById("nav-user-avatar");
    btnLogoutEl = document.getElementById("btn-logout");

    teacherLoginFormEl = document.getElementById("teacher-login-form");
    adminLoginFormEl = document.getElementById("admin-login-form");

    // Login Portal Role Toggle (Teacher Login vs Admin Login)
    const roleBtns = document.querySelectorAll(".login-role-btn");
    const roleContents = document.querySelectorAll(".login-tab-content");
    roleBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const tab = btn.getAttribute("data-role-tab");
        roleBtns.forEach((b) => b.classList.remove("active"));
        roleContents.forEach((c) => c.classList.remove("active"));
        btn.classList.add("active");
        const target = document.getElementById(`login-tab-${tab}`);
        if (target) target.classList.add("active");
      });
    });

    // Wire Forms
    if (teacherLoginFormEl) {
      teacherLoginFormEl.addEventListener("submit", handleTeacherLoginSubmit);
    }
    if (adminLoginFormEl) {
      adminLoginFormEl.addEventListener("submit", handleAdminLoginSubmit);
    }

    // Wire Logout Button (Replaces switch button)
    if (btnLogoutEl) {
      btnLogoutEl.addEventListener("click", logout);
    }

    // Check existing stored session
    const savedRole = localStorage.getItem(STORAGE_KEY_ROLE);
    const savedTeacher = localStorage.getItem(STORAGE_KEY_TEACHER);
    const savedAdmin = localStorage.getItem(STORAGE_KEY_ADMIN);

    if (savedRole === "admin" && savedAdmin) {
      try {
        currentAdmin = JSON.parse(savedAdmin);
        currentRole = "admin";
        showAppView();
        applyRoleUI();
        onAdminChanged();
        return;
      } catch (_) {
        currentAdmin = null;
      }
    }

    if (savedRole === "teacher" && savedTeacher) {
      try {
        currentTeacher = JSON.parse(savedTeacher);
        currentRole = "teacher";
        showAppView();
        applyRoleUI();
        onTeacherChanged();
        return;
      } catch (_) {
        currentTeacher = null;
      }
    }

    // Default: Always show the manual login portal on opening!
    showLoginScreen();
  };

  const showLoginScreen = () => {
    if (loginScreenEl) loginScreenEl.style.display = "flex";
    if (appViewEl) appViewEl.style.display = "none";
  };

  const showAppView = () => {
    if (loginScreenEl) loginScreenEl.style.display = "none";
    if (appViewEl) appViewEl.style.display = "block";
  };

  /**
   * Teacher Login: requires Branch, Section, Email, and Password.
   */
  const handleTeacherLoginSubmit = async (e) => {
    e.preventDefault();
    const branch = document.getElementById("login-teacher-branch")?.value;
    const section = document.getElementById("login-teacher-section")?.value.trim();
    const email = document.getElementById("login-teacher-email")?.value.trim();
    const password = document.getElementById("login-teacher-pass")?.value;

    if (!branch || !section || !email || !password) {
      Toast.show("Please enter Branch, Section, Email, and Password.", "warning");
      return;
    }

    const submitBtn = document.getElementById("btn-teacher-login-submit");
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>Verifying credentials...</span>`;

    try {
      const teacher = await API.teacherLogin({
        branch,
        section,
        email,
        password,
      });

      setTeacher(teacher);
      Toast.show(`Welcome, ${teacher.name}! Class session active for ${teacher.subject} (${teacher.department} - ${teacher.section}).`, "success");
      if (teacherLoginFormEl) teacherLoginFormEl.reset();
    } catch (err) {
      Toast.show(`Teacher Login Failed: ${err.message}`, "danger");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    }
  };

  /**
   * Admin Login: requires Email and Password.
   */
  const handleAdminLoginSubmit = async (e) => {
    e.preventDefault();
    const email = document.getElementById("login-admin-email")?.value.trim();
    const password = document.getElementById("login-admin-pass")?.value;

    if (!email || !password) {
      Toast.show("Please enter Administrator Email and Password.", "warning");
      return;
    }

    const submitBtn = document.getElementById("btn-admin-login-submit");
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>Authenticating Admin...</span>`;

    try {
      const admin = await API.adminLogin(email, password);
      setAdmin(admin);
      Toast.show(`Administrator authenticated successfully! Teacher Management active.`, "success");
      if (adminLoginFormEl) adminLoginFormEl.reset();
    } catch (err) {
      Toast.show(`Admin Login Failed: ${err.message}`, "danger");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    }
  };

  const setTeacher = (teacher) => {
    currentRole = "teacher";
    currentTeacher = teacher;
    currentAdmin = null;

    localStorage.setItem(STORAGE_KEY_ROLE, "teacher");
    localStorage.setItem(STORAGE_KEY_TEACHER, JSON.stringify(teacher));
    localStorage.removeItem(STORAGE_KEY_ADMIN);

    showAppView();
    applyRoleUI();
    onTeacherChanged();

    // Select Dashboard tab
    const dashBtn = document.querySelector(".nav-btn[data-tab='dashboard']");
    if (dashBtn) dashBtn.click();
  };

  const setAdmin = (admin) => {
    currentRole = "admin";
    currentAdmin = admin;
    currentTeacher = null;

    localStorage.setItem(STORAGE_KEY_ROLE, "admin");
    localStorage.setItem(STORAGE_KEY_ADMIN, JSON.stringify(admin));
    localStorage.removeItem(STORAGE_KEY_TEACHER);

    showAppView();
    applyRoleUI();
    onAdminChanged();

    // Select Manage Teachers tab
    const adminTabBtn = document.querySelector(".nav-btn[data-tab='admin-teachers']");
    if (adminTabBtn) adminTabBtn.click();
  };

  const logout = () => {
    if (window.CameraController && window.CameraController.stopCamera) {
      window.CameraController.stopCamera();
    }

    currentRole = null;
    currentTeacher = null;
    currentAdmin = null;

    localStorage.removeItem(STORAGE_KEY_ROLE);
    localStorage.removeItem(STORAGE_KEY_TEACHER);
    localStorage.removeItem(STORAGE_KEY_ADMIN);

    // Reset password inputs on logout
    const teacherPass = document.getElementById("login-teacher-pass");
    if (teacherPass) teacherPass.value = "";
    const adminPass = document.getElementById("login-admin-pass");
    if (adminPass) adminPass.value = "";

    showLoginScreen();
    Toast.show("Logged out successfully.", "info");
  };

  const applyRoleUI = () => {
    const isTeacher = currentRole === "teacher";
    const isAdmin = currentRole === "admin";

    // Toggle navigation buttons based on role
    document.querySelectorAll(".nav-btn").forEach((btn) => {
      const tab = btn.getAttribute("data-tab");
      if (isAdmin) {
        // Admin views: Manage Teachers, Admin Overview, Attendance Records
        if (tab === "admin-teachers" || tab === "admin-overview" || tab === "attendance") {
          btn.style.display = "flex";
        } else {
          btn.style.display = "none";
        }
      } else {
        // Teacher views: Dashboard, Gate Camera, Add Student, Student Database, Attendance Records
        if (tab === "admin-teachers" || tab === "admin-overview") {
          btn.style.display = "none";
        } else {
          btn.style.display = "flex";
        }
      }
    });

    // Update Top Banner
    if (isAdmin && currentAdmin) {
      if (navBannerEl) navBannerEl.classList.add("admin-mode");
      if (navAvatarEl) navAvatarEl.textContent = "🛡️";
      if (navTitleEl) navTitleEl.textContent = currentAdmin.name || "System Administrator";
      if (navBadgeEl) {
        navBadgeEl.textContent = "Administrator";
        navBadgeEl.className = "badge badge-warning";
      }
      if (navSubtitleEl) navSubtitleEl.textContent = currentAdmin.email;
    } else if (isTeacher && currentTeacher) {
      if (navBannerEl) navBannerEl.classList.remove("admin-mode");
      if (navAvatarEl) navAvatarEl.textContent = "👨‍🏫";
      if (navTitleEl) navTitleEl.textContent = currentTeacher.name;
      if (navBadgeEl) {
        navBadgeEl.textContent = currentTeacher.subject;
        navBadgeEl.className = "badge badge-primary";
      }
      if (navSubtitleEl) navSubtitleEl.textContent = `${currentTeacher.department} • ${currentTeacher.section}`;

      // Set Student Registration defaults
      const regDept = document.getElementById("reg-department");
      if (regDept && currentTeacher.department) regDept.value = currentTeacher.department;
      const regSem = document.getElementById("reg-semester");
      if (regSem && currentTeacher.section) regSem.value = currentTeacher.section;

      // Set Attendance Filter defaults
      const attDept = document.getElementById("att-filter-dept");
      if (attDept && currentTeacher.department) attDept.value = currentTeacher.department;
      const attSubj = document.getElementById("att-filter-subject");
      if (attSubj && currentTeacher.subject) attSubj.value = currentTeacher.subject;
    }
  };

  const onTeacherChanged = () => {
    if (window.DashboardController?.refreshStats) window.DashboardController.refreshStats();
    if (window.StudentsController?.loadStudents) window.StudentsController.loadStudents();
    if (window.AttendanceController?.loadAttendance) window.AttendanceController.loadAttendance();

    const camBadge = document.getElementById("cam-active-teacher-badge");
    if (camBadge && currentTeacher) {
      camBadge.innerHTML = `
        <div>
          <span>👨‍🏫 <strong>Subject:</strong> ${currentTeacher.subject} &bull; <strong>Class:</strong> ${currentTeacher.department} (${currentTeacher.section}) &bull; <strong>Teacher:</strong> ${currentTeacher.name}</span>
        </div>
      `;
    }
  };

  const onAdminChanged = () => {
    if (window.AdminController) {
      AdminController.loadTeachers();
      AdminController.loadAdminOverviewStats();
    }
    if (window.AttendanceController?.loadAttendance) {
      const deptEl = document.getElementById("att-filter-dept");
      if (deptEl) deptEl.value = "All";
      const subjEl = document.getElementById("att-filter-subject");
      if (subjEl) subjEl.value = "All";
      AttendanceController.loadAttendance();
    }
  };

  const getRole = () => currentRole;
  const getCurrentTeacher = () => currentTeacher;
  const getCurrentAdmin = () => currentAdmin;

  return {
    init,
    getRole,
    getCurrentTeacher,
    getCurrentAdmin,
    setTeacher,
    setAdmin,
    logout,
  };
})();

window.Auth = Auth;
