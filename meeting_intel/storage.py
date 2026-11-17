from __future__ import annotations

import builtins
import re
import shutil
import uuid
from pathlib import Path

from .schemas import Meeting

_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class InvalidMeetingId(ValueError):
    """Raised for ids that could escape the data directory (``..``, slashes, ...)."""


def _check_id(meeting_id: str) -> str:
    if not _SAFE_ID.fullmatch(meeting_id):
        raise InvalidMeetingId(f"invalid meeting id: {meeting_id!r}")
    return meeting_id


class MeetingStore:
    """Stores one folder per meeting: audio file + meeting.json."""

    def __init__(self, data_dir: Path):
        self.root = Path(data_dir) / "meetings"
        self.root.mkdir(parents=True, exist_ok=True)

    def new_id(self) -> str:
        return uuid.uuid4().hex[:12]

    def dir(self, meeting_id: str) -> Path:
        d = self.root / _check_id(meeting_id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save(self, meeting: Meeting) -> None:
        # write-then-rename so a crash never leaves a half-written meeting.json behind
        target = self.dir(meeting.id) / "meeting.json"
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(meeting.model_dump_json(indent=2), encoding="utf-8")
        tmp.replace(target)

    def load(self, meeting_id: str) -> Meeting:
        try:
            p = self.root / _check_id(meeting_id) / "meeting.json"
        except InvalidMeetingId as e:
            raise FileNotFoundError(meeting_id) from e
        if not p.exists():
            raise FileNotFoundError(meeting_id)
        return Meeting.model_validate_json(p.read_text(encoding="utf-8"))

    def list(self) -> builtins.list[Meeting]:
        items = []
        for p in self.root.glob("*/meeting.json"):
            try:
                items.append(Meeting.model_validate_json(p.read_text(encoding="utf-8")))
            except Exception:  # a corrupt file must not break the listing
                continue
        return sorted(items, key=lambda m: m.created_at, reverse=True)

    def delete(self, meeting_id: str) -> None:
        try:
            target = self.root / _check_id(meeting_id)
        except InvalidMeetingId:
            return
        shutil.rmtree(target, ignore_errors=True)

    def recover_interrupted(self) -> builtins.list[str]:
        """Mark meetings left in 'uploaded'/'processing' (server stopped mid-job) as failed."""
        fixed = []
        for m in self.list():
            if m.status in ("uploaded", "processing"):
                m.status, m.error = "failed", "Interrupted: the server stopped before processing finished."
                self.save(m)
                fixed.append(m.id)
        return fixed
