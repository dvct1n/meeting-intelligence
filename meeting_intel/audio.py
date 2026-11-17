from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def to_wav(src: Path, dst: Path | None = None) -> Path:
    """Convert any audio/video file to 16 kHz mono WAV (needs ffmpeg on PATH)."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found. Install it (e.g. `apt install ffmpeg` / `brew install ffmpeg`).")
    dst = dst or src.with_suffix(".16k.wav")
    cmd = ["ffmpeg", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(dst)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {proc.stderr[-500:]}")
    return dst
