"""LLM engine — Ollama / Groq / Mistral adapters behind a single interface."""
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any

from renamer.watcher import FileRecord

_PROMPT_TEMPLATE = """You are a file organization assistant. Given a list of files, propose better names and folder locations.

Files (JSON):
{files}

Rules:
- Use snake_case for filenames
- Keep extensions unchanged
- Group related files into subfolders
- Return ONLY valid JSON: [{{"original": "...", "new_name": "...", "new_folder": "...", "confidence": 0.0-1.0}}]
"""


def _build_prompt(records: list[FileRecord]) -> str:
    data = [{"path": r.path, "type": r.event_type, "size": r.size} for r in records]
    return _PROMPT_TEMPLATE.format(files=json.dumps(data, indent=2))


def _parse_response(text: str) -> list[dict[str, Any]]:
    start, end = text.find("["), text.rfind("]") + 1
    if start == -1 or end == 0:
        return []
    return json.loads(text[start:end])  # type: ignore[no-any-return]


class BaseLLM(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str: ...

    def analyze(self, records: list[FileRecord]) -> list[dict[str, Any]]:
        return _parse_response(self.complete(_build_prompt(records)))


class OllamaLLM(BaseLLM):
    def __init__(self, model: str = "llama3.2", host: str | None = None) -> None:
        import ollama  # type: ignore[import-untyped]

        self._client = ollama.Client(host=host or os.getenv("OLLAMA_HOST", "http://localhost:11434"))
        self._model = model

    def complete(self, prompt: str) -> str:
        resp = self._client.chat(model=self._model, messages=[{"role": "user", "content": prompt}])
        return resp["message"]["content"]


class GroqLLM(BaseLLM):
    def __init__(self, model: str = "llama3-8b-8192") -> None:
        from groq import Groq  # type: ignore[import-untyped]

        self._client = Groq(api_key=os.environ["GROQ_API_KEY"])
        self._model = model

    def complete(self, prompt: str) -> str:
        resp = self._client.chat.completions.create(
            model=self._model, messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content or ""


class MistralLLM(BaseLLM):
    def __init__(self, model: str = "mistral-small-latest") -> None:
        from mistralai import Mistral  # type: ignore[import-untyped]

        self._client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
        self._model = model

    def complete(self, prompt: str) -> str:
        resp = self._client.chat.complete(
            model=self._model, messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content or ""


def get_llm(backend: str = "ollama", **kwargs: Any) -> BaseLLM:
    match backend:
        case "groq":
            return GroqLLM(**kwargs)
        case "mistral":
            return MistralLLM(**kwargs)
        case _:
            return OllamaLLM(**kwargs)
