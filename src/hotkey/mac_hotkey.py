"""macOS global hotkey -> clipboard refine -> paste. 100% stdlib (ctypes + Carbon/Quartz).

Listening for the hotkey needs no permission. Auto copy/paste (synthetic Cmd+C / Cmd+V)
needs Accessibility access for the Python binary; without it the tool falls back to
refining whatever is already on the clipboard and leaves the result there for Cmd+V.
"""

import ctypes
import ctypes.util
import os
import sys
import threading
import time
from typing import Optional

KEY_CODES = {
    "a": 0, "s": 1, "d": 2, "f": 3, "h": 4, "g": 5, "z": 6, "x": 7, "c": 8, "v": 9,
    "b": 11, "q": 12, "w": 13, "e": 14, "r": 15, "y": 16, "t": 17, "o": 31, "u": 32,
    "i": 34, "p": 35, "l": 37, "j": 38, "k": 40, "n": 45, "m": 46,
}
CARBON_MODS = {"cmd": 0x100, "shift": 0x200, "alt": 0x800, "ctrl": 0x1000}
MOD_ALIASES = {"command": "cmd", "option": "alt", "opt": "alt", "control": "ctrl", "super": "cmd", "win": "cmd"}
DEFAULT_HOTKEY = "ctrl+alt+r"
CMD_FLAG = 0x100000  # kCGEventFlagMaskCommand
KEY_C, KEY_V = 8, 9


def parse_hotkey(spec: str) -> tuple:
    """'ctrl+alt+r' -> (keycode, carbon_modifiers)."""
    parts = [MOD_ALIASES.get(p.strip().lower(), p.strip().lower()) for p in spec.split("+")]
    key = parts[-1]
    if key not in KEY_CODES:
        raise ValueError(f"Unsupported key '{key}'. Use a letter a-z.")
    mods = 0
    for m in parts[:-1]:
        if m not in CARBON_MODS:
            raise ValueError(f"Unknown modifier '{m}'. Use ctrl, alt, shift, cmd.")
        mods |= CARBON_MODS[m]
    if not mods:
        raise ValueError("Hotkey needs at least one modifier (e.g. ctrl+alt+r).")
    return KEY_CODES[key], mods


TAP_WINDOW = 0.4  # seconds allowed between taps of a multi-tap hotkey


def parse_hotkey_spec(spec: str) -> tuple:
    """'cmd+a*2' -> (keycode, carbon_modifiers, taps). '*N' (N=2 or 3) means press N times quickly."""
    spec = spec.strip().lower().replace(" ", "")
    taps = 1
    if "*" in spec:
        spec, _, n = spec.partition("*")
        if n not in ("2", "3"):
            raise ValueError("Multi-tap must be *2 or *3 (e.g. cmd+a*2).")
        taps = int(n)
    keycode, mods = parse_hotkey(spec)
    return keycode, mods, taps


# CGEventFlags masks used by the passive (multi-tap) listener
_CG_MODS = {0x100: 0x100000, 0x200: 0x20000, 0x800: 0x80000, 0x1000: 0x40000}  # carbon -> CG
_CG_ALL_MODS = 0x100000 | 0x20000 | 0x80000 | 0x40000


class _Quartz:
    def __init__(self):
        self.lib = ctypes.CDLL("/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices")
        self.lib.AXIsProcessTrusted.restype = ctypes.c_bool
        self.lib.CGEventCreateKeyboardEvent.restype = ctypes.c_void_p
        self.lib.CGEventCreateKeyboardEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_bool]
        self.lib.CGEventSetFlags.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
        self.lib.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
        self.cf = ctypes.CDLL(ctypes.util.find_library("CoreFoundation"))
        self.cf.CFRelease.argtypes = [ctypes.c_void_p]

    def trusted(self) -> bool:
        return bool(self.lib.AXIsProcessTrusted())

    def cmd_key(self, keycode: int) -> None:
        for down in (True, False):
            ev = self.lib.CGEventCreateKeyboardEvent(None, keycode, down)
            self.lib.CGEventSetFlags(ev, CMD_FLAG)
            self.lib.CGEventPost(0, ev)  # kCGHIDEventTap
            self.cf.CFRelease(ev)
            time.sleep(0.02)


