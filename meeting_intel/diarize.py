"""Speaker diarization with pyannote.audio ("who spoke when")."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .schemas import SpeakerTurn


@lru_cache(maxsize=1)
def _load_pipeline(model_name: str, hf_token: str | None):
    import torch
    from pyannote.audio import Pipeline

    try:  # pyannote.audio 3.x
        pipe = Pipeline.from_pretrained(model_name, use_auth_token=hf_token)
    except TypeError:  # pyannote.audio 4.x renamed the argument
        pipe = Pipeline.from_pretrained(model_name, token=hf_token)
    if pipe is None:
        raise RuntimeError(
            "Could not load the diarization model. Set HF_TOKEN and accept the model terms on "
            f"https://huggingface.co/{model_name}"
        )
    if torch.cuda.is_available():
        pipe.to(torch.device("cuda"))
    return pipe


def diarize(
    audio_path: Path,
    model_name: str,
    hf_token: str | None,
    num_speakers: int | None = None,
) -> list[SpeakerTurn]:
    pipe = _load_pipeline(model_name, hf_token)
    result = pipe(str(audio_path), num_speakers=num_speakers)
    annotation = getattr(result, "speaker_diarization", result)  # 4.x wraps the annotation
    return [
        SpeakerTurn(start=float(turn.start), end=float(turn.end), speaker=str(speaker))
        for turn, _, speaker in annotation.itertracks(yield_label=True)
    ]
