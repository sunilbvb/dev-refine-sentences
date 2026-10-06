# macOS Setup Guide

Refine any selected text, in any app, with one keystroke: the Claude desktop app, Google Chat,
Chrome, Slack, Notes, VS Code. This guide covers the workflow, the setup, the settings, the design
and the problems we ran into on the way.

> Tested on macOS with Apple Silicon, a 16 GB MacBook, Homebrew Python 3.14 and Ollama.

---

## 1. How it works (the workflow)

```
 You select text in any app
          |
          v
 Press the hotkey  (default: Cmd+A twice, or Ctrl+Option+R)
          |
          v
 Listener (src/hotkey/mac_hotkey.py) wakes up
   1. Cmd+C  -> copies the selection            (needs Accessibility)
   2. Refiner engine rewrites it                (re-reads your settings on every press)
        Gemini -> OpenAI -> Claude -> Ollama (local open model) -> LanguageTool -> built-in rules
   3. Puts the result on the clipboard
   4. Cmd+V  -> replaces the selection          (needs Accessibility)
   5. Plays a sound + shows a notification
```

The listener is a small background process that starts at login. It does not need the web portal.
It only needs the web portal (port 8080) if you want the Settings page.

**If Accessibility is not granted**, the tool falls back to *clipboard mode*: you press Cmd+C
yourself, press the hotkey, then paste with Cmd+V.

### Why a global hotkey and not a macOS Quick Action / Services entry?

We tried Services first and abandoned it:

| Approach | Result |
|---|---|
| `osascript` keystrokes from a shell script | Blocked: `osascript is not allowed to send keystrokes (1002)` |
| Hand-built Automator workflow | Registered, but never ran from the shortcut |
| Automator Quick Action made in the Automator UI | Worked in TextEdit and other native apps. **Did not work in the Claude desktop app or Google Chat**: Electron apps and web editors do not support the macOS Services menu |
| **Global hotkey listener (current)** | Works in every app, including Electron and browsers |

---

## 2. Requirements

| Item | Why | How to get it |
|---|---|---|
| **Python 3.10+** | The code uses `dict \| None` type syntax. macOS ships Python 3.9, which crashes on import | `brew install python` |
| **Tk** (optional) | Only for the desktop popup window; `main.py` imports it at start-up | `brew install python-tk@3.14` (match your Python version) |
| **Ollama** (optional) | Runs an open model locally for much better rewrites than the built-in rules | `brew install ollama` |

Check your Python: `/opt/homebrew/bin/python3 --version`.
The shell's default `python3` may still be the old system 3.9, so use the full Homebrew path
(or put `/opt/homebrew/bin` first on your `PATH`).

---

## 3. Quick start

```bash
git clone https://github.com/sunilbvb/dev-refine-sentences
cd dev-refine-sentences

# 1. (optional) local open model, free and offline
brew services start ollama
ollama pull qwen2.5:3b
/opt/homebrew/bin/python3 main.py --set-model qwen2.5:3b

# 2. start the hotkey listener now and at every login
bash scripts/install_mac_hotkey.sh

# 3. (optional) web portal + Settings page
PATH=/opt/homebrew/bin:$PATH bash scripts/start.sh      # then open http://localhost:8080
```

Then grant the permissions in section 4 and select some text.

---

## 4. Permissions (macOS makes you do these yourself)

The permissions go to **Python.app** itself, not to Terminal or the Claude app:

```
/opt/homebrew/Cellar/python@3.14/<version>/Frameworks/Python.framework/Versions/3.14/Resources/Python.app
```

| Permission | Needed for | Where |
|---|---|---|
| **Accessibility** | Auto copy (Cmd+C) and paste (Cmd+V) | System Settings > Privacy & Security > Accessibility |
| **Input Monitoring** | Only for **multi-tap** hotkeys such as `cmd+a*2` | System Settings > Privacy & Security > Input Monitoring |

How to add it: open the page above, click **`+`**, press **Cmd+Shift+G**, paste the Python.app path
and click **Open**, then make sure the toggle is **on**.
Shortcut: `open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"`
(use `Privacy_ListenEvent` for Input Monitoring).

**Important:** after granting a permission, restart the listener:

```bash
launchctl kickstart -k gui/$(id -u)/com.refine.hotkey
```

> **Gotcha we hit:** when the listener was started from inside another app (for example from a
> terminal in the Claude app), macOS checked the permission against *that* app and reported
> "Accessibility not granted" even though Python.app was enabled. Starting it as its own process
> (the LaunchAgent does this, or `open -n -a ".../Python.app" --args main.py --hotkey`) fixes it.

The listener log tells you the state: `~/.config/refine_tool/hotkey.log`.

---

## 5. Hotkeys

Set the combo with the CLI or the Settings page. It applies **live**, with no restart.