def _run_refine_pipeline(refiner, clipboard, injector, quartz: _Quartz, tone: str, history) -> None:
    trusted = quartz.trusted()
    if trusted:
        time.sleep(0.25)  # let the user release the hotkey modifiers
        sentinel = f"__refine_sentinel_{time.time()}__"
        clipboard.set_text(sentinel)
        quartz.cmd_key(KEY_C)
        text = ""
        for _ in range(10):
            time.sleep(0.05)
            text = clipboard.get_text()
            if text and text != sentinel:
                break
        if text == sentinel:
            text = ""
    else:
        text = clipboard.get_text()

    if not text or not text.strip():
        hint = "Select a sentence first." if trusted else "Copy a sentence (Cmd+C) first, then press the hotkey."
        injector.notify("Sentence Refiner", hint)
        return

    original = text.strip()
    refined = refiner.refine(original, tone=tone)
    clipboard.set_text(refined)
    try:
        history.record(original=original, refined=refined, tone=tone, engine=refiner.get_active_engine().name)
    except Exception:
        pass

    if trusted:
        quartz.cmd_key(KEY_V)
        injector.play_sound("complete")
        injector.notify("Sentence Refiner", f"Refined: {refined[:60]}")
    else:
        injector.play_sound("complete")
        injector.notify("Sentence Refiner", "Refined text copied. Press Cmd+V to paste. "
                        "(Grant Accessibility to auto-paste.)")


def _run_multi_tap(quartz, keycode: int, mods: int, taps: int, label: str, trigger) -> None:
    """Passive keyboard listener: fire `trigger` when the combo is pressed `taps` times within
    TAP_WINDOW. Listen-only, so the keystroke still reaches the app (e.g. Cmd+A still selects
    all). Needs the Input Monitoring permission for this Python."""
    lib = quartz.lib
    cf = quartz.cf
    want_flags = 0
    for carbon_bit, cg_bit in _CG_MODS.items():
        if mods & carbon_bit:
            want_flags |= cg_bit

    lib.CGPreflightListenEventAccess.restype = ctypes.c_bool
    if not lib.CGPreflightListenEventAccess():
        lib.CGRequestListenEventAccess.restype = ctypes.c_bool
        lib.CGRequestListenEventAccess()  # shows the macOS permission prompt once
        sys.exit("Input Monitoring is not granted to this Python. Enable it in System Settings > "
                 f"Privacy & Security > Input Monitoring for: {sys.executable}, then restart.")

    tap_cb_t = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p)
    lib.CGEventGetIntegerValueField.restype = ctypes.c_int64
    lib.CGEventGetIntegerValueField.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    lib.CGEventGetFlags.restype = ctypes.c_uint64
    lib.CGEventGetFlags.argtypes = [ctypes.c_void_p]
    lib.CGEventTapCreate.restype = ctypes.c_void_p
    lib.CGEventTapCreate.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
                                     ctypes.c_uint64, tap_cb_t, ctypes.c_void_p]
    lib.CGEventTapEnable.argtypes = [ctypes.c_void_p, ctypes.c_bool]
    state = {"count": 0, "last": 0.0, "port": None}

    def on_event(_proxy, etype, event, _refcon):
        if etype in (0xFFFFFFFE, 0xFFFFFFFF):  # tap disabled by timeout/user input: turn it back on
            lib.CGEventTapEnable(state["port"], True)
            return event
        if etype != 10:  # kCGEventKeyDown
            return event
        if lib.CGEventGetIntegerValueField(event, 9) != keycode:      # kCGKeyboardEventKeycode
            return event
        if lib.CGEventGetIntegerValueField(event, 8):                 # ignore key auto-repeat
            return event
        if (lib.CGEventGetFlags(event) & _CG_ALL_MODS) != want_flags:
            state["count"] = 0
            return event
        now = time.monotonic()
        state["count"] = state["count"] + 1 if now - state["last"] <= TAP_WINDOW else 1
        state["last"] = now
        if state["count"] >= taps:
            state["count"] = 0
            trigger()
        return event

    callback = tap_cb_t(on_event)  # keep a reference alive
    # kCGSessionEventTap=1, kCGHeadInsertEventTap=0, kCGEventTapOptionListenOnly=1, mask: keyDown (1<<10)
    port = lib.CGEventTapCreate(1, 0, 1, 1 << 10, callback, None)
    if not port:
        sys.exit("Could not create the keyboard listener (Input Monitoring missing?).")
    state["port"] = port

    cf.CFMachPortCreateRunLoopSource.restype = ctypes.c_void_p
    cf.CFMachPortCreateRunLoopSource.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long]
    cf.CFRunLoopGetCurrent.restype = ctypes.c_void_p
    cf.CFRunLoopAddSource.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    source = cf.CFMachPortCreateRunLoopSource(None, port, 0)
    common_modes = ctypes.c_void_p.in_dll(cf, "kCFRunLoopCommonModes")
    cf.CFRunLoopAddSource(cf.CFRunLoopGetCurrent(), source, common_modes)
    lib.CGEventTapEnable(port, True)

    print(f"Sentence Refiner hotkey active: {label}  (press {taps}x within {TAP_WINDOW}s; listen-only)", flush=True)
    if not quartz.trusted():
        print("Note: Accessibility not granted -> clipboard fallback mode.", flush=True)
    cf.CFRunLoopRun()


