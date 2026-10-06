import sys
import shutil
import subprocess
import time
from typing import Optional


class KeyInjector:
    """Simulates keystrokes via native macOS (osascript), Windows (PowerShell), or Linux (Atspi/tools)."""

    def __init__(self):
        self.is_mac = sys.platform == "darwin"
        self.is_win = sys.platform == "win32"
        self.osascript = shutil.which("osascript")
        self.afplay = shutil.which("afplay")
        self.powershell = shutil.which("powershell")
        self.ydotool = shutil.which("ydotool")
        self.wtype = shutil.which("wtype")
        self.xdotool = shutil.which("xdotool")
        self.notify_send = shutil.which("notify-send")
        self.canberra = shutil.which("canberra-gtk-play")
        self.has_atspi = self._check_atspi()

    def _check_atspi(self) -> bool:
        """Check if GNOME Atspi accessibility keyboard generator is available."""
        if self.is_mac or self.is_win:
            return False
        try:
            import gi
            gi.require_version("Atspi", "2.0")
            from gi.repository import Atspi
            return hasattr(Atspi, "generate_keyboard_event")
        except Exception:
            return False

    def play_sound(self, sound_id: str = "message-new-instant") -> None:
        """Play subtle sensory confirmation sound."""
        if self.is_mac and self.afplay:
            try:
                subprocess.Popen([self.afplay, "/System/Library/Sounds/Tink.aiff"], stderr=subprocess.DEVNULL)
                return
            except Exception:
                pass
        if self.is_win:
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_OK)
                return
            except Exception:
                pass
        if self.canberra:
            try:
                subprocess.Popen([self.canberra, "-i", sound_id], stderr=subprocess.DEVNULL)
            except Exception:
                pass

    def notify(self, title: str, message: str) -> None:
        """Send transient desktop notification."""
        clean_msg = message.replace('"', '\\"')
        clean_title = title.replace('"', '\\"')
        if self.is_mac and self.osascript:
            try:
                subprocess.Popen(
                    ["osascript", "-e", f'display notification "{clean_msg}" with title "{clean_title}"'],
                    stderr=subprocess.DEVNULL,
                )
                return
            except Exception:
                pass
        if self.is_win and self.powershell:
            try:
                cmd = (
                    f'[System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms") | Out-Null; '
                    f'$n = New-Object System.Windows.Forms.NotifyIcon; '
                    f'$n.Icon = [System.Drawing.SystemIcons]::Information; '
                    f'$n.Visible = $true; '
                    f'$n.ShowBalloonTip(2000, "{clean_title}", "{clean_msg}", [System.Windows.Forms.ToolTipIcon]::Info); '
                    f'Start-Sleep -s 3; $n.Dispose()'
                )
                subprocess.Popen(
                    ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cmd],
                    stderr=subprocess.DEVNULL,
                )
                return
            except Exception:
                pass
        if self.notify_send:
            try:
                subprocess.Popen(
                    [self.notify_send, "-a", "Sentence Refiner", "-t", "2500", "-u", "low", title, message],
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass

    def _get_keycodes(self, keysym: int, fallback_codes: list) -> list:
        """Resolve hardware keycodes for a given keysym using Gdk if available, else fallback."""
        try:
            import gi
            gi.require_version("Gtk", "3.0")
            gi.require_version("Gdk", "3.0")
            from gi.repository import Gdk
            keymap = Gdk.Keymap.get_default()
            success, entries = keymap.get_entries_for_keyval(keysym)
            if success and entries:
                return [e.keycode for e in entries]
        except Exception:
            pass
        return fallback_codes

    def release_modifiers(self) -> None:
        """Synthetically release Alt, Ctrl, Shift modifiers so they don't interfere with copy/paste."""
        if self.has_atspi:
            try:
                import gi
                gi.require_version("Atspi", "2.0")
                from gi.repository import Atspi
                # Release Left/Right Alt (64, 108), Left/Right Ctrl (37, 105), Shift (50, 62)
                for code in (64, 108, 37, 105, 50, 62):
                    Atspi.generate_keyboard_event(code, None, Atspi.KeySynthType.RELEASE)
            except Exception:
                pass

    def simulate_copy(self) -> bool:
        """Simulate copy (Cmd+C on macOS, Ctrl+C on Linux/Windows) to copy selected text."""
        # Method 0: macOS native via osascript (Cmd+C)
        if self.is_mac or self.osascript:
            try:
                subprocess.run(
                    ["osascript", "-e", 'tell application "System Events" to keystroke "c" using command down'],
                    check=False,
                    timeout=0.8,
                )
                time.sleep(0.08)
                return True
            except Exception:
                pass

        # Method 0.5: Windows native via PowerShell (Ctrl+C)
        if self.is_win and self.powershell:
            try:
                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('^c')",
                    ],
                    check=False,
                    timeout=1.0,
                )
                time.sleep(0.08)
                return True
            except Exception:
                pass

        # Method 1: Atspi native (Wayland GNOME)
        if self.has_atspi:
            try:
                import gi
                gi.require_version("Atspi", "2.0")
                from gi.repository import Atspi

                self.release_modifiers()
                time.sleep(0.02)
                ctrl_codes = self._get_keycodes(0xffe3, [37])
                c_codes = self._get_keycodes(0x63, [54])
                ctrl_code = ctrl_codes[0] if ctrl_codes else 37
                c_code = c_codes[0] if c_codes else 54

                Atspi.generate_keyboard_event(ctrl_code, None, Atspi.KeySynthType.PRESS)
                Atspi.generate_keyboard_event(c_code, None, Atspi.KeySynthType.PRESS)
                Atspi.generate_keyboard_event(c_code, None, Atspi.KeySynthType.RELEASE)
                Atspi.generate_keyboard_event(ctrl_code, None, Atspi.KeySynthType.RELEASE)
                time.sleep(0.08)
                return True
            except Exception:
                pass

        # Method 2: ydotool
        if self.ydotool:
            try:
                subprocess.run(["ydotool", "key", "29:1", "46:1", "46:0", "29:0"], check=False)
                time.sleep(0.08)
                return True
            except Exception:
                pass

        # Method 3: wtype
        if self.wtype:
            try:
                subprocess.run(["wtype", "-M", "ctrl", "-k", "c", "-m", "ctrl"], check=False)
                time.sleep(0.08)
                return True
            except Exception:
                pass

        # Method 4: xdotool
        if self.xdotool:
            try:
                subprocess.run(["xdotool", "key", "ctrl+c"], check=False)
                time.sleep(0.08)
                return True
            except Exception:
                pass

        return False

    def simulate_paste(self) -> bool:
        """Simulate paste (Cmd+V on macOS, Ctrl+V on Linux/Windows) to replace selected text."""
        # Wait small moment for user to lift fingers off hotkey combo
        time.sleep(0.15)

        # Method 0: macOS native via osascript (Cmd+V)
        if self.is_mac or self.osascript:
            try:
                subprocess.run(
                    ["osascript", "-e", 'tell application "System Events" to keystroke "v" using command down'],
                    check=False,
                    timeout=0.8,
                )
                return True
            except Exception:
                pass

        # Method 0.5: Windows native via PowerShell (Ctrl+V)
        if self.is_win and self.powershell:
            try:
                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('^v')",
                    ],
                    check=False,
                    timeout=1.0,
                )
                return True
            except Exception:
                pass

        # Method 1: Atspi native (Wayland GNOME)
        if self.has_atspi:
            try:
                import gi
                gi.require_version("Atspi", "2.0")
                self.release_modifiers()
                time.sleep(0.02)
                ctrl_codes = self._get_keycodes(0xffe3, [37])
                v_codes = self._get_keycodes(0x76, [55])
                ctrl_code = ctrl_codes[0] if ctrl_codes else 37
                v_code = v_codes[0] if v_codes else 55

                Atspi.generate_keyboard_event(ctrl_code, None, Atspi.KeySynthType.PRESS)
                Atspi.generate_keyboard_event(v_code, None, Atspi.KeySynthType.PRESS)
                Atspi.generate_keyboard_event(v_code, None, Atspi.KeySynthType.RELEASE)
                Atspi.generate_keyboard_event(ctrl_code, None, Atspi.KeySynthType.RELEASE)
                return True
            except Exception:
                pass

        # Method 2: ydotool
        if self.ydotool:
            try:
                subprocess.run(["ydotool", "key", "29:1", "47:1", "47:0", "29:0"], check=False)
                return True
            except Exception:
                pass

        # Method 3: wtype
        if self.wtype:
            try:
                subprocess.run(["wtype", "-M", "ctrl", "-k", "v", "-m", "ctrl"], check=False)
                return True
            except Exception:
                pass

        # Method 4: xdotool
        if self.xdotool:
            try:
                subprocess.run(["xdotool", "key", "ctrl+v"], check=False)
                return True
            except Exception:
                pass

        return False