```bash
python3 main.py --set-hotkey "ctrl+alt+r"     # modifiers + one letter
python3 main.py --set-hotkey "cmd+shift+e"
python3 main.py --set-hotkey "cmd+a*2"        # press Cmd+A twice within 0.4 s
```

Syntax: modifiers `ctrl`, `alt` (Option), `shift`, `cmd`, plus **one** letter a-z. Add `*2` or `*3`
for a double or triple tap.

### What is and is not possible

| Idea | Possible? | Notes |
|---|---|---|
| Modifiers + one letter (`ctrl+alt+r`) | Yes | Uses the macOS Carbon hotkey API. No extra permission to listen |
| Two letters at once (e.g. A and R together) | **No** | The hotkey API takes one non-modifier key |
| Double tap (`cmd+a*2`, `ctrl+alt+a*2`) | Yes | Uses a passive keyboard listener. Needs **Input Monitoring** |
| Cmd+A then R in sequence | Not recommended | The plain `R` would be typed over your selected text |
| `cmd+r` | Avoid | Cmd+R reloads pages in browsers |

### About `cmd+a*2`

* Cmd+A still does **Select All**. The listener only watches, so nothing is blocked.
* The second press runs the refine. The first press just selects everything in the field.
* Because Cmd+A selects the whole field, the **whole message** is refined, not one sentence.
* Pressing Cmd+A twice out of habit will refine and replace the text. **Cmd+Z** undoes it.
* The tap window is `TAP_WINDOW = 0.4` seconds in `src/hotkey/mac_hotkey.py`.
* If you want something that cannot fire by accident, use `ctrl+alt+a*2`.

---

## 6. Settings

Four settings are editable. All of them are stored in `~/.config/refine_tool/config.json`.

| Setting | CLI | Values | Default |
|---|---|---|---|
| Hotkey | `--set-hotkey` | see section 5 | `ctrl+alt+r` |
| Tone | `--set-tone` | standard, concise, professional, friendly, bullet_points, email_formal | `standard` |
| Engine | `--set-engine` | auto, rules, gemini, openai, claude, ollama, languagetool | `auto` |
| Local model | `--set-model` | any installed Ollama model name, no spaces | `qwen2.5:3b` |

```bash
python3 main.py --show-config            # print current settings (API key values are never shown)
python3 main.py --set-model qwen2.5:1.5b
python3 main.py --set-tone concise
```

Explicit flags such as `--tone` and `--engine` always win over the saved config.

### Web Settings page

Open http://localhost:8080/#settings (start it with `scripts/start.sh`). It shows dropdowns for tone
and engine, a list of the models you actually have in Ollama (with sizes), and the hotkey field.
Press **Save**.

* Invalid values are rejected with a message and are not saved.
* API keys are **not** editable from the web page, on purpose. Use `--set-key` or environment
  variables.

### What applies when

| Change | Takes effect |
|---|---|
| Tone, engine, model | On the next hotkey press (the engine is rebuilt every time) |
| Hotkey | Within ~2 seconds. The listener restarts itself (same process id) |
| Web / daemon refine endpoint | As soon as `config.json` changes |

---

## 7. Choosing a local model (and why it was slow)

Rewrites quality and speed depend on the model. The built-in rule engine only fixes simple things
("i has went" becomes "I have went"). A local open model fixes grammar properly:

| Model | Size | Typical speed on 16 GB Mac | Quality |
|---|---|---|---|
| built-in rules | none | instant | basic |
| `qwen2.5:0.5b` | ~0.4 GB | very fast | weak |
| **`qwen2.5:3b` (default)** | ~1.9 GB | ~0.6-2 s | good |
| `gemma4:e4b` | 9.6 GB | 4 s when warm, **minutes when memory is tight** | very good |

**Real incident:** with `gemma4:e4b`, one sentence took about **5 minutes**. The 16 GB Mac was
already swapping (17.6 of 18.4 GB swap used: the iOS Simulator, browsers and the 9.5 GB model all
competed for RAM), so the model kept being paged to disk. Switching to the 2 GB `qwen2.5:3b` brought
it to 1-2 seconds. Rule of thumb: **keep the model under about a third of your free RAM.**

Other things the tool does to stay fast: it keeps the model loaded for 30 minutes
(`keep_alive`) and waits up to 60 s for the very first (cold) call.

Check what is loaded: `ollama ps`. Free memory: `ollama stop <model>`.

For the best quality, add a cloud key: `python3 main.py --set-key anthropic <key>` (or gemini / openai).

---

## 8. Starting at login

```bash
bash scripts/install_mac_hotkey.sh              # recommended: hotkey comes from config, live reload
bash scripts/install_mac_hotkey.sh "ctrl+alt+r" # pinned: ignores later hotkey changes in config
```

