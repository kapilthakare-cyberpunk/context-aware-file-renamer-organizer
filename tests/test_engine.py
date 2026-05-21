"""Basic unit tests."""
from pathlib import Path
from unittest.mock import MagicMock

from renamer.engine import Proposal, build_proposals, apply, undo


def _proposal(tmp_path: Path) -> dict:
    f = tmp_path / "old_file.txt"
    f.write_text("hello")
    return {"original": str(f), "new_name": "new_file.txt", "new_folder": ".", "confidence": 0.9}


def test_build_proposals_filters_low_confidence(tmp_path: Path) -> None:
    item = _proposal(tmp_path)
    low = {**item, "confidence": 0.3}
    proposals = build_proposals([item, low])
    assert len(proposals) == 1
    assert proposals[0].new_name == "new_file.txt"


def test_apply_dry_run(tmp_path: Path) -> None:
    proposals = build_proposals([_proposal(tmp_path)])
    results = apply(proposals, dry_run=True)
    assert all(ok for _, ok in results)
    # File should NOT have moved
    assert (tmp_path / "old_file.txt").exists()


def test_apply_and_undo(tmp_path: Path) -> None:
    proposals = build_proposals([_proposal(tmp_path)])
    apply(proposals, dry_run=False)
    assert not (tmp_path / "old_file.txt").exists()
    undo(proposals)
    assert (tmp_path / "old_file.txt").exists()
