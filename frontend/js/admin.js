/**
 * Admin Controller: Teacher Management & System Administration
 * Handles listing teachers, adding new teachers, editing/changing teacher profiles,
 * deleting teachers, and rendering administrator system overview metrics.
 */
const AdminController = (() => {
  let teachersList = [];
  let currentEditingTeacher = null;

  // DOM Elements
  let tbodyEl, searchInputEl, deptFilterEl;
  let addModalEl, editModalEl, addFormEl, editFormEl;
  let statTeachersEl, statStudentsEl, statDeptsEl, statAttendanceEl, statStatusEl;

  const init = () => {
    tbodyEl = document.getElementById("admin-teachers-tbody");
    searchInputEl = document.getElementById("admin-teachers-search");
    deptFilterEl = document.getElementById("admin-teachers-dept-filter");

    addModalEl = document.getElementById("add-teacher-modal");
    editModalEl = document.getElementById("edit-teacher-modal");
    addFormEl = document.getElementById("admin-add-teacher-form");
    editFormEl = document.getElementById("admin-edit-teacher-form");

    statTeachersEl = document.getElementById("admin-stat-teachers");
    statStudentsEl = document.getElementById("admin-stat-students");
    statDeptsEl = document.getElementById("admin-stat-departments");
    statAttendanceEl = document.getElementById("admin-stat-today-att");
    statStatusEl = document.getElementById("admin-stat-status");

    // Search & Filter listeners
    if (searchInputEl) {
      searchInputEl.addEventListener("input", filterAndRenderTeachers);
    }
    if (deptFilterEl) {
      deptFilterEl.addEventListener("change", filterAndRenderTeachers);
    }

    // Modal forms
    if (addFormEl) {
      addFormEl.addEventListener("submit", handleAddTeacherSubmit);
    }
    if (editFormEl) {
      editFormEl.addEventListener("submit", handleEditTeacherSubmit);
    }

    // Close buttons for modals
    const closeButtons = document.querySelectorAll(".admin-modal-close");
    closeButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        closeAddModal();
        closeEditModal();
      });
    });

    // Close modals on backdrop click
    [addModalEl, editModalEl].forEach((modal) => {
      if (modal) {
        modal.addEventListener("click", (e) => {
          if (e.target === modal) {
            closeAddModal();
            closeEditModal();
          }
        });
      }
    });

    // Open Add Teacher button
    const btnOpenAdd = document.getElementById("btn-admin-add-teacher");
    if (btnOpenAdd) {
      btnOpenAdd.addEventListener("click", openAddModal);
    }

    // Refresh teachers button
    const btnRefresh = document.getElementById("btn-admin-refresh-teachers");
    if (btnRefresh) {
      btnRefresh.addEventListener("click", () => {
        loadTeachers();
        Toast.show("Teacher roster refreshed.", "info");
      });
    }
  };

  const loadTeachers = async () => {
    if (!tbodyEl) return;
    try {
      tbodyEl.innerHTML = `<tr><td colspan="7" class="empty-state">Loading teacher directory...</td></tr>`;
      teachersList = await API.getTeachers();
      filterAndRenderTeachers();
    } catch (err) {
      tbodyEl.innerHTML = `<tr><td colspan="7" class="empty-state text-danger">Failed to load teachers: ${err.message}</td></tr>`;
    }
  };

  const filterAndRenderTeachers = () => {
    if (!tbodyEl) return;

    const query = (searchInputEl?.value || "").toLowerCase().trim();
    const dept = deptFilterEl?.value || "All";

    const filtered = teachersList.filter((t) => {
      const matchQuery =
        !query ||
        t.name.toLowerCase().includes(query) ||
        t.email.toLowerCase().includes(query) ||
        t.teacher_id.toLowerCase().includes(query) ||
        t.subject.toLowerCase().includes(query) ||
        t.department.toLowerCase().includes(query);

      const matchDept = dept === "All" || t.department === dept;

      return matchQuery && matchDept;
    });

    if (filtered.length === 0) {
      tbodyEl.innerHTML = `<tr><td colspan="7" class="empty-state">No teachers matching your filter criteria.</td></tr>`;
      return;
    }

    tbodyEl.innerHTML = filtered
      .map((t) => {
        const joinedDate = t.created_at ? new Date(t.created_at).toLocaleDateString() : "—";
        return `
          <tr>
            <td>
              <span class="badge badge-info" style="font-family: monospace; font-size: 0.85rem; font-weight: 700;">
                ${t.teacher_id}
              </span>
            </td>
            <td>
              <div style="display: flex; align-items: center; gap: 0.6rem;">
                <div class="teacher-mini-avatar">👨‍🏫</div>
                <div>
                  <div style="font-weight: 600; color: var(--text-main); font-size: 0.92rem;">${t.name}</div>
                  <div style="font-size: 0.75rem; color: var(--text-muted);">${joinedDate}</div>
                </div>
              </div>
            </td>
            <td>
              <a href="mailto:${t.email}" style="color: var(--primary); text-decoration: none; font-size: 0.85rem;">
                ${t.email}
              </a>
            </td>
            <td>
              <span class="dept-pill">${t.department}</span>
            </td>
            <td>
              <span class="badge badge-outline" style="font-size: 0.8rem;">${t.section}</span>
            </td>
            <td>
              <span class="badge badge-primary" style="font-size: 0.82rem; font-weight: 600;">
                📖 ${t.subject}
              </span>
            </td>
            <td>
              <div style="display: flex; gap: 0.4rem;">
                <button
                  class="btn btn-xs btn-outline btn-edit-teacher"
                  title="Change / Edit Teacher Profile"
                  onclick="AdminController.openEditModal(${JSON.stringify(t).replace(/"/g, '&quot;')})"
                >
                  ✏️ Edit
                </button>
                <button
                  class="btn btn-xs btn-danger btn-delete-teacher"
                  title="Remove Teacher"
                  onclick="AdminController.confirmDeleteTeacher('${t.teacher_id}', '${t.name.replace(/'/g, "\\'")}')"
                >
                  🗑️ Delete
                </button>
              </div>
            </td>
          </tr>
        `;
      })
      .join("");
  };

  const openAddModal = () => {
    if (addFormEl) addFormEl.reset();
    if (addModalEl) addModalEl.classList.add("show");
  };

  const closeAddModal = () => {
    if (addModalEl) addModalEl.classList.remove("show");
  };

  const handleAddTeacherSubmit = async (e) => {
    e.preventDefault();
    const teacherId = document.getElementById("admin-add-tid").value.trim();
    const name = document.getElementById("admin-add-name").value.trim();
    const email = document.getElementById("admin-add-email").value.trim();
    const department = document.getElementById("admin-add-dept").value;
    const section = document.getElementById("admin-add-section").value.trim();
    const subject = document.getElementById("admin-add-subject").value.trim();
    const password = document.getElementById("admin-add-pass").value;

    if (!teacherId || !name || !email || !department || !section || !subject || !password) {
      Toast.show("Please fill out all teacher fields.", "warning");
      return;
    }

    const submitBtn = document.getElementById("btn-admin-add-submit");
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>Creating Teacher...</span>`;

    try {
      const created = await API.teacherRegister({
        teacher_id: teacherId,
        name,
        email,
        department,
        section,
        subject,
        password,
      });

      closeAddModal();
      Toast.show(`Teacher ${created.name} (${created.subject}) successfully created!`, "success");
      await loadTeachers();
      await loadAdminOverviewStats();
    } catch (err) {
      Toast.show(`Failed to add teacher: ${err.message}`, "danger");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    }
  };

  const openEditModal = (teacher) => {
    currentEditingTeacher = teacher;
    document.getElementById("admin-edit-tid-display").textContent = teacher.teacher_id;
    document.getElementById("admin-edit-tid").value = teacher.teacher_id;
    document.getElementById("admin-edit-name").value = teacher.name;
    document.getElementById("admin-edit-email").value = teacher.email;
    document.getElementById("admin-edit-dept").value = teacher.department;
    document.getElementById("admin-edit-section").value = teacher.section;
    document.getElementById("admin-edit-subject").value = teacher.subject;
    document.getElementById("admin-edit-pass").value = ""; // Leave empty if not changing

    if (editModalEl) editModalEl.classList.add("show");
  };

  const closeEditModal = () => {
    currentEditingTeacher = null;
    if (editModalEl) editModalEl.classList.remove("show");
  };

  const handleEditTeacherSubmit = async (e) => {
    e.preventDefault();
    if (!currentEditingTeacher) return;

    const teacherId = currentEditingTeacher.teacher_id;
    const name = document.getElementById("admin-edit-name").value.trim();
    const email = document.getElementById("admin-edit-email").value.trim();
    const department = document.getElementById("admin-edit-dept").value;
    const section = document.getElementById("admin-edit-section").value.trim();
    const subject = document.getElementById("admin-edit-subject").value.trim();
    const password = document.getElementById("admin-edit-pass").value;

    if (!name || !email || !department || !section || !subject) {
      Toast.show("Please complete all required fields.", "warning");
      return;
    }

    const payload = {
      name,
      email,
      department,
      section,
      subject,
    };
    if (password && password.trim()) {
      payload.password = password.trim();
    }

    const submitBtn = document.getElementById("btn-admin-edit-submit");
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>Saving Changes...</span>`;

    try {
      const updated = await API.updateTeacher(teacherId, payload);
      closeEditModal();
      Toast.show(`Teacher profile for '${updated.name}' updated successfully!`, "success");
      await loadTeachers();

      // If active teacher session matches updated teacher, sync storage
      if (window.Auth) {
        const cur = Auth.getCurrentTeacher();
        if (cur && cur.teacher_id === teacherId) {
          Auth.setTeacher(updated);
        }
      }
    } catch (err) {
      Toast.show(`Teacher Update Failed: ${err.message}`, "danger");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    }
  };

  const confirmDeleteTeacher = async (teacherId, teacherName) => {
    if (!confirm(`Are you sure you want to permanently delete teacher "${teacherName}" (ID: ${teacherId})?`)) {
      return;
    }

    try {
      await API.deleteTeacher(teacherId);
      Toast.show(`Teacher "${teacherName}" removed from the system.`, "success");
      await loadTeachers();
      await loadAdminOverviewStats();

      // If deleted teacher was active, clear session
      if (window.Auth) {
        const cur = Auth.getCurrentTeacher();
        if (cur && cur.teacher_id === teacherId) {
          Auth.clearTeacherSession();
        }
      }
    } catch (err) {
      Toast.show(`Failed to delete teacher: ${err.message}`, "danger");
    }
  };

  const loadAdminOverviewStats = async () => {
    try {
      const stats = await API.getAdminStats();
      if (statTeachersEl) statTeachersEl.textContent = stats.total_teachers;
      if (statStudentsEl) statStudentsEl.textContent = stats.total_students;
      if (statDeptsEl) statDeptsEl.textContent = stats.total_departments;
      if (statAttendanceEl) statAttendanceEl.textContent = stats.total_attendance_today;
      if (statStatusEl) statStatusEl.textContent = stats.system_status;
    } catch (err) {
      console.error("[Admin Stats Error]:", err);
    }
  };

  return {
    init,
    loadTeachers,
    openAddModal,
    closeAddModal,
    openEditModal,
    closeEditModal,
    confirmDeleteTeacher,
    loadAdminOverviewStats,
  };
})();

window.AdminController = AdminController;
