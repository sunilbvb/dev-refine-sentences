"""Universal clipboard and primary selection manager supporting Wayland, X11, and Tkinter."""

import shutil
import subprocess
import threading
from typing import Optional


class ClipboardManager:
    """Read and write system clipboard and primary selection buffers."""

    def __init__(self):
        self.has_wl = bool(shutil.which("wl-copy") and shutil.which("wl-paste"))
        self.has_xclip = bool(shutil.which("xclip"))
        self.has_xsel = bool(shutil.which("xsel"))

    def get_primary_selection(self) -> str:
        """Retrieve text currently highlighted by the user (PRIMARY selection)."""
        # Method 1: Wayland primary selection
        if self.has_wl:
            try:
                res = subprocess.run(["wl-paste", "--primary", "--no-newline"], capture_output=True, text=True, timeout=0.8)
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout
            except Exception:
                pass

        # Method 2: xclip primary
        if self.has_xclip:
            try:
                res = subprocess.run(["xclip", "-selection", "primary", "-o"], capture_output=True, text=True, timeout=0.8)
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout
            except Exception:
                pass

        # Method 3: Tkinter primary selection with 0.25s timeout
        def _read_tk_primary():
            try:
                import tkinter as tk
                root = tk.Tk()
                root.withdraw()
                try:
                    res_p[0] = root.selection_get(selection="PRIMARY")
                except Exception:
                    res_p[0] = ""
                root.destroy()
            except Exception:
                pass

        res_p = [""]
        th_p = threading.Thread(target=_read_tk_primary, daemon=True)
        th_p.start()
        th_p.join(timeout=0.25)
        if res_p[0] and res_p[0].strip():
            return res_p[0]

        return ""

    def get_text(self) -> str:
        """Retrieve current text content from system clipboard."""
        # Method 1: Wayland native
        if self.has_wl:
            try:
                res = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, text=True, timeout=0.8)
                if res.returncode == 0:
                    return res.stdout
            except Exception:
                pass

        # Method 2: xclip
        if self.has_xclip:
            try:
                res = subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True, timeout=0.8)
                if res.returncode == 0:
                    return res.stdout
            except Exception:
                pass

        # Method 3: xsel
        if self.has_xsel:
            try:
                res = subprocess.run(["xsel", "--clipboard", "--output"], capture_output=True, text=True, timeout=0.8)
                if res.returncode == 0:
                    return res.stdout
            except Exception:
                pass

        # Method 4: Stdlib Tkinter fallback with 0.25s timeout to prevent Wayland hangs
        def _read_tk_clip():
            try:
                import tkinter as tk
                root = tk.Tk()
                root.withdraw()
                try:
                    res_c[0] = root.clipboard_get()
                except Exception:
                    res_c[0] = ""
                root.destroy()
            except Exception:
                pass

        res_c = [""]
        th_c = threading.Thread(target=_read_tk_clip, daemon=True)
        th_c.start()
        th_c.join(timeout=0.25)
        return res_c[0]

    def get_selected_or_clipboard(self) -> str:
        """Get currently highlighted text; if none highlighted, fallback to clipboard."""
        selected = self.get_primary_selection()
        if selected and selected.strip():
            return selected.strip()
        return self.get_text().strip()

    def set_text(self, text: str) -> bool:
        """Write text to system clipboard (and primary selection)."""
        success = False

        # Method 1: Wayland native
        if self.has_wl:
            try:
                p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE, text=True)
                p.communicate(input=text, timeout=0.8)
                if p.returncode == 0:
                    success = True
            except Exception:
                pass

        # Method 2: xclip
        if self.has_xclip:
            try:
                p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE, text=True)
                p.communicate(input=text, timeout=0.8)
                if p.returncode == 0:
                    success = True
            except Exception:
                pass

        # Method 3: Tkinter fallback
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            root.destroy()
            success = True
        except Exception:
            pass

        return success
