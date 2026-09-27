/**
 * API Service Client for Face Recognition Attendance System
 * Supports both local unified hosting and decoupled Vercel deployment.
 */
const API = (() => {
  // Configurable base URL: checks window override, localStorage, or defaults to relative root
  const getBaseUrl = () => {
    if (window.API_BASE_URL) return window.API_BASE_URL;
    const stored = localStorage.getItem("API_BASE_URL");
    if (stored) return stored;
    return ""; // Relative path for unified FastAPI hosting
  };

  const request = async (endpoint, options = {}) => {
    const url = `${getBaseUrl()}${endpoint}`;
    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        let errMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errData = await response.json();
          if (errData.detail) {
            errMessage = typeof errData.detail === "string" ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch (_) {}
        throw new Error(errMessage);
      }
      // Return JSON or blob depending on content-type
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        return await response.json();
      }
      return response;
    } catch (error) {
      console.error(`[API Error] ${endpoint}:`, error);
      throw error;
    }
  };

  return {
    getBaseUrl,
    setBaseUrl: (url) => {
      localStorage.setItem("API_BASE_URL", url);
    },

    // Health
    getHealth: () => request("/api/health"),

    // Administrator Auth & System Stats
    adminLogin: (email, password) => {
      return request("/api/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
    },

    getAdminStats: () => request("/api/admin/stats"),

    // Teachers & Classroom Auth
    getTeachers: () => request("/api/teachers"),

    getTeacher: (teacherId) => request(`/api/teachers/${encodeURIComponent(teacherId)}`),

    teacherLogin: (loginOrPayload, maybePassword) => {
      let payload = {};
      if (typeof loginOrPayload === "object") {
        payload = loginOrPayload;
      } else {
        payload = { login: loginOrPayload, password: maybePassword };
      }
      return request("/api/teachers/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },

    teacherRegister: (teacherData) => {
      return request("/api/teachers/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(teacherData),
      });
    },

    updateTeacher: (teacherId, teacherData) => {
      return request(`/api/teachers/${encodeURIComponent(teacherId)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(teacherData),
      });
    },

    deleteTeacher: (teacherId) => {
      return request(`/api/teachers/${encodeURIComponent(teacherId)}`, {
        method: "DELETE",
      });
    },


    // Dashboard Stats
    getStats: ({ targetDate = "", department = "", section = "", subject = "" } = {}) => {
      const params = new URLSearchParams();
      if (targetDate) params.append("target_date", targetDate);
      if (department && department !== "All") params.append("department", department);
      if (section && section !== "All") params.append("section", section);
      if (subject && subject !== "All") params.append("subject", subject);

      const qs = params.toString() ? `?${params.toString()}` : "";
      return request(`/api/attendance/stats${qs}`);
    },

    // Students
    getStudents: ({ search = "", department = "", section = "" } = {}) => {
      const params = new URLSearchParams();
      if (search) params.append("search", search);
      if (department && department !== "All") params.append("department", department);
      if (section && section !== "All") params.append("section", section);

      const qs = params.toString() ? `?${params.toString()}` : "";
      return request(`/api/students${qs}`);
    },

    getStudent: (studentId) => request(`/api/students/${encodeURIComponent(studentId)}`),

    registerStudent: (formData) => {
      return request("/api/students", {
        method: "POST",
        body: formData, // FormData handles multipart/form-data boundary automatically
      });
    },

    deleteStudent: (studentId) => {
      return request(`/api/students/${encodeURIComponent(studentId)}`, {
        method: "DELETE",
      });
    },

    // Attendance
    getAttendance: ({ date = "", department = "", course = "", section = "", subject = "", search = "" } = {}) => {
      const params = new URLSearchParams();
      if (date) params.append("target_date", date);
      if (department && department !== "All") params.append("department", department);
      if (course && course !== "All") params.append("course", course);
      if (section && section !== "All") params.append("section", section);
      if (subject && subject !== "All") params.append("subject", subject);
      if (search) params.append("search", search);

      const qs = params.toString() ? `?${params.toString()}` : "";
      return request(`/api/attendance${qs}`);
    },

    getExportCsvUrl: ({ date = "", department = "", course = "", section = "", subject = "" } = {}) => {
      const params = new URLSearchParams();
      if (date) params.append("target_date", date);
      if (department && department !== "All") params.append("department", department);
      if (course && course !== "All") params.append("course", course);
      if (section && section !== "All") params.append("section", section);
      if (subject && subject !== "All") params.append("subject", subject);
      const qs = params.toString() ? `?${params.toString()}` : "";
      return `${getBaseUrl()}/api/attendance/export-csv${qs}`;
    },

    // Face Recognition Frame
    processFrame: (base64Image, teacherContext = {}) => {
      const payload = {
        image: base64Image,
        subject: teacherContext.subject || "",
        teacher_name: teacherContext.name || "",
        department: teacherContext.department || "",
        section: teacherContext.section || "",
      };
      return request("/api/recognize/frame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },

    // Cooldown Settings
    getCooldownSettings: () => request("/api/recognize/settings"),

    updateCooldownSettings: (seconds) => {
      return request("/api/recognize/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cooldown_seconds: seconds }),
      });
    },

    // Train/Update Face Data
    trainFaceData: () => {
      return request("/api/face/train", {
        method: "POST",
      });
    },

    getFaceStatus: () => request("/api/face/status"),
  };
})();
