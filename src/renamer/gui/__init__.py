"""Floating always-on-top GUI — polished dark minimal design."""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from dotenv import load_dotenv

from renamer.engine import Proposal, apply, build_proposals, undo
from renamer.llm import get_llm
from renamer.watcher import FolderWatcher

load_dotenv()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── Tokens ────────────────────────────────────────────────────────────────────
_BG      = "#0F0F0F"
_SURFACE = "#1A1A1A"
_CARD    = "#222222"
_BORDER  = "#2E2E2E"
_GOLD    = "#D4AF37"
_GOLD_DIM= "#8A6F1E"
_TEXT    = "#F0F0F0"
_MUTED   = "#666666"
_SUCCESS = "#4CAF50"
_DANGER  = "#E05252"
_FONT    = "Inter"


def _label(parent: ctk.CTkBaseClass, text: str, size: int = 12,
           weight: str = "normal", color: str = _MUTED, **kw: object) -> ctk.CTkLabel:
    return ctk.CTkLabel(parent, text=text, font=(_FONT, size, weight),
                        text_color=color, **kw)  # type: ignore[arg-type]


def _btn(parent: ctk.CTkBaseClass, text: str, cmd: object,
         fg: str = _CARD, hover: str = _GOLD, text_color: str = _TEXT,
         width: int = 0, **kw: object) -> ctk.CTkButton:
    return ctk.CTkButton(
        parent, text=text, command=cmd,  # type: ignore[arg-type]
        font=(_FONT, 12), fg_color=fg, hover_color=hover,
        text_color=text_color, cursor="hand2",
        border_width=1, border_color=_BORDER,
        corner_radius=6, width=width, **kw,  # type: ignore[arg-type]
    )


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Renamer")
        self.geometry("400x620")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(fg_color=_BG)

        self._proposals: list[Proposal] = []
        self._applied: list[Proposal] = []
        self._watching = False

        self._build()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        # ── Titlebar ──────────────────────────────────────────────────────────
        bar = ctk.CTkFrame(self, fg_color=_SURFACE, corner_radius=0, height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        _label(bar, "◈  File Renamer", 14, "bold", _GOLD).pack(side="left", padx=14)
        self._dot = _label(bar, "●", 10, color=_MUTED)
        self._dot.pack(side="right", padx=14)

        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=14, pady=10)

        # ── LLM row ───────────────────────────────────────────────────────────
        row = ctk.CTkFrame(outer, fg_color=_CARD, corner_radius=8)
        row.pack(fill="x", pady=(0, 8))
        _label(row, "LLM", 11, color=_MUTED).pack(side="left", padx=12, pady=10)
        self._llm_var = ctk.StringVar(value=os.getenv("LLM_BACKEND", "ollama"))
        ctk.CTkSegmentedButton(
            row, values=["ollama", "groq", "mistral"],
            variable=self._llm_var, font=(_FONT, 11),
            selected_color=_GOLD, selected_hover_color=_GOLD_DIM,
            unselected_color=_SURFACE, fg_color=_SURFACE,
            text_color=_TEXT, corner_radius=6,
        ).pack(side="left", padx=8, pady=8)

        # ── Watch hours ───────────────────────────────────────────────────────
        row2 = ctk.CTkFrame(outer, fg_color=_CARD, corner_radius=8)
        row2.pack(fill="x", pady=(0, 8))
        _label(row2, "Watch (hours)", 11).pack(side="left", padx=12, pady=10)
        self._hours_var = ctk.StringVar(value=os.getenv("WATCH_INTERVAL_HOURS", "4"))
        ctk.CTkEntry(
            row2, textvariable=self._hours_var, width=56,
            font=(_FONT, 12), fg_color=_SURFACE,
            border_color=_BORDER, text_color=_TEXT, corner_radius=6,
        ).pack(side="right", padx=12, pady=8)

        # ── Folders ───────────────────────────────────────────────────────────
        fhdr = ctk.CTkFrame(outer, fg_color="transparent")
        fhdr.pack(fill="x", pady=(0, 4))
        _label(fhdr, "WATCHED FOLDERS", 10, color=_MUTED).pack(side="left")
        _btn(fhdr, "+ Add", self._add_folder, width=60,
             fg=_SURFACE, hover=_GOLD).pack(side="right")

        self._paths_box = ctk.CTkTextbox(
            outer, height=56, font=(_FONT, 11),
            fg_color=_CARD, text_color=_TEXT,
            border_color=_BORDER, border_width=1, corner_radius=8,
        )
        self._paths_box.pack(fill="x", pady=(0, 8))
        self._paths_box.insert("0.0", os.getenv("WATCH_PATHS", "~/Downloads"))

        # ── Status bar ────────────────────────────────────────────────────────
        status_frame = ctk.CTkFrame(outer, fg_color=_CARD, corner_radius=8, height=32)
        status_frame.pack(fill="x", pady=(0, 4))
        status_frame.pack_propagate(False)
        self._status_var = ctk.StringVar(value="Ready")
        self._status_lbl = _label(status_frame, "", 11, color=_MUTED)
        self._status_lbl.configure(textvariable=self._status_var)
        self._status_lbl.pack(side="left", padx=10)

        # ── Progress ──────────────────────────────────────────────────────────
        self._progress = ctk.CTkProgressBar(
            outer, fg_color=_CARD, progress_color=_GOLD,
            corner_radius=4, height=4,
        )
        self._progress.pack(fill="x", pady=(0, 8))
        self._progress.set(0)

        # ── Proposals ─────────────────────────────────────────────────────────
        _label(outer, "PROPOSALS", 10, color=_MUTED).pack(anchor="w", pady=(0, 4))
        self._proposals_box = ctk.CTkTextbox(
            outer, height=160, font=(_FONT, 11),
            fg_color=_CARD, text_color=_TEXT,
            border_color=_BORDER, border_width=1, corner_radius=8,
            state="disabled",
        )
        self._proposals_box.pack(fill="x", pady=(0, 10))

        # ── Dry-run toggle ────────────────────────────────────────────────────
        self._dry_run = ctk.BooleanVar(value=os.getenv("DRY_RUN", "true").lower() == "true")
        ctk.CTkCheckBox(
            outer, text="Dry run  (preview only — no files moved)",
            variable=self._dry_run,
            font=(_FONT, 11), text_color=_MUTED,
            checkmark_color=_GOLD, fg_color=_GOLD,
            hover_color=_GOLD_DIM, cursor="hand2",
            border_color=_BORDER,
        ).pack(anchor="w", pady=(0, 10))

        # ── Action buttons ────────────────────────────────────────────────────
        actions = ctk.CTkFrame(outer, fg_color="transparent")
        actions.pack(fill="x")
        actions.columnconfigure((0, 1, 2), weight=1)

        self._start_btn = _btn(
            actions, "▶  Start", self._start_watching,
            fg=_GOLD, hover=_GOLD_DIM, text_color="#000000",
        )
        self._start_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self._apply_btn = _btn(actions, "✓  Apply", self._apply_proposals, fg=_CARD)
        self._apply_btn.configure(state="disabled")
        self._apply_btn.grid(row=0, column=1, sticky="ew", padx=4)

        self._undo_btn = _btn(actions, "↩  Undo", self._undo_proposals,
                              fg=_CARD, hover=_DANGER)
        self._undo_btn.configure(state="disabled")
        self._undo_btn.grid(row=0, column=2, sticky="ew", padx=(4, 0))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_status(self, msg: str, color: str = _MUTED) -> None:
        self._status_var.set(msg)
        self._status_lbl.configure(text_color=color)

    def _set_dot(self, color: str) -> None:
        self._dot.configure(text_color=color)

    def _write_proposals(self, lines: list[str]) -> None:
        self._proposals_box.configure(state="normal")
        self._proposals_box.delete("0.0", "end")
        for line in lines:
            self._proposals_box.insert("end", line + "\n")
        self._proposals_box.configure(state="disabled")

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _add_folder(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            cur = self._paths_box.get("0.0", "end").strip()
            self._paths_box.delete("0.0", "end")
            self._paths_box.insert("0.0", f"{cur},{folder}" if cur else folder)

    def _start_watching(self) -> None:
        raw = self._paths_box.get("0.0", "end").strip()
        paths = [p.strip() for p in raw.split(",") if p.strip()]
        if not paths:
            self._set_status("No folders selected.", _DANGER)
            return

        try:
            hours = float(self._hours_var.get() or "4")
        except ValueError:
            self._set_status("Invalid hours value.", _DANGER)
            return

        self._proposals = []
        self._write_proposals(["Waiting for file events…"])
        self._start_btn.configure(state="disabled")
        self._apply_btn.configure(state="disabled")
        self._undo_btn.configure(state="disabled")
        self._progress.set(0)
        self._set_dot(_GOLD)
        self._set_status(f"Watching {len(paths)} folder(s)…", _GOLD)

        threading.Thread(target=self._watch_worker, args=(paths, hours), daemon=True).start()
        self._poll_progress(hours)

    def _watch_worker(self, paths: list[str], hours: float) -> None:
        watcher = FolderWatcher(paths)
        records = watcher.watch_for(hours)
        self.after(0, lambda: self._set_status(f"Analyzing {len(records)} events…", _GOLD))

        try:
            llm = get_llm(self._llm_var.get())
            raw = llm.analyze(records)
        except Exception as e:
            self.after(0, lambda: self._set_status(f"LLM error: {e}", _DANGER))
            self.after(0, lambda: self._set_dot(_DANGER))
            self.after(0, lambda: self._start_btn.configure(state="normal"))
            return

        threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))
        self._proposals = build_proposals(raw, threshold)
        self.after(0, self._show_proposals)

    def _poll_progress(self, total_hours: float) -> None:
        start = time.time()
        total_secs = total_hours * 3600

        def tick() -> None:
            frac = min((time.time() - start) / total_secs, 1.0)
            self._progress.set(frac)
            if frac < 1.0:
                self.after(1000, tick)

        tick()

    def _show_proposals(self) -> None:
        self._progress.set(1)
        self._start_btn.configure(state="normal")
        if self._proposals:
            self._write_proposals([f"  {p}" for p in self._proposals])
            self._apply_btn.configure(state="normal")
            self._set_status(f"{len(self._proposals)} proposals ready.", _SUCCESS)
            self._set_dot(_SUCCESS)
        else:
            self._write_proposals(["No proposals above confidence threshold."])
            self._set_status("Done — nothing to rename.", _MUTED)
            self._set_dot(_MUTED)

    def _apply_proposals(self) -> None:
        dry = self._dry_run.get()
        results = apply(self._proposals, dry_run=dry)
        ok = sum(1 for _, s in results if s)
        if not dry:
            self._applied = self._proposals[:]
            self._undo_btn.configure(state="normal")
            self._apply_btn.configure(state="disabled")
            self._set_status(f"Applied {ok}/{len(results)} renames.", _SUCCESS)
        else:
            self._set_status(f"Preview: {ok}/{len(results)} would rename.", _GOLD)

    def _undo_proposals(self) -> None:
        undo(self._applied)
        self._set_status("Undo complete.", _MUTED)
        self._set_dot(_MUTED)
        self._undo_btn.configure(state="disabled")
        self._apply_btn.configure(state="normal")


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
