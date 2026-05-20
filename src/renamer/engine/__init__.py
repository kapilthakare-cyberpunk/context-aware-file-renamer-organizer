"""Rename & reorganize engine — applies LLM proposals safely."""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Proposal:
    original: Path
    new_name: str
    new_folder: str
    confidence: float

    @property
    def destination(self) -> Path:
        return self.original.parent / self.new_folder / self.new_name

    def __str__(self) -> str:
        return f"{self.original.name} → {self.new_folder}/{self.new_name} ({self.confidence:.0%})"


def build_proposals(
    llm_output: list[dict[str, Any]],
    confidence_threshold: float = 0.75,
) -> list[Proposal]:
    proposals = []
    for item in llm_output:
        p = Proposal(
            original=Path(item["original"]),
            new_name=item.get("new_name", Path(item["original"]).name),
            new_folder=item.get("new_folder", "."),
            confidence=float(item.get("confidence", 0)),
        )
        if p.confidence >= confidence_threshold and p.original.exists():
            proposals.append(p)
    return proposals


def apply(proposals: list[Proposal], dry_run: bool = True) -> list[tuple[Proposal, bool]]:
    """Apply proposals. Returns list of (proposal, success) tuples."""
    results = []
    for p in proposals:
        if dry_run:
            results.append((p, True))
            continue
        try:
            p.destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p.original), str(p.destination))
            results.append((p, True))
        except OSError:
            results.append((p, False))
    return results


def undo(proposals: list[Proposal]) -> None:
    """Reverse applied proposals (move files back)."""
    for p in proposals:
        if p.destination.exists():
            shutil.move(str(p.destination), str(p.original))
