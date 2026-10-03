"""HTTP server for developer documentation and interactive refinement portal.

100% Python Standard Library.
"""

import http.server
import json
import socket
from pathlib import Path

from daemon import query_daemon_refine
from refiner import RefinerManager

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOCKET_PATH = Path.home() / ".config" / "refine_tool" / "daemon.sock"


class DocsRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler serving static portal files and API endpoints."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT_ROOT), **kwargs)

    def do_GET(self):
        if self.path == "/api/status":
            daemon_active = False
            if SOCKET_PATH.exists():
                try:
                    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    s.settimeout(0.2)
                    s.connect(str(SOCKET_PATH))
                    s.sendall(json.dumps({"mode": "ping"}).encode("utf-8"))
                    resp = s.recv(1024)
                    s.close()
                    daemon_active = resp.strip() == b"PONG"
                except Exception:
                    daemon_active = False

            payload = {
                "status": "online",
                "daemon_active": daemon_active,
                "version": "1.2.0",
            }
            self._send_json(payload)
            return

        # Serve static files from PROJECT_ROOT
        super().do_GET()

    def do_POST(self):
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

    def _send_json(self, data: dict, status_code: int = 200) -> None:
        raw = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
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
