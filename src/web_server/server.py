"""HTTP server for developer documentation and interactive refinement portal.

100% Python Standard Library.
"""

import http.server
import json
import socket
import os
from pathlib import Path

import urllib.request
from urllib.parse import urlparse

from config import ConfigManager
from config.settings import EDITABLE_SETTINGS, ENGINES, TONES
from daemon import query_daemon_refine
from refiner import RefinerManager

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SOCKET_PATH = Path.home() / ".config" / "refine_tool" / "daemon.sock"


class DocsRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler serving static portal files and API endpoints."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT_ROOT), **kwargs)

    def do_GET(self):
        if self.path in ["/api/status", "/api/server/status"]:
            daemon_active = False
            if SOCKET_PATH.exists():
                try:
                    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                        s.settimeout(0.2)
                        s.connect(str(SOCKET_PATH))
                        s.sendall(json.dumps({"mode": "ping"}).encode("utf-8"))
                        resp = s.recv(1024)
                        daemon_active = resp.strip() == b"PONG"
                except Exception:
                    daemon_active = False

            payload = {
                "status": "online",
                "daemon_active": daemon_active,
                "version": "1.2.0",
                "pid": os.getpid(),
                "port": getattr(self.server, "server_port", 8080),
            }
            self._send_json(payload)
            return

        if self.path == "/api/config":
            self._send_json({
                **ConfigManager().public_settings(),
                "options": {"tones": TONES, "engines": ENGINES},
            }, cors=False)
            return

        if self.path == "/api/ollama/models":
            self._send_json(self._ollama_models(), cors=False)
            return

        # Serve static files from PROJECT_ROOT
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/server/stop":
            self._send_json({"status": "shutting_down", "message": "Web server stopped."})
            import threading
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return

        if self.path == "/api/config":
            self._handle_config_update()
            return

        if self.path == "/api/refine":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
                text = data.get("text", "")
                tone = data.get("tone", "standard")

                # Try daemon first
                res = query_daemon_refine(text, tone=tone)
                if res is None:
                    # In-process fallback
                    mgr = RefinerManager()
                    refined = mgr.refine(text, tone=tone)
                    res = {
                        "refined": refined,
                        "explanations": mgr.get_last_explanations(),
                        "engine": mgr.get_active_engine().name,
                    }
                self._send_json(res)
            except Exception as e:
                self._send_json({"error": str(e)}, status_code=500)
            return

        self.send_error(404, "Not Found")

    def _is_local_origin(self) -> bool:
        """Settings writes must come from this portal itself, not from another website the user
        happens to have open (CSRF / DNS-rebinding guard on a localhost-only server)."""
        origin = self.headers.get("Origin")
        host = (self.headers.get("Host") or "").split(":")[0]
        if host not in ("localhost", "127.0.0.1", "[::1]"):
            return False
        if origin is None:
            return True  # non-browser client (curl, CLI)
        return urlparse(origin).hostname in ("localhost", "127.0.0.1", "::1")

    def _handle_config_update(self) -> None:
        if not self._is_local_origin() or not self.headers.get("Content-Type", "").startswith("application/json"):
            self._send_json({"error": "Forbidden"}, status_code=403, cors=False)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(min(length, 10_000)).decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Body must be a JSON object.")
            unknown = [k for k in data if k not in EDITABLE_SETTINGS]
            if unknown:
                raise ValueError(f"Unknown setting(s): {', '.join(unknown)}")
            cfg = ConfigManager()
            saved = {k: cfg.set_setting(k, v) for k, v in data.items()}
            self._send_json({"saved": saved, **cfg.public_settings()}, cors=False)
        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": str(exc)}, status_code=400, cors=False)

    @staticmethod
    def _ollama_models() -> dict:
        try:
            with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=1.5) as resp:
                tags = json.loads(resp.read().decode("utf-8")).get("models", [])
            return {"available": True, "models": [
                {"name": m["name"], "size_gb": round(m.get("size", 0) / 1e9, 1)} for m in tags
            ]}
        except Exception:
            return {"available": False, "models": []}

    def _send_json(self, data: dict, status_code: int = 200, cors: bool = True) -> None:
        raw = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        if cors:
            self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)


def run_docs_server(port: int = 8080) -> None:
    """Run documentation HTTP server."""
    server_address = ("127.0.0.1", port)
    httpd = http.server.HTTPServer(server_address, DocsRequestHandler)
    print(f"📖 Documentation & Developer Portal serving at http://localhost:{port}/")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping documentation server...")
        httpd.server_close()
