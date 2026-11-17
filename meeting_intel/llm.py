"""Thin LLM wrapper. Works with any OpenAI-compatible server (OpenAI, Ollama, vLLM, Groq...)
or with Anthropic. Clients are created lazily so importing this module is cheap."""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Callable, Protocol, TypeVar

from .config import Settings

log = logging.getLogger(__name__)
T = TypeVar("T")


def with_retries(
    fn: Callable[[], T],
    attempts: int = 3,
    base_delay: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call ``fn``; on failure wait 1 s, 2 s, 4 s... and try again (rate limits, flaky network)."""
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as e:
            if attempt == attempts:
                raise
            delay = base_delay * 2 ** (attempt - 1)
            log.warning("LLM call failed (%s); retry %d/%d in %.1fs", e, attempt, attempts - 1, delay)
            sleep(delay)
    raise AssertionError("unreachable")  # pragma: no cover


class LLM(Protocol):
    def complete(self, system: str, user: str, *, json_mode: bool = False, max_tokens: int = 1500) -> str: ...


class OpenAICompatLLM:
    def __init__(self, model: str, api_key: str | None = None, base_url: str | None = None):
        self.model, self.api_key, self.base_url = model, api_key, base_url
        self._client: Any = None

    def complete(self, system: str, user: str, *, json_mode: bool = False, max_tokens: int = 1500) -> str:
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        kwargs = dict(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
            max_tokens=max_tokens,
        )
        create = self._client.chat.completions.create
        if json_mode:
            try:
                resp = create(response_format={"type": "json_object"}, **kwargs)
            except Exception:  # some OpenAI-compatible servers do not support JSON mode
                resp = with_retries(lambda: create(**kwargs))
        else:
            resp = with_retries(lambda: create(**kwargs))
        return resp.choices[0].message.content or ""


class AnthropicLLM:
    def __init__(self, model: str, api_key: str | None = None):
        self.model, self.api_key = model, api_key
        self._client: Any = None

    def complete(self, system: str, user: str, *, json_mode: bool = False, max_tokens: int = 1500) -> str:
        if self._client is None:
            from anthropic import Anthropic

            self._client = Anthropic(api_key=self.api_key)
        resp = with_retries(
            lambda: self._client.messages.create(
                model=self.model, max_tokens=max_tokens, temperature=0.2, system=system,
                messages=[{"role": "user", "content": user}],
            )
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


def build_llm(settings: Settings) -> LLM:
    if settings.llm_provider == "anthropic":
        return AnthropicLLM(settings.llm_model, settings.llm_api_key)
    return OpenAICompatLLM(settings.llm_model, settings.llm_api_key, settings.llm_base_url)


def extract_json(text: str) -> dict:
    """Parse a JSON object from an LLM reply, tolerating ```json fences and extra prose."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("no JSON object in LLM reply") from None
        return json.loads(text[start:end + 1])
