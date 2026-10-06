# Frequently Asked Questions (FAQ)

---

### Q: Does this tool work on macOS (MacBook), Windows, and Linux?
A: **Yes, 100%!** Universal Sentence Refiner is engineered with 100% Python Standard Library (zero third-party pip dependencies) and includes native adapters for all major operating systems:
* **Linux (Ubuntu / Fedora / Arch / Wayland & X11)**: Uses native Wayland `wl-copy`/`wl-paste`, `xclip`, and `Atspi` accessibility. 1-click shortcut registrar: `bash scripts/setup_shortcuts.sh`.
* **macOS (MacBook, iMac, Mac Studio)**: Uses native `pbcopy`/`pbpaste`, AppleScript `osascript` keystrokes, and system notifications. 1-click Quick Action registrar: `bash scripts/setup_shortcuts_mac.sh`.
* **Windows (Windows 10 & 11)**: Uses native `clip.exe`, PowerShell `SendKeys`, and Windows Forms notifications. 1-click desktop shortcut creator: `scripts\setup_shortcuts_win.bat` (or AutoHotkey script `scripts/refine_shortcuts.ahk`).

---

### Q: What is the "Super" key on my keyboard?
A: The **Super key** is the **Windows key** (`⊞ Win`) on a standard PC keyboard, or the **Command key** (`⌘ Cmd`) on an Apple Mac keyboard. On most keyboards, it is located on the bottom-left row between the `Ctrl` and `Alt` (or `Option`) keys.

---

### Q: What is the difference between `Ctrl+Alt+R` and `Super+Shift+R`?
A: The tool features two complementary operating modes:
1. **Visual Popup Mode (`Ctrl + Alt + R`)**:
   - Opens a floating dark-mode modal right next to your cursor.
   - Shows original text, word-by-word visual diff (<span style="color:#F38BA8">red deletions</span>, <span style="color:#A6E3A1">green additions</span>), tone switcher buttons, Teach Mode explanations, and readability metrics.
   - Press **Enter** or click **Apply** to paste the refined sentence.
2. **Instant Flash Mode (`Super + Shift + R`)**:
   - Zero-dialog in-place replacement.
   - Automatically polishes the highlighted sentence in ~2ms, copies it to the clipboard, replaces it in-place via simulated paste, and plays an audio confirmation chime. No window appears.

---

### Q: I pressed the shortcut and nothing happened. Does that mean the server is not running?
A: Not necessarily! If pressing the shortcut produces no change:
1. **Make sure text is highlighted first**: The tool needs selected text to refine. Highlight your sentence with your mouse drag or `Shift + Arrow keys` before hitting the shortcut. If no text is selected, a notification will appear reminding you to highlight text first.
2. **Check service status**: Run `./scripts/status.sh` or `systemctl --user status refine-daemon.service`. The daemon runs as an in-RAM resident service for sub-5ms latency.
3. **Check keybindings**: Run `gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings` on Linux or re-run `bash scripts/setup_shortcuts.sh`.

---

### Q: How does the tool handle grammatical errors like "I students are is great"?
A: The built-in rule engine includes dedicated grammar rules for:
1. **Pronoun-before-noun correction**: Corrects subjective/objective pronouns into possessive determiners (`I students` ➔ `My students`, `I team` ➔ `My team`, `I friends` ➔ `My friends`).
2. **Duplicate verb / copula collision**: Collapses accidental double auxiliary verbs (`are is` / `is are` ➔ `are`, `was were` ➔ `were`, `has have` ➔ `have`).
3. **Missing copulas & double negatives**: Fixes missing auxiliary verbs and resolves double negatives (`didn't have no` ➔ `didn't have any`).
* Input: `"I students are is great"`
* Output: `"My students are great."`
* For complex linguistic restructuring, you can also connect cloud AI models (Gemini, Claude, OpenAI) with a free API key.

---

### Q: Why did the application window freeze when I clicked the notification and pasted, and how was it solved?
A: In X11/Xwayland, the clipboard is **pull-based** (the selection owner must stay alive and answer incoming selection requests from other applications). When Tkinter was previously invoked inside secondary threads of the daemon without a persistent event loop, the destroyed Tkinter window left a dangling selection ID. When an app like Chrome attempted to paste, Chrome's UI thread blocked waiting for a response that never arrived.
* **Solution**:
  1. Installed and linked native Wayland `wl-copy`/`wl-paste` into `~/.local/bin/`. Wayland's `wl_data_device` protocol handles clipboard storage asynchronously without window ownership locks.
  2. Isolated any fallback clipboard operations into clean ephemeral subprocesses.
  3. Made desktop notifications transient (`-t 2500 -u low`) and non-blocking, preventing window focus trapping.

---

### Q: Do I need to press Ctrl+C before pressing the shortcut?
A: **No!** Just highlight the text (with mouse drag or `Shift+Arrows`) and press `Ctrl+Alt+R` (or `Super+Shift+R`). The tool automatically captures the highlighted text directly from the OS primary selection buffer or simulated copy.

---

### Q: What is Teach Mode ("Why Changed?")?
A: Teach Mode explains the exact grammatical, typographical, or stylistic reasons why text was altered. When using the built-in rule engine, the popup window displays notes such as:
* *"Grammar: Corrected pronoun 'I' to possessive 'My' before noun 'students'."*
* *"Grammar: Removed duplicate verb 'are is' → 'are'."*
* *"Subject-verb agreement: third-person singular uses 'goes'."*
* *"Irregular verb: 'buy' past tense is 'bought'."*
* *"Conciseness: Removed filler word 'basically'."*

---

