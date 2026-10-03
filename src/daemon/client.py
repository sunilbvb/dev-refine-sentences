"""Client connector to RefineDaemon socket."""

import json
import socket
from pathlib import Path


SOCKET_PATH = Path.home() / ".config" / "refine_tool" / "daemon.sock"


def send_daemon_request(mode: str = "popup", tone: str = "standard", paste: bool = True) -> bool:
    """Send request to resident background daemon.

    Returns:
        bool: True if processed by daemon, False if daemon is inactive.
    """
    if not SOCKET_PATH.exists():
        return False

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            sock.connect(str(SOCKET_PATH))

            payload = json.dumps({"mode": mode, "tone": tone, "paste": paste})
            sock.sendall(payload.encode("utf-8"))

            resp = sock.recv(1024)
            return resp.strip() == b"OK"
    except Exception:
        return False


def query_daemon_refine(text: str, tone: str = "standard") -> dict | None:
    """Send text directly to daemon for instant in-RAM refinement.

    Returns:
        dict with keys {'refined', 'explanations', 'engine'} or None if daemon inactive.
    """
    if not SOCKET_PATH.exists():
        return None

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(1.0)
            sock.connect(str(SOCKET_PATH))

            payload = json.dumps({"mode": "refine", "text": text, "tone": tone})
            sock.sendall(payload.encode("utf-8"))

            resp = sock.recv(65536)
            if not resp:
                return None
            return json.loads(resp.decode("utf-8"))
    except Exception:
        return None

