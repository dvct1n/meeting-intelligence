"""End-to-end orchestration. Heavy steps are injected so they can be swapped or faked in tests."""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Callable

from .align import assign_speakers, merge_utterances, relabel_speakers
from .analyze import analyze_meeting
from .asr import transcribe
from .audio import to_wav
from .config import Settings
from .diarize import diarize
from .embed import Embedder
from .index import MeetingIndex
from .llm import LLM
from .schemas import Meeting, Segment, SpeakerTurn
from .segment import chunk_utterances
from .storage import MeetingStore

log = logging.getLogger(__name__)
_GPU_LOCK = threading.Lock()  # process one recording at a time


class MeetingPipeline:
    def __init__(
        self,
        settings: Settings,
        store: MeetingStore,
        index: MeetingIndex,
        llm: LLM,
        embedder: Embedder,
        audio_fn: Callable[[Path], Path] = to_wav,
        asr_fn: Callable[[Path], list[Segment]] | None = None,
        diarize_fn: Callable[[Path], list[SpeakerTurn]] | None = None,
    ):
        self.s, self.store, self.index, self.llm, self.embedder = settings, store, index, llm, embedder
        self.audio_fn = audio_fn
        self.asr_fn = asr_fn or (lambda p: transcribe(p, settings.whisper_model, settings.whisper_language))
        self.diarize_fn = diarize_fn or (lambda p: diarize(p, settings.diarization_model, settings.hf_token))

    def _set(self, meeting: Meeting, status: str, error: str | None = None) -> None:
        meeting.status, meeting.error = status, error  # type: ignore[assignment]
        self.store.save(meeting)

    def process(self, meeting_id: str) -> Meeting:
        meeting = self.store.load(meeting_id)
        with _GPU_LOCK:
            try:
                self._set(meeting, "processing")
                audio = self.store.dir(meeting_id) / meeting.filename
                wav = self.audio_fn(audio)

                log.info("[%s] transcribing", meeting_id)
                segments = self.asr_fn(wav)

                turns: list[SpeakerTurn] = []
                if self.s.diarize:
                    log.info("[%s] diarizing", meeting_id)
                    try:
                        turns = self.diarize_fn(wav)
                    except Exception as e:  # keep going with a single speaker
                        log.warning("[%s] diarization failed (%s); using one speaker", meeting_id, e)

                utts = relabel_speakers(merge_utterances(assign_speakers(segments, turns)))
                meeting.utterances = utts
                meeting.duration = utts[-1].end if utts else 0.0

                log.info("[%s] segmenting", meeting_id)
                meeting.chunks = chunk_utterances(
                    utts, self.embedder, max_chars=self.s.chunk_max_chars, min_chars=self.s.chunk_min_chars
                )

                log.info("[%s] analysing with LLM", meeting_id)
                meeting.analysis = analyze_meeting(self.llm, utts, meeting.chunks)

                log.info("[%s] indexing", meeting_id)
                self.index.upsert_chunks(meeting_id, meeting.chunks)
                self._set(meeting, "done")
            except Exception as e:
                log.exception("[%s] pipeline failed", meeting_id)
                self._set(meeting, "failed", f"{type(e).__name__}: {e}")
        return meeting
