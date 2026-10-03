# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-10-03

### Added
- **Sub-5ms Resident Daemon (`--daemon`)**:
  - Persistent UNIX domain socket daemon (`~/.config/refine_tool/daemon.sock`) keeping modules, regexes, and clipboard hot in RAM.
  - Slashes cold startup latency from 50ms to 0.2ms–2ms.
  - Automatic fallback to standalone execution if daemon is stopped.
- **Pre-Compiled Regex Performance Suite**:
  - All typo, grammar, concise redundancy, and tone regexes pre-compiled at import time.
  - Throughput exceeds 11,000 sentences per second (86µs per sentence).
- **In-Memory LRU Cache & Tone Prefetching**:
  - Instant 0.2ms resolution for cached sentences.
  - Parallel background tone prefetching in Tkinter modal enabling 0ms instantaneous tone switching.
- **Zero-Sudo User Installer & Systemd User Service**:
  - `packaging/install_user.sh` installs to `~/.local/bin` and activates a persistent `systemd --user` daemon service.
  - Debian `.deb` package now installs `/usr/lib/systemd/user/refine-daemon.service`.
- **Extended Shorthand Vocabulary**:
  - Added expansions for `pls`, `asap`, `btw`, `fyi`, `rn`, `tmrw`, `yday`, `msg`.
- **Interactive Web Portal & Developer Documentation Hub (`index.html`)**:
  - Complete documentation and interactive playground portal with live word diff, Teach mode explanations, and readability metrics.
  - Fully offline capable in static browser mode, and live connected when served.
- **Built-in Stdlib Documentation Server (`web_server/`)**:
  - Launch with `python3 main.py --serve [PORT]` to serve portal locally.
  - Connects web `/api/refine` requests directly to resident daemon socket in RAM.
- **Modular Frontend Architecture (`web/`)**:
  - Structured domain modules: `web/js/modules/diff.js`, `metrics.js`, `rules_engine.js`, `api_client.js`, `tabs.js`, and `app.js`.
- **1-Click Service Management Scripts**:
  - `start.sh`, `stop.sh`, `restart.sh`, `status.sh` (plus `.start.sh`, `.stop.sh`, etc. aliases) to manage daemon and web portal with single commands.

## [1.1.0] - 2026-10-03

### Added
- **Smart Float-at-Cursor Positioning**:
  - Modal automatically aligns with mouse pointer coordinates (`winfo_pointerxy`), appearing right next to highlighted text (Raycast / PopClip style).
- **Single-Key Lightning Navigation**:
  - `1`-`6` for instantaneous tone switching.
  - `y` / `Enter` to apply and replace in-place.
  - `n` / `Esc` to dismiss.
- **Sensory Sound Confirmation**:
  - Added subtle audio chime (`canberra-gtk-play`) on in-place replacement.
- **Debian Packaging**:
  - Added `packaging/build_deb.sh` script generating standalone `.deb` package (`dist/refine-sentences_1.0.0_all.deb`).

## [1.0.0] - 2026-10-03

### Added
- **Core Engine**:
  - Deterministic rule-based sentence polisher with 100% Python Standard Library.
  - Multi-engine resolution manager (Ollama, LanguageTool, Gemini, OpenAI, Claude, Rules).
- **Universal Text Replacement**:
  - Wayland and X11 PRIMARY selection buffer integration.
  - Native Linux Atspi accessibility keyboard generator for automatic `Ctrl+C` capture and `Ctrl+V` replacement.
- **Visual Word-by-Word Diff**:
  - Word tokenizer using `difflib.SequenceMatcher`.
  - Red strikethrough for deleted text and green bold for additions.
  - `Alt+D` toggle between Diff View and Direct Editor.
- **Teach Mode**:
  - Explains the exact grammatical, typographical, and stylistic rationale behind changes.
- **Linguistic & Readability Metrics**:
  - Flesch Reading Ease score calculation.
  - Flesch-Kincaid Grade Level index.
  - Word count and reading time estimator.
- **Interactive Settings GUI**:
  - Tabbed settings dialog to manage API keys, whitelist words, and custom snippets.
- **Dynamic Text Snippets**:
  - Espanso-style template variables (`{{date}}`, `{{time}}`, `{{year}}`, `{{day}}`).
- **Tones**:
  - Standard, Concise, Professional, Friendly, Bullet Points, and Email Formal.
- **Refinement History & Undo**:
  - Persistent audit log storing last 50 refinements.
- **Instant Flash Trigger**:
  - `refine_flash.sh` for 50ms silent in-place text replacement without dialogs.
