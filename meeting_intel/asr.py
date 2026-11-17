"""Speech recognition with Whisper through Hugging Face Transformers."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .schemas import Segment


@lru_cache(maxsize=1)
def _load_asr(model_name: str):
    import torch
    from transformers import pipeline

    use_cuda = torch.cuda.is_available()
    return pipeline(
        "automatic-speech-recognition",
        model=model_name,
        device=0 if use_cuda else -1,
        torch_dtype=torch.float16 if use_cuda else torch.float32,
        chunk_length_s=30,  # long-form audio is processed in 30 s windows
    )


def transcribe(audio_path: Path, model_name: str, language: str | None = None) -> list[Segment]:
    asr = _load_asr(model_name)
    generate_kwargs = {"task": "transcribe"}
    if language:
        generate_kwargs["language"] = language
    out = asr(str(audio_path), return_timestamps=True, generate_kwargs=generate_kwargs)

    segments: list[Segment] = []
    for ch in out.get("chunks", []):
        start, end = ch["timestamp"]
        text = (ch.get("text") or "").strip()
        if start is None or not text:
            continue
        if end is None:  # last chunk can have an open end
            end = start + 1.0
        segments.append(Segment(start=float(start), end=float(end), text=text))
    return segments
