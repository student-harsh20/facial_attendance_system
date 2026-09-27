/**
 * Camera & Face Recognition Gate Controller
 * Implements real-time recognition, bounding boxes overlay, and cooldown buffer feedback.
 */
const CameraController = (() => {
  let videoStream = null;
  let isRecognizing = false;
  let frameIntervalId = null;
  let isProcessingFrame = false;

  // DOM elements
  let videoEl, canvasEl, ctx, placeholderEl, gateBannerEl, gateStatusTextEl, gateBadgeEl;
  let cooldownSliderEl, cooldownValEl, liveFeedEl;

  // Web Audio Context for pleasant attendance mark chime
  let audioCtx = null;
  const playSuccessChime = () => {
    try {
      if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
      osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.15); // A5
      gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.35);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.35);
    } catch (_) {}
  };

  const init = () => {
    videoEl = document.getElementById("recognition-video");
    canvasEl = document.getElementById("recognition-canvas");
    placeholderEl = document.getElementById("camera-placeholder");
    gateBannerEl = document.getElementById("gate-banner");
    gateStatusTextEl = document.getElementById("gate-status-text");
    gateBadgeEl = document.getElementById("gate-badge");
    cooldownSliderEl = document.getElementById("cooldown-slider");
    cooldownValEl = document.getElementById("cooldown-val");
    liveFeedEl = document.getElementById("live-attendance-feed");

    if (canvasEl) {
      ctx = canvasEl.getContext("2d");
    }

    // Cooldown duration slider listeners: immediate UI update on input, backend sync on change
    if (cooldownSliderEl) {
      cooldownSliderEl.addEventListener("input", (e) => {
        const val = parseInt(e.target.value, 10);
        if (cooldownValEl) cooldownValEl.textContent = `${val}s`;
      });

      cooldownSliderEl.addEventListener("change", async (e) => {
        const val = parseInt(e.target.value, 10);
        if (cooldownValEl) cooldownValEl.textContent = `${val}s`;
        try {
          await API.updateCooldownSettings(val);
          Toast.show(`Cooldown set to ${val} seconds`, "info");
        } catch (err) {
          Toast.show(err.message, "danger");
        }
      });
    }

    // Direct button click binding for start/stop camera
    const btnStart = document.getElementById("btn-start-camera");
    if (btnStart) {
      btnStart.onclick = () => startCamera();
    }
    const btnStop = document.getElementById("btn-stop-camera");
    if (btnStop) {
      btnStop.onclick = () => stopCamera();
    }

    // Load initial cooldown settings
    loadSettings();
  };

  const loadSettings = async () => {
    try {
      const data = await API.getCooldownSettings();
      if (cooldownSliderEl && data && data.cooldown_seconds) {
        cooldownSliderEl.value = data.cooldown_seconds;
        if (cooldownValEl) cooldownValEl.textContent = `${data.cooldown_seconds}s`;
      }
    } catch (_) {}
  };

  const startCamera = async () => {
    if (!videoEl || !placeholderEl) {
      init();
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      Toast.show(
        "Camera access requires a Secure Context (http://localhost:8000 or HTTPS) and browser permissions.",
        "danger",
        6000
      );
      if (placeholderEl) placeholderEl.style.display = "block";
      return;
    }

    try {
      if (placeholderEl) placeholderEl.style.display = "none";
      videoStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
        audio: false,
      });

      videoEl.srcObject = videoStream;
      await videoEl.play();

      // Adjust canvas to match video stream dimensions
      const updateCanvasSize = () => {
        if (videoEl.videoWidth && videoEl.videoHeight) {
          canvasEl.width = videoEl.videoWidth;
          canvasEl.height = videoEl.videoHeight;
        }
      };
      videoEl.onloadedmetadata = updateCanvasSize;
      updateCanvasSize();

      isRecognizing = true;
      updateGateUI("ready", "Ready for student", "Gate Active");
      startRecognitionLoop();

      const btnStart = document.getElementById("btn-start-camera");
      const btnStop = document.getElementById("btn-stop-camera");
      if (btnStart) btnStart.style.display = "none";
      if (btnStop) btnStop.style.display = "inline-flex";
      Toast.show("Camera started. Ready for attendance!", "success");
    } catch (err) {
      console.error("Camera access error:", err);
      if (placeholderEl) placeholderEl.style.display = "block";
      Toast.show(`Camera Access Failed: ${err.message}`, "danger");
    }
  };

  const stopCamera = () => {
    if (!videoEl || !placeholderEl) {
      init();
    }
    isRecognizing = false;
    if (frameIntervalId) {
      clearInterval(frameIntervalId);
      frameIntervalId = null;
    }
    if (videoStream) {
      videoStream.getTracks().forEach((track) => track.stop());
      videoStream = null;
    }
    if (videoEl) {
      videoEl.srcObject = null;
    }
    if (ctx && canvasEl) {
      ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);
    }
    if (placeholderEl) placeholderEl.style.display = "block";
    updateGateUI("idle", "Camera stopped", "Offline");

    const btnStart = document.getElementById("btn-start-camera");
    const btnStop = document.getElementById("btn-stop-camera");
    if (btnStart) btnStart.style.display = "inline-flex";
    if (btnStop) btnStop.style.display = "none";
  };

  const startRecognitionLoop = () => {
    // Process frames every 600ms for responsive recognition without overloading client/server
    frameIntervalId = setInterval(captureAndSendFrame, 600);
  };

  const captureAndSendFrame = async () => {
    if (!isRecognizing || isProcessingFrame || !videoEl || videoEl.readyState < 2) {
      return;
    }
    const vw = videoEl.videoWidth || 640;
    const vh = videoEl.videoHeight || 480;
    if (vw === 0 || vh === 0) return;

    isProcessingFrame = true;

    try {
      // Offscreen canvas for frame capture
      const offscreen = document.createElement("canvas");
      offscreen.width = videoEl.videoWidth || 640;
      offscreen.height = videoEl.videoHeight || 480;
      const offCtx = offscreen.getContext("2d");
      offCtx.drawImage(videoEl, 0, 0, offscreen.width, offscreen.height);

      const base64Image = offscreen.toDataURL("image/jpeg", 0.75);

      const teacher = window.Auth ? Auth.getCurrentTeacher() : null;
      const response = await API.processFrame(base64Image, teacher || {});
      handleRecognitionResult(response);
    } catch (err) {
      console.warn("Frame recognition error:", err);
    } finally {
      isProcessingFrame = false;
    }
  };

  const handleRecognitionResult = (data) => {
    if (!ctx || !canvasEl) return;

    // Clear previous bounding boxes
    ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);

    const { results, gate_status, cooldown_seconds } = data;

    // Update Gate Status Message & Banner
    if (results.length === 0) {
      updateGateUI("ready", "Ready for student", "Gate Active");
    }

    results.forEach((face) => {
      drawFaceBox(face);

      if (face.status === "marked") {
        playSuccessChime();
        const subjectTag = face.subject ? ` for ${face.subject}` : "";
        updateGateUI(
          "cooldown",
          `Attendance marked${subjectTag} for ${face.name}!`,
          "Marked Present"
        );
        addLiveFeedItem(face.student_id, face.name, `${face.department || ""} • ${face.subject || ""}`, "Present", "badge-success");
        Toast.show(`Attendance Marked: ${face.name} (${face.student_id}) - ${face.subject || ""}`, "success");
        // Also refresh dashboard stats in background
        if (window.DashboardController) {
          DashboardController.refreshStats();
        }
      } else if (face.status === "wrong_class") {
        updateGateUI(
          "wrong-class",
          face.message || `Student belongs to another class/branch!`,
          "Wrong Class"
        );
        addLiveFeedItem(face.student_id, face.name, `${face.department || ""} (${face.semester || ""})`, "Wrong Class", "badge-danger");
      } else if (face.status === "already_marked") {
        const subjectTag = face.subject ? ` in ${face.subject}` : "";
        updateGateUI(
          "cooldown",
          `${face.name} already marked today${subjectTag}!`,
          "Already Present"
        );
      } else if (face.status === "cooldown") {
        updateGateUI(
          "cooldown",
          `Please wait... Cooldown buffer active for ${face.name}`,
          "Buffer Active"
        );
      } else if (face.status === "unknown") {
        updateGateUI(
          "idle",
          "Unknown Face Detected - Access Denied / Not Registered",
          "Unknown"
        );
      }
    });
  };

  const drawFaceBox = (face) => {
    if (!face.box) return;
    const { x, y, width, height } = face.box;

    let strokeColor = "#ef4444"; // red default (unknown)
    let label = "Unknown Face";
    let sublabel = "Not Registered";

    if (face.status === "marked") {
      strokeColor = "#10b981"; // emerald green
      label = face.name || "Student";
      sublabel = `ID: ${face.student_id} | ${face.subject || "Present"}`;
    } else if (face.status === "wrong_class") {
      strokeColor = "#f59e0b"; // amber / warning
      label = `${face.name || "Student"} [Wrong Class]`;
      sublabel = `Enrolled: ${face.department || ""} (${face.semester || ""})`;
    } else if (face.status === "already_marked") {
      strokeColor = "#f59e0b"; // amber
      label = face.name || "Student";
      sublabel = `ID: ${face.student_id} | Already Marked (${face.subject || ""})`;
    } else if (face.status === "cooldown") {
      strokeColor = "#3b82f6"; // blue
      label = face.name || "Student";
      sublabel = `Cooldown Buffer Active`;
    }

    ctx.save();
    ctx.lineWidth = 3;
    ctx.strokeStyle = strokeColor;

    // Draw styled bounding box with rounded aesthetic
    ctx.beginPath();
    if (typeof ctx.roundRect === "function") {
      ctx.roundRect(x, y, width, height, 8);
    } else {
      ctx.rect(x, y, width, height);
    }
    ctx.stroke();

    // Draw label pill above box
    const pillHeight = 24;
    ctx.fillStyle = strokeColor;
    ctx.font = "bold 13px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
    const textWidth = Math.max(ctx.measureText(label).width, ctx.measureText(sublabel).width) + 16;
    const pillY = Math.max(0, y - pillHeight - 4);

    ctx.beginPath();
    if (typeof ctx.roundRect === "function") {
      ctx.roundRect(x, pillY, textWidth, pillHeight, 4);
    } else {
      ctx.rect(x, pillY, textWidth, pillHeight);
    }
    ctx.fill();

    // Label text
    ctx.fillStyle = "#ffffff";
    ctx.fillText(label, x + 8, pillY + 16);

    ctx.restore();
  };

  const updateGateUI = (status, message, badgeText) => {
    if (!gateBannerEl) return;
    gateBannerEl.className = `gate-banner ${status}`;
    if (gateStatusTextEl) gateStatusTextEl.textContent = message;
    if (gateBadgeEl) gateBadgeEl.textContent = badgeText;
  };

  const addLiveFeedItem = (studentId, name, metaText, status, badgeClass = "badge-success") => {
    if (!liveFeedEl) return;

    // Remove empty placeholder if any
    const emptyEl = liveFeedEl.querySelector(".empty-feed");
    if (emptyEl) emptyEl.remove();

    const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

    const item = document.createElement("li");
    item.className = "feed-item";
    item.innerHTML = `
      <div class="feed-info">
        <span class="feed-name">${name}</span>
        <span class="feed-meta">${studentId} • ${metaText || "Student"} • ${timeStr}</span>
      </div>
      <span class="badge ${badgeClass}">${status}</span>
    `;

    liveFeedEl.insertBefore(item, liveFeedEl.firstChild);

    // Keep max 20 items in live feed
    if (liveFeedEl.children.length > 20) {
      liveFeedEl.removeChild(liveFeedEl.lastChild);
    }
  };

  return {
    init,
    startCamera,
    stopCamera,
    loadSettings,
  };
})();

// Attach to window so other scripts and DOM handlers can invoke it
window.CameraController = CameraController;
