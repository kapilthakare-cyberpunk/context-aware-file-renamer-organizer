"""Folder watcher — collects file events into a context buffer."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event, Thread
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


@dataclass
class FileRecord:
    path: str
    event_type: str  # created | modified | moved | deleted
    timestamp: float = field(default_factory=time.time)
    size: int = 0
    suffix: str = ""

    @classmethod
    def from_event(cls, event: FileSystemEvent) -> "FileRecord":
        p = Path(event.src_path)
        size = p.stat().st_size if p.exists() else 0
        return cls(
            path=event.src_path,
            event_type=event.event_type,
            size=size,
            suffix=p.suffix.lower(),
        )


class _Handler(FileSystemEventHandler):
    def __init__(self, on_event: Callable[[FileRecord], None]) -> None:
        self._on_event = on_event

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._on_event(FileRecord.from_event(event))


class FolderWatcher:
    """Watch one or more folders and accumulate FileRecords."""

    def __init__(self, paths: list[str]) -> None:
        self.paths = [str(Path(p).expanduser()) for p in paths]
        self.records: list[FileRecord] = []
        self._stop = Event()
        self._observer = Observer()

    def start(self) -> None:
        handler = _Handler(self.records.append)
        for p in self.paths:
            self._observer.schedule(handler, p, recursive=True)
        self._observer.start()

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join()

    def snapshot(self) -> list[FileRecord]:
        """Return accumulated records and clear the buffer."""
        records, self.records = self.records[:], []
        return records

    def watch_for(self, hours: float) -> list[FileRecord]:
        """Block for `hours`, then return all collected records."""
        self.start()
        try:
            time.sleep(hours * 3600)
        finally:
            self.stop()
        return self.snapshot()
