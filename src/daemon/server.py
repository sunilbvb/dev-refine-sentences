"""Resident background daemon for sub-5 millisecond sentence refinement.

100% Python Standard Library.
"""

import os
import sys
import json
import socket
import signal
import threading
from pathlib import Path
from typing import Optional

from refiner import RefinerManager
from clipboard import ClipboardManager
from injector import KeyInjector
from config import ConfigManager
from history import HistoryManager
from ui import RefinePopup


SOCKET_PATH = Path.home() / ".config" / "refine_tool" / "daemon.sock"


class RefineDaemon:
    """Resident UNIX domain socket server keeping models, regexes, and UI warm in memory."""

    def __init__(self):
        self.config_mgr = ConfigManager()
        self.history_mgr = HistoryManager()
        self.refiner_mgr = RefinerManager(config_manager=self.config_mgr)
        self.clipboard = ClipboardManager()
        self.injector = KeyInjector()
        self.running = False

    def start(self) -> None:
        """Start the background resident daemon."""
        SOCKET_PATH.parent.mkdir(parents=True, exist_ok=True)
        if SOCKET_PATH.exists():
            try:
                # Test if existing socket is active
                test_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                test_sock.connect(str(SOCKET_PATH))
                test_sock.close()
                print("RefineDaemon is already running.")
                return
            except Exception:
                SOCKET_PATH.unlink(missing_ok=True)

        server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server_sock.bind(str(SOCKET_PATH))
        server_sock.listen(5)
        self.running = True

        def handle_shutdown(signum, frame):
            self.running = False
            try:
                server_sock.close()
                SOCKET_PATH.unlink(missing_ok=True)
            except Exception:
                pass
            sys.exit(0)

        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)

        print(f"✨ RefineDaemon started in RAM. Listening on {SOCKET_PATH}")
        print("Sub-5ms zero-latency refinement ready!")

        while self.running:
            try:
                client_sock, _ = server_sock.accept()
                raw_data = client_sock.recv(4096).decode("utf-8").strip()
                if not raw_data:
                    client_sock.close()
                    continue

                req = json.loads(raw_data)
                mode = req.get("mode", "popup")
                tone = req.get("tone", "standard")
                paste = req.get("paste", True)
                text = req.get("text", None)

                # Fast ping check
                if mode == "ping":
                    client_sock.sendall(b"PONG\n")
                    client_sock.close()
                    continue

                # Direct fast text refinement via daemon
                if mode == "refine" and text is not None:
                    refined = self.refiner_mgr.refine(text, tone=tone)
                    resp = json.dumps({
                        "refined": refined,
                        "explanations": self.refiner_mgr.get_last_explanations(),
                        "engine": self.refiner_mgr.get_active_engine().name
                    })
                    client_sock.sendall(resp.encode("utf-8") + b"\n")
                    client_sock.close()
                    continue

                # Immediate ACK so client process exits in <2ms
                client_sock.sendall(b"OK\n")
                client_sock.close()

                # Process request in-memory asynchronously so socket loop never blocks
                threading.Thread(
                    target=self._handle_request,
                    args=(mode, tone, paste),
                    daemon=True,
                ).start()
            except Exception as e:
                pass

    def _handle_request(self, mode: str, tone: str, paste: bool) -> None:
        # Step 1: Capture highlighted text directly via primary selection or Atspi
        raw_text = self.clipboard.get_primary_selection()
        if not raw_text or not raw_text.strip():
            self.injector.simulate_copy()
            raw_text = self.clipboard.get_text()

        if not raw_text or not raw_text.strip():
            self.injector.notify("Sentence Refiner", "Please highlight a sentence first, then press shortcut.")
            return

        raw_text = raw_text.strip()
        active_engine = self.refiner_mgr.get_active_engine()

        # Instant Flash Mode (Sub-5ms)
        if mode == "clipboard" or mode == "flash":
            refined = self.refiner_mgr.refine(raw_text, tone=tone)
            self.clipboard.set_text(refined)
            self.history_mgr.record(raw_text, refined, tone, active_engine.name)
            if paste:
                self.injector.simulate_paste()
                self.injector.play_sound("complete")
            summary_orig = (raw_text[:35] + "...") if len(raw_text) > 35 else raw_text
            summary_ref = (refined[:35] + "...") if len(refined) > 35 else refined
            self.injector.notify("Sentence Refined ✨", f"\"{summary_orig}\" ➔ \"{summary_ref}\"")
            return

        # Popup Mode
        initial_refined = self.refiner_mgr.refine(raw_text, tone=tone)
        history_items = self.history_mgr.get_history(limit=10)

        # Available engines
        seen = set()
        available_names = []
        name_to_key = {}
        for key, eng in self.refiner_mgr.engines.items():
            if key in ["chatgpt", "anthropic"]:
                continue
            if eng.is_available() and eng.name not in seen:
                seen.add(eng.name)
                available_names.append(eng.name)
                name_to_key[eng.name] = key

        current_engine = active_engine

        def on_tone_change(t: str) -> str:
            return current_engine.refine(raw_text, tone=t)

        def on_engine_change(display_name: str) -> str:
            nonlocal current_engine
            k = name_to_key.get(display_name)
            if k and k in self.refiner_mgr.engines:
                current_engine = self.refiner_mgr.engines[k]
            return current_engine.refine(raw_text, tone=popup.selected_tone)

        def on_apply(final_text: str) -> None:
            self.clipboard.set_text(final_text)
            self.history_mgr.record(raw_text, final_text, popup.selected_tone, current_engine.name)
            if paste:
                self.injector.simulate_paste()
                self.injector.play_sound("complete")

        popup = RefinePopup(
            original_text=raw_text,
            initial_refined_text=initial_refined,
            engine_name=active_engine.name,
            on_tone_change=on_tone_change,
            on_apply=on_apply,
            history_items=history_items,
            available_engines=available_names,
            on_engine_change=on_engine_change,
            config_manager=self.config_mgr,
            get_explanations=self.refiner_mgr.get_last_explanations,
        )
        popup.show()


def run_daemon() -> None:
    daemon = RefineDaemon()
    daemon.start()


if __name__ == "__main__":
    run_daemon()