This writes `~/Library/LaunchAgents/com.refine.hotkey.plist` (runs Python.app directly, restarts
it if it crashes, logs to `~/.config/refine_tool/hotkey.log`).

```bash
launchctl list | grep refine                                   # is it running?
launchctl kickstart -k gui/$(id -u)/com.refine.hotkey          # restart
launchctl bootout gui/$(id -u)/com.refine.hotkey               # stop (until next login)
launchctl bootout gui/$(id -u)/com.refine.hotkey && rm ~/Library/LaunchAgents/com.refine.hotkey.plist   # uninstall
```

To run it by hand instead (no login item):

```bash
open -n -a "/opt/homebrew/Cellar/python@3.14/<version>/Frameworks/Python.framework/Versions/3.14/Resources/Python.app" \
  --args "$PWD/main.py" --hotkey
```

> After a `brew upgrade python`, the Python.app path changes. Re-add the new Python.app under
> Accessibility (and Input Monitoring) and run `bash scripts/install_mac_hotkey.sh` again.

---

## 9. Troubleshooting & FAQ

**Nothing happens when I press the hotkey.**
1. `launchctl list | grep refine` should show a PID. If not, run `bash scripts/install_mac_hotkey.sh`.
2. `tail ~/.config/refine_tool/hotkey.log`. Look for `hotkey active: ...`.
3. Make sure text is **selected** first.
4. If the log says `Accessibility not granted`, see section 4, then restart the listener.

**The log says "Input Monitoring is not granted" and the hotkey does not start.**
You set a multi-tap hotkey (`*2`) but have not enabled Input Monitoring for Python.app. Enable it
(section 4) and restart the listener, or switch to a normal combo: `python3 main.py --set-hotkey ctrl+alt+r`.

**`Could not register ctrl+alt+r (status ...)`**
Another app owns that combo. Pick another one.

**`sandbox_extension_issue_file_to_process failed ... Operation not permitted` in the log.**
Harmless noise from launchd. Ignore it.

**It pastes but the text is unchanged.**
The engine fell back to the original text. Usually Ollama is not running (`brew services start ollama`)
or the model is not installed (`ollama list`). Run `python3 main.py --mode cli --text "test sentence"`
to see the engine's behaviour.

**It is very slow.**
The model is too big for your free RAM (section 7). Use a smaller model, quit heavy apps
(iOS Simulator, Docker), or check `sysctl vm.swapusage`.

**`TypeError: unsupported operand type(s) for |`**
You are running Python 3.9. Use `/opt/homebrew/bin/python3` (3.10+).

**`ModuleNotFoundError: No module named '_tkinter'`**
`brew install python-tk@3.14` (match your Python version).

**Does it work in the Claude desktop app and Google Chat?**
Yes, that is the point of the hotkey listener. A *Chrome extension* would only cover web pages, and
could never reach the Claude desktop app.

**Does my text leave my Mac?**
Not with the built-in rules or Ollama. Only if you configure a cloud key (Gemini / OpenAI / Claude)
and the engine is set to auto or that provider.

**Is the web Settings page safe?**
It only listens on `127.0.0.1`. Writes are accepted only from the portal itself (it checks the
`Origin` and `Host` headers and requires `application/json`), so another website you have open in
your browser cannot change your settings. API keys are never returned by the API.

**Why can't I use two letters like A+R?**
macOS global hotkeys support modifiers plus a single key. Use a double tap (`*2`) instead.

**Can I get a QuillBot-style button next to every text box?**
That needs a browser extension. It is not built yet. It would cover Chrome pages (Google Chat,
Gmail, claude.ai) but not native apps, and the hotkey would stay for those.

---

## 10. Files added or changed for macOS

| File | Purpose |
|---|---|
| `src/hotkey/mac_hotkey.py` | Global hotkey (Carbon) and multi-tap listener (CGEventTap), copy / refine / paste pipeline, live hotkey reload |
| `src/config/settings.py` | Editable settings with validation, atomic saves, API-key-free public view |
| `src/refiner/manager.py`, `ollama.py` | Local model comes from config; model kept loaded; 60 s timeout |
| `src/daemon/server.py` | Rebuilds its engine when `config.json` changes |
| `src/web_server/server.py` | `GET/POST /api/config`, `GET /api/ollama/models` with origin checks |
| `web/js/modules/settings.js`, `index.html` | Settings page |
| `scripts/install_mac_hotkey.sh` | Login item (LaunchAgent) installer |
| `scripts/setup_shortcuts_mac.sh` | Now just calls the installer (the Services approach was removed) |
| `main.py` | `--hotkey`, `--set-model/--set-hotkey/--set-tone/--set-engine`, `--show-config` |
| `tests/test_all.py` | Tests for settings validation, hotkey parsing, and a web test that no longer depends on a running Ollama |
