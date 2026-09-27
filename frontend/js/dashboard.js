/**
 * Dashboard Controller
 * Updates metric cards, today's attendance stats, and recent activity.
 */
const DashboardController = (() => {
  let totalStudentsEl, presentTodayEl, pctEl, todayDateEl, recentTableBodyEl;

  const init = () => {
    totalStudentsEl = document.getElementById("stat-total-students");
    presentTodayEl = document.getElementById("stat-present-today");
    pctEl = document.getElementById("stat-attendance-pct");
    todayDateEl = document.getElementById("stat-today-date");
    recentTableBodyEl = document.getElementById("recent-attendance-tbody");

    refreshStats();
  };

  const refreshStats = async () => {
    try {
      const teacher = window.Auth ? Auth.getCurrentTeacher() : null;
      const params = {};
      if (teacher) {
        params.department = teacher.department;
        params.section = teacher.section;
        params.subject = teacher.subject;
      }

      const stats = await API.getStats(params);
      if (totalStudentsEl) totalStudentsEl.textContent = stats.total_students;
      if (presentTodayEl) presentTodayEl.textContent = stats.present_today;
      if (pctEl) pctEl.textContent = `${stats.attendance_percentage}%`;
      if (todayDateEl) {
        const todayStr = new Date().toLocaleDateString(undefined, {
          weekday: "short",
          year: "numeric",
          month: "short",
          day: "numeric",
        });
        const classInfo = teacher ? ` • ${teacher.subject} (${teacher.section})` : "";
        todayDateEl.textContent = todayStr + classInfo;
      }

      // Also refresh recent logs preview in dashboard
      loadRecentActivity();
    } catch (err) {
      console.warn("Failed to load dashboard metrics:", err);
    }
  };

  const loadRecentActivity = async () => {
    if (!recentTableBodyEl) return;
    try {
      const teacher = window.Auth ? Auth.getCurrentTeacher() : null;
      const params = {};
      if (teacher) {
        params.department = teacher.department;
        params.section = teacher.section;
        params.subject = teacher.subject;
      }

      const records = await API.getAttendance(params);
      const recent = records.slice(0, 5); // top 5

      if (recent.length === 0) {
        recentTableBodyEl.innerHTML = `
          <tr>
            <td colspan="6" class="empty-state">No attendance records logged for this class today yet.</td>
          </tr>
        `;
        return;
      }

      recentTableBodyEl.innerHTML = recent
        .map(
          (r) => `
        <tr>
          <td><strong>${r.student_id}</strong></td>
          <td>${r.student_name}</td>
          <td>${r.department || "—"}</td>
          <td><span class="badge badge-info">${r.subject || "General"}</span></td>
          <td>${r.time ? r.time.slice(0, 8) : "—"}</td>
          <td><span class="badge badge-success">Present</span></td>
        </tr>
      `
        )
        .join("");
    } catch (_) {}
  };

  return {
    init,
    refreshStats,
  };
})();

// Attach to window so other scripts can call refreshStats()
window.DashboardController = DashboardController;
