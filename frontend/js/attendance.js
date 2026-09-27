const AttendanceController = (() => {
  let dateInputEl, deptFilterEl, courseFilterEl, sectionFilterEl, subjectFilterEl, searchInputEl, tableBodyEl, exportBtnEl;

  const init = () => {
    dateInputEl = document.getElementById("att-filter-date");
    deptFilterEl = document.getElementById("att-filter-dept");
    courseFilterEl = document.getElementById("att-filter-course");
    sectionFilterEl = document.getElementById("att-filter-section");
    subjectFilterEl = document.getElementById("att-filter-subject");
    searchInputEl = document.getElementById("att-search-input");
    tableBodyEl = document.getElementById("attendance-tbody");
    exportBtnEl = document.getElementById("btn-export-csv");

    // Default to today's local date in YYYY-MM-DD
    const d = new Date();
    const today = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    if (dateInputEl) dateInputEl.value = today;

    // Apply teacher defaults if available
    applyTeacherDefaults();

    // Filter listeners
    if (dateInputEl) dateInputEl.addEventListener("change", loadAttendance);
    if (deptFilterEl) deptFilterEl.addEventListener("change", loadAttendance);
    if (courseFilterEl) courseFilterEl.addEventListener("change", loadAttendance);
    if (sectionFilterEl) sectionFilterEl.addEventListener("input", () => {
      clearTimeout(sectionDebounce);
      sectionDebounce = setTimeout(loadAttendance, 300);
    });
    if (subjectFilterEl) subjectFilterEl.addEventListener("change", loadAttendance);

    let sectionDebounce = null;

    if (searchInputEl) {
      let debounceTimeout = null;
      searchInputEl.addEventListener("input", () => {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(loadAttendance, 300);
      });
    }

    if (exportBtnEl) {
      exportBtnEl.addEventListener("click", handleExportCsv);
    }

    const refreshBtn = document.getElementById("btn-refresh-attendance");
    if (refreshBtn) refreshBtn.addEventListener("click", loadAttendance);

    const btnResetFilters = document.getElementById("btn-reset-att-filters");
    if (btnResetFilters) {
      btnResetFilters.addEventListener("click", () => {
        if (deptFilterEl) deptFilterEl.value = "All";
        if (courseFilterEl) courseFilterEl.value = "All";
        if (sectionFilterEl) sectionFilterEl.value = "";
        if (subjectFilterEl) subjectFilterEl.value = "All";
        if (searchInputEl) searchInputEl.value = "";
        loadAttendance();
      });
    }

    const btnMyClass = document.getElementById("btn-my-class-att-filters");
    if (btnMyClass) {
      btnMyClass.addEventListener("click", () => {
        applyTeacherDefaults();
        loadAttendance();
      });
    }

    loadAttendance();
  };

  const applyTeacherDefaults = () => {
    const teacher = window.Auth ? Auth.getCurrentTeacher() : null;
    if (teacher) {
      if (deptFilterEl && teacher.department) deptFilterEl.value = teacher.department;
      if (sectionFilterEl && teacher.section) sectionFilterEl.value = teacher.section;
      if (subjectFilterEl && teacher.subject) subjectFilterEl.value = teacher.subject;
    }
  };

  const loadAttendance = async () => {
    if (!tableBodyEl) return;

    const dateVal = dateInputEl ? dateInputEl.value : "";
    const deptVal = deptFilterEl ? deptFilterEl.value : "";
    const courseVal = courseFilterEl ? courseFilterEl.value : "";
    const sectionVal = sectionFilterEl ? sectionFilterEl.value.trim() : "";
    const subjectVal = subjectFilterEl ? subjectFilterEl.value : "";
    const searchVal = searchInputEl ? searchInputEl.value : "";

    tableBodyEl.innerHTML = `<tr><td colspan="9" class="empty-state">Loading attendance records...</td></tr>`;

    try {
      const records = await API.getAttendance({
        date: dateVal,
        department: deptVal,
        course: courseVal,
        section: sectionVal,
        subject: subjectVal,
        search: searchVal,
      });

      if (records.length === 0) {
        tableBodyEl.innerHTML = `<tr><td colspan="9" class="empty-state">No attendance records found for selected filters.</td></tr>`;
        return;
      }

      tableBodyEl.innerHTML = records
        .map((r) => {
          const dateStr = r.date || "—";
          const timeStr = r.time ? r.time.slice(0, 8) : "—";
          return `
          <tr>
            <td><strong>${r.student_id}</strong></td>
            <td>${r.student_name}</td>
            <td>${r.department || "—"}</td>
            <td>${r.semester || "—"}</td>
            <td><span class="badge badge-info">${r.subject || "General"}</span></td>
            <td>${r.teacher_name || "—"}</td>
            <td>${dateStr}</td>
            <td>${timeStr}</td>
            <td><span class="badge badge-success">${r.status}</span></td>
          </tr>
        `;
        })
        .join("");
    } catch (err) {
      tableBodyEl.innerHTML = `<tr><td colspan="9" class="empty-state">Failed to load records: ${err.message}</td></tr>`;
    }
  };

  const handleExportCsv = () => {
    const dateVal = dateInputEl ? dateInputEl.value : "";
    const deptVal = deptFilterEl ? deptFilterEl.value : "";
    const courseVal = courseFilterEl ? courseFilterEl.value : "";
    const sectionVal = sectionFilterEl ? sectionFilterEl.value.trim() : "";
    const subjectVal = subjectFilterEl ? subjectFilterEl.value : "";

    const url = API.getExportCsvUrl({
      date: dateVal,
      department: deptVal,
      course: courseVal,
      section: sectionVal,
      subject: subjectVal,
    });

    // Create anchor to trigger direct download
    const a = document.createElement("a");
    a.href = url;
    a.download = `attendance_${subjectVal || "all"}_${dateVal || "all"}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    Toast.show(`Downloading attendance CSV for ${subjectVal ? subjectVal + ' (' + dateVal + ')' : (dateVal || "all records")}...`, "info");
  };

  return {
    init,
    loadAttendance,
    applyTeacherDefaults,
  };
})();

window.AttendanceController = AttendanceController;
