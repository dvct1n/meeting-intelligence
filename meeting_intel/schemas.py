from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class Segment(BaseModel):
    """A piece of recognised speech (no speaker yet)."""
    start: float
    end: float
    text: str


class SpeakerTurn(BaseModel):
    """Who spoke when, from diarization."""
    start: float
    end: float
    speaker: str


class Utterance(BaseModel):
    start: float
    end: float
    speaker: str
    text: str


class Chunk(BaseModel):
    """A topic-coherent block of the transcript."""
    id: int
    start: float
    end: float
    speakers: list[str]
    text: str
    summary: str | None = None


class Decision(BaseModel):
    decision: str
    rationale: str | None = None


class ActionItem(BaseModel):
    task: str
    owner: str | None = None
    deadline: str | None = None


class Analysis(BaseModel):
    title: str = "Untitled meeting"
    summary: str = ""
    topics: list[str] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    speaker_summaries: dict[str, str] = Field(default_factory=dict)


class Meeting(BaseModel):
    id: str
    filename: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: Literal["uploaded", "processing", "done", "failed"] = "uploaded"
    error: str | None = None
    duration: float = 0.0
    utterances: list[Utterance] = Field(default_factory=list)
    chunks: list[Chunk] = Field(default_factory=list)
    analysis: Analysis | None = None


class SearchHit(BaseModel):
    meeting_id: str
    chunk_id: int
    score: float
    start: float
    end: float
    speakers: list[str]
    text: str
    summary: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(max_length=1000)
    meeting_id: str | None = None
    limit: int = Field(default=5, ge=1, le=50)
