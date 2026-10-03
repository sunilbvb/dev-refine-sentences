"""Refinement history and undo buffer manager.

100% Python Standard Library.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional


class HistoryManager:
    """Maintains persistent log of refined sentences for undo and inspection."""

    def __init__(self, history_dir: Optional[Path] = None, max_entries: int = 50):
        if history_dir is None:
            self.history_dir = Path.home() / ".config" / "refine_tool"
        else:
            self.history_dir = Path(history_dir)

        self.history_file = self.history_dir / "history.json"
        self.max_entries = max_entries
        self._ensure_file()

    def _ensure_file(self) -> None:
        try:
            self.history_dir.mkdir(parents=True, exist_ok=True)
            if not self.history_file.exists():
                with open(self.history_file, "w", encoding="utf-8") as f:
                    json.dump([], f)
        except Exception:
            pass

    def record(self, original: str, refined: str, tone: str, engine: str) -> None:
        """Record a refinement operation into history."""
        if not original.strip():
            return

        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "original": original.strip(),
            "refined": refined.strip(),
            "tone": tone,
            "engine": engine,
        }

        history = self.get_history(limit=self.max_entries)
        # Avoid duplicate top entry
        if history and history[0].get("original") == entry["original"] and history[0].get("refined") == entry["refined"]:
            return

        history.insert(0, entry)
        history = history[:self.max_entries]

        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent refinement entries."""
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data[:limit] if isinstance(data, list) else []
        except Exception:
            return []

    def get_last(self) -> Optional[Dict[str, Any]]:
        """Retrieve the most recent refinement entry."""
        hist = self.get_history(limit=1)
        return hist[0] if hist else None

    def clear(self) -> None:
        """Clear all stored history."""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump([], f)
        except Exception:
            pass
