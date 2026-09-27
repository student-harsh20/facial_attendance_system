import time
from typing import Dict, Tuple, Optional
from backend.config import settings


class CooldownManager:
    """
    Manages recognition cooldown and buffer for entry-gate workflow.
    - Prevents repeated recognition/spamming of the same student.
    - Configurable duration via settings.RECOGNITION_COOLDOWN_SECONDS.
    - Does NOT block different students from being recognized.
    """

    def __init__(self, cooldown_seconds: Optional[int] = None):
        self.cooldown_seconds = cooldown_seconds or settings.RECOGNITION_COOLDOWN_SECONDS
        # student_id -> last_marked_timestamp
        self._last_marked: Dict[str, float] = {}
        # Gate state: tracks the last student marked and timestamp
        self._last_marked_student_id: Optional[str] = None
        self._last_marked_student_name: Optional[str] = None
        self._last_marked_time: float = 0.0

    def update_cooldown_duration(self, seconds: int):
        """Update cooldown duration dynamically if changed."""
        self.cooldown_seconds = max(1, seconds)
        settings.RECOGNITION_COOLDOWN_SECONDS = self.cooldown_seconds

    def mark_success(self, student_id: str, student_name: str):
        """Record successful attendance mark for a student."""
        now = time.time()
        self._last_marked[student_id] = now
        self._last_marked_student_id = student_id
        self._last_marked_student_name = student_name
        self._last_marked_time = now

    def is_in_cooldown(self, student_id: str) -> Tuple[bool, float]:
        """
        Check if a specific student is in cooldown.
        Returns:
            (in_cooldown: bool, seconds_remaining: float)
        """
        now = time.time()
        last_time = self._last_marked.get(student_id)
        if last_time is None:
            return False, 0.0

        elapsed = now - last_time
        if elapsed < self.cooldown_seconds:
            remaining = round(self.cooldown_seconds - elapsed, 1)
            return True, remaining

        return False, 0.0

    def get_gate_status(self) -> dict:
        """
        Get current gate status message for display on the camera interface.
        """
        now = time.time()
        if self._last_marked_time == 0:
            return {
                "gate_status": "ready",
                "message": "Ready for student",
                "cooldown_remaining": 0.0,
                "recent_student": None
            }

        elapsed = now - self._last_marked_time
        if elapsed < self.cooldown_seconds:
            remaining = round(self.cooldown_seconds - elapsed, 1)
            return {
                "gate_status": "cooldown",
                "message": f"Attendance marked for {self._last_marked_student_name}. Please wait {remaining}s...",
                "cooldown_remaining": remaining,
                "recent_student": self._last_marked_student_name
            }

        return {
            "gate_status": "ready",
            "message": "Ready for next student",
            "cooldown_remaining": 0.0,
            "recent_student": self._last_marked_student_name
        }

    def clear(self):
        """Clear all cooldown records."""
        self._last_marked.clear()
        self._last_marked_student_id = None
        self._last_marked_student_name = None
        self._last_marked_time = 0.0


# Global singleton instance
cooldown_manager = CooldownManager()