### Q: How do I manage background services (start, stop, restart, status)?
A: Use the 1-click scripts in the `scripts/` directory:
```bash
./scripts/start.sh    # Start resident daemon and web portal
./scripts/status.sh   # Live probe of PIDs, RAM usage, ports, and sockets
./scripts/restart.sh  # Cleanly restart all services
./scripts/stop.sh     # Terminate all background processes
```

---

### Q: How do I configure API keys for Google Gemini, OpenAI (ChatGPT), or Anthropic (Claude)?
A: You can configure API keys in three easy ways:
1. **Via CLI**:
   ```bash
   python3 main.py --set-key gemini <YOUR_API_KEY>
   python3 main.py --set-key openai <YOUR_API_KEY>
   python3 main.py --set-key claude <YOUR_API_KEY>
   ```
2. **Via Desktop Popup**: Press `Ctrl+Alt+R` and click the **[⚙️ Settings]** button in the header.
3. **Via Web Portal**: Open [http://localhost:8080](http://localhost:8080), go to **Config**, and save your keys.
*(Keys are stored locally in `~/.config/refine_tool/config.json`. If no keys are provided, the tool automatically uses the 100% offline rule engine.)*

---

### Q: How do I open and use the web documentation portal (`index.html`)?
A: You can view it in two ways:
1. **Locally via Web Server**: Run `./scripts/start.sh` (or `python3 main.py --serve 8080`) and open [http://localhost:8080](http://localhost:8080). This connects live to your resident daemon in RAM.
2. **Standalone Browser File**: Double-click `index.html` or open `file:///.../index.html` directly in any web browser. It runs with an embedded client-side fallback rule engine with zero server dependencies!

---

### Q: Can I install and run this without `sudo` privileges?
A: **Yes!** Run `bash packaging/install_user.sh`. It installs binaries to `~/.local/bin` and activates user-level systemd services (`systemctl --user status refine-daemon.service`) with zero root privileges required.

---

### Q: Why did the tool previously not refine "Also please crete a develop branch because I wasn other develoeprs..."?
A: When no cloud API key (Gemini, Claude, OpenAI) is configured and local Ollama is not active, the tool runs its **100% offline built-in engine**. Previously, the rule engine only contained exact regex substitutions and lacked a general spell checker, meaning words like `crete`, `develoeprs`, `develpo`, `follwo`, and `stndard` were ignored.
* **The Fix**: We integrated a native, zero-pip pure Python **Spelling Engine** (`src/refiner/spelling.py`) implementing Peter Norvig's edit-distance candidate scoring, alongside a curated developer lexicon.
* **Now**:
  * Input: `"Also please crete a develop branch because I wasn other develoeprs to contribute on this tool so would be great if we have the develpo branch updatodate and follwo the git stndard rules."`
  * Output: `"Also, please create a develop branch because I want other developers to contribute to this tool so it would be great if we have the develop branch up to date and follow standard Git rules."`

---

### Q: How do I run a 100% private, offline AI model with Ollama?
A: Run our 1-click setup script:
```bash
bash scripts/setup_ollama.sh
```
This script checks/installs Ollama, starts the daemon, and pulls the lightweight `qwen2.5:0.5b` model (~390MB, sub-second responses). Once active, `dev-refine-sentences` automatically detects Ollama and uses it as the primary offline engine.

---

## macOS & Local Models

### Q: What is the macOS hotkey, and how do I change it?
A: Default **`Ctrl+Option+R`**. Run `python3 main.py --set-hotkey "cmd+shift+e"` or use the web Settings page. It applies live, with no restart. Syntax: modifiers (`ctrl`, `alt`, `shift`, `cmd`) plus one letter; add `*2` for a double tap (e.g. `cmd+a*2`).

### Q: Can I use two letters, like A and R together?
A: No. macOS global hotkeys support modifiers plus a single key. Use a double tap (`*2`) instead.

### Q: Is `cmd+a*2` (double Cmd+A) safe?
A: It works, but it refines the **whole text field** (Cmd+A selects everything), and a habitual double Cmd+A will rewrite your text. Cmd+Z undoes it. It also needs **Input Monitoring** permission. `ctrl+alt+a*2` is safer.

### Q: Why does it say "Accessibility not granted" although I enabled Python?
A: Enable the exact `Python.app` under System Settings > Privacy & Security > Accessibility, then **restart the listener** (`launchctl kickstart -k gui/$(id -u)/com.refine.hotkey`). If you start the listener from inside another app, macOS may check that app instead; the LaunchAgent avoids this.

### Q: It worked in TextEdit via a Quick Action but not in Claude desktop or Google Chat. Why?
A: macOS Services (Quick Actions) are not supported by Electron apps or web editors. The global hotkey listener does not use Services, so it works everywhere.

### Q: Which local model should I use?
A: Default `qwen2.5:3b` (~2 GB, 1-2 s) or lightweight `qwen2.5:0.5b` (~390MB, <1s). Large models (e.g. 9.6 GB `gemma4`) can take **minutes** on a 16 GB Mac under memory pressure. Change with `--set-model NAME` or the Settings page; list installed models with `ollama list`.

### Q: It is very slow, what do I check?
A: `ollama ps` (what is loaded), `sysctl vm.swapusage` (is the Mac swapping?), then use a smaller model and quit heavy apps (iOS Simulator, Docker).

### Q: Can Claude desktop be refined with a Chrome extension?
A: No. A Chrome extension only reaches web pages. The hotkey listener covers native and Electron apps.

### Q: Does the web Settings page expose my API keys?
A: No. The API reports only whether a key is configured, and keys can only be set via the CLI or environment variables. Writes are accepted only from the local portal itself.