def _watch_config_for_hotkey(config, current: str, injector) -> None:
    """Re-exec this process when the saved hotkey changes, so the new combo is live
    without a manual restart (works under launchd KeepAlive and when run by hand)."""
    path = config.config_file
    last = path.stat().st_mtime if path.exists() else 0
    while True:
        time.sleep(1.5)
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime == last:
            continue
        last = mtime
        wanted = str(config.get_setting("hotkey") or DEFAULT_HOTKEY).lower()
        if wanted != current:
            try:
                parse_hotkey_spec(wanted)
            except ValueError:
                continue  # ignore an invalid saved combo; keep the working one
            injector.notify("Sentence Refiner", f"Hotkey changed to {wanted}")
            os.execv(sys.executable, [sys.executable] + sys.argv)


def run_hotkey_listener(config, clipboard, injector, history, hotkey: Optional[str] = None,
                        tone: Optional[str] = None, engine: Optional[str] = None,
                        model: Optional[str] = None) -> None:
    """Listen for a global hotkey. Tone/engine/model are re-read from `config` on every press,
    so settings changes apply instantly. An explicit `hotkey` pins the combo; otherwise it is
    taken from config and live-reloaded."""
    if sys.platform != "darwin":
        sys.exit("--hotkey is macOS only. On Linux/Windows use the scripts/ shortcut setup.")

    from refiner import RefinerManager

    explicit_hotkey = hotkey is not None
    if not explicit_hotkey:
        hotkey = str(config.get_setting("hotkey") or DEFAULT_HOTKEY).lower()
    try:
        keycode, mods, taps = parse_hotkey_spec(hotkey)
    except ValueError as exc:
        print(f"Invalid hotkey '{hotkey}': {exc} -> using {DEFAULT_HOTKEY}", flush=True)
        hotkey = DEFAULT_HOTKEY
        keycode, mods, taps = parse_hotkey_spec(hotkey)

    quartz = _Quartz()
    carbon = ctypes.CDLL("/System/Library/Frameworks/Carbon.framework/Carbon")

    class EventTypeSpec(ctypes.Structure):
        _fields_ = [("eventClass", ctypes.c_uint32), ("eventKind", ctypes.c_uint32)]

    class EventHotKeyID(ctypes.Structure):
        _fields_ = [("signature", ctypes.c_uint32), ("id", ctypes.c_uint32)]

    handler_t = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
    carbon.GetApplicationEventTarget.restype = ctypes.c_void_p
    carbon.InstallEventHandler.argtypes = [ctypes.c_void_p, handler_t, ctypes.c_uint32,
                                           ctypes.POINTER(EventTypeSpec), ctypes.c_void_p, ctypes.c_void_p]
    carbon.RegisterEventHotKey.argtypes = [ctypes.c_uint32, ctypes.c_uint32, EventHotKeyID,
                                           ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p)]

    busy = threading.Lock()

    def worker():
        if not busy.acquire(blocking=False):
            return
        try:
            eff_tone = tone or config.get_setting("preferred_tone") or "standard"
            eff_engine = engine or config.get_setting("preferred_engine") or "auto"
            refiner = RefinerManager(preferred_engine=eff_engine, model=model, config_manager=config)
            _run_refine_pipeline(refiner, clipboard, injector, quartz, eff_tone, history)
        except Exception as exc:  # never kill the listener
            injector.notify("Sentence Refiner", f"Error: {exc}")
        finally:
            busy.release()

    def trigger():
        threading.Thread(target=worker, daemon=True).start()

    def on_hotkey(_call_ref, _event, _user):
        trigger()
        return 0

    if taps > 1:
        if not explicit_hotkey:
            threading.Thread(target=_watch_config_for_hotkey, args=(config, hotkey, injector), daemon=True).start()
        _run_multi_tap(quartz, keycode, mods, taps, hotkey, trigger)
        return

    callback = handler_t(on_hotkey)  # keep a reference alive
    spec = EventTypeSpec(0x6B657962, 5)  # 'keyb', kEventHotKeyPressed
    status = carbon.InstallEventHandler(carbon.GetApplicationEventTarget(), callback, 1,
                                        ctypes.byref(spec), None, None)
    if status != 0:
        sys.exit(f"InstallEventHandler failed ({status}).")

    ref = ctypes.c_void_p()
    status = carbon.RegisterEventHotKey(keycode, mods, EventHotKeyID(0x52464E52, 1),
                                        carbon.GetApplicationEventTarget(), 0, ctypes.byref(ref))
    if status != 0:
        sys.exit(f"Could not register {hotkey} (status {status}); another app may own it.")

    print(f"Sentence Refiner hotkey active: {hotkey}  "
          f"({'pinned by flag' if explicit_hotkey else 'from config, live-reload on'})", flush=True)
    if not quartz.trusted():
        print("Note: Accessibility not granted to this Python -> clipboard fallback mode.\n"
              f"  Grant it to: {sys.executable}\n"
              "  System Settings > Privacy & Security > Accessibility", flush=True)
    if not explicit_hotkey:
        threading.Thread(target=_watch_config_for_hotkey, args=(config, hotkey, injector), daemon=True).start()
    carbon.RunApplicationEventLoop()
