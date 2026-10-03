# Universal Sentence Refiner

A fast, system-wide sentence refinement tool designed to emulate Google Chat's text refinement feature across **any** input field on Linux (including Antigravity IDE, Google Chrome, Firefox, Claude web, ChatGPT web, Slack, LibreOffice, and terminals).

Built with **100% Python Standard Library** (zero third-party pip dependencies). Supports completely offline rule-based polishing, local offline models (Ollama/LanguageTool), and optional cloud AI API keys (**Google Gemini**, **OpenAI ChatGPT**, **Anthropic Claude**).

---

## 🌟 Key Features

1. **Universal Input Field Support (Browser, Antigravity, Claude, ChatGPT, etc.)**:
   - Highlight text anywhere with your mouse or keyboard (`Shift + Arrows`).
   - Automatically captures highlighted text using Linux `PRIMARY` selection and native GNOME `Atspi` event hooks.
   - **Zero manual copying required**!
2. **Immediate Refinement & In-Place Text Replacement**:
   - Press the global shortcut (`Ctrl + Alt + R`).
   - The tool immediately captures the highlighted text, runs refinement, and opens the suggestion modal.
   - Press **Enter** (or click **Apply & Copy**): the tool automatically pastes (`Ctrl+V`) the refined text over your selection in the active input box!
3. **Visual Word-by-Word Diff (Like Google Chat)**:
   - Floating popup highlights exact modified words: <span style="color:#F38BA8">red strikethrough</span> for deletions, <span style="color:#A6E3A1">green bold</span> for corrections.
   - Toggle seamlessly between **Diff View** and **Direct Editor** (`Alt+D`).
4. **Teach Mode ("Why Changed?")**:
   - Explains the exact grammatical rules, typos, and style improvements made (e.g. *"Grammar: Subject-verb agreement: third-person singular uses 'goes'"* or *"Conciseness: Removed filler word 'basically'"*).
5. **Linguistic & Readability Metrics**:
   - Live **Flesch Reading Ease** score (e.g. *85.2 - Very Easy*), **Flesch-Kincaid Grade Level**, word counts, and estimated reading time.
6. **Interactive GUI Settings Dialog**:
   - Click `[⚙️ Settings]` directly inside the popup to add/edit API keys, whitelist terms, and snippets with zero terminal commands needed.
7. **Dynamic Snippet Template Variables (Espanso-style)**:
   - Snippets support live variables: `{{date}}`, `{{time}}`, `{{year}}`, `{{day}}`. (e.g. `meet` → *"Meeting on {{day}} at {{time}}"*).
8. **One-Key Instant Flash Mode (`refine_flash.sh`)**:
   - Bypass all dialogs for ultra-fast, 50ms in-place replacement.
9. **Pluggable Engine Architecture (Offline & Cloud AI)**:
   - **Built-in Rule Engine** (Default, 100% offline, zero config, instant).
   - **Google Gemini API** (`gemini-1.5-flash`, `gemini-1.5-pro` via stdlib `urllib`).
   - **OpenAI / ChatGPT API** (`gpt-4o-mini`, `gpt-4o` via stdlib `urllib`).
   - **Anthropic Claude API** (`claude-3-5-haiku`, `claude-3-5-sonnet` via stdlib `urllib`).
   - **Local Ollama Connector** (Offline local models like `qwen2.5:0.5b`).
   - **Local LanguageTool Server** (Offline rule server).
   - **Live Engine Switcher**: Switch engines directly inside the GUI popup!
10. **Multi-Tone Expansion**:
    - **Standard**: Polishes grammar, typos, capitalization, and punctuation.
    - **Concise**: Eliminates fluff, filler words, and awkward redundancies.
    - **Professional**: Converts informal slang and contractions into formal phrasing.
    - **Friendly**: Warms tone and softens imperative orders.
    - **Bullets**: Reorganizes clauses into clean markdown bullet points (`- ...`).
    - **Email**: Auto-wraps sentence with professional greeting and sign-off.
11. **Refinement History & Undo Buffer**:
    - Automatically saves past refinements to `~/.config/refine_tool/history.json`.
    - Restore past snippets right from the popup dropdown or via `--history`.

---

## 📁 Project Structure

```
dev-refine-sentences/
├── refiner/                      # Domain sub-package: Refinement engines
│   ├── __init__.py               # Package exports
│   ├── base.py                   # Abstract BaseRefiner interface
│   ├── rules.py                  # 100% stdlib rule engine (Teach mode + templates + whitelist)
│   ├── gemini.py                 # Google Gemini API connector (stdlib urllib)
│   ├── openai.py                 # OpenAI / ChatGPT API connector (stdlib urllib)
│   ├── claude.py                 # Anthropic Claude API connector (stdlib urllib)
│   ├── ollama.py                 # Local Ollama HTTP connector (stdlib urllib)
│   ├── languagetool.py           # Local LanguageTool HTTP connector
│   └── manager.py                # Engine registry, auto-resolver, and explanation getter
├── metrics/                      # Domain sub-package: Readability & metrics
│   ├── __init__.py               # Package exports
│   └── readability.py            # Flesch-Kincaid Reading Ease, Grade Level, syllable counter
├── config/                       # Domain sub-package: User settings & whitelist
│   ├── __init__.py               # Package exports
│   └── settings.py               # Whitelist, dynamic snippets, API keys, and config manager
├── history/                      # Domain sub-package: Audit & undo logs
│   ├── __init__.py               # Package exports
│   └── history_manager.py        # Persistent history log manager
├── clipboard/                    # Domain sub-package: Clipboard management
│   ├── __init__.py               # Package exports
│   └── manager.py                # Primary selection & Wayland/X11 clipboard wrapper
├── injector/                     # Domain sub-package: OS keystrokes & alerts
│   ├── __init__.py               # Package exports
│   └── injector.py               # Atspi Wayland key event injection & notify-send handler
├── ui/                           # Domain sub-package: User Interface
│   ├── __init__.py               # Package exports
│   ├── diff_highlighter.py       # Stdlib difflib word-level diff tokenizer
│   ├── settings_dialog.py        # Tkinter Settings modal (API keys, whitelist, snippets)
│   └── popup.py                  # Tkinter floating preview modal with visual diff & teach mode
├── tests/                        # Unit test suite
│   ├── __init__.py               # Package exports
│   └── test_all.py               # Comprehensive unit tests (16 tests)
├── main.py                       # CLI orchestrator & entry point
├── refine_trigger.sh             # Shell wrapper for OS global hotkey (Popup modal)
├── refine_flash.sh               # Shell wrapper for OS global hotkey (Instant silent replace)
├── ARCHITECTURE.md               # Architectural specification & component flow
├── FAQ.md                        # Common questions & troubleshooting
└── README.md                     # Project documentation
```

---

## ⌨️ Setup Hotkeys in Ubuntu GNOME (Wayland)

Open **Settings** -> **Keyboard** -> **View and Customize Shortcuts** -> **Custom Shortcuts**:

1. **Refine Sentence (Suggestion Preview + Replace)**:
   * **Name**: `Refine Sentence`
   * **Command**: `/home/sunil-bakale/IdeaProjects/dev-refine-sentences/refine_trigger.sh`
   * **Shortcut**: `Ctrl + Alt + R`
2. **Instant Silent Flash Mode (Zero Dialog In-Place Replace)**:
   * **Name**: `Refine Sentence Flash`
   * **Command**: `/home/sunil-bakale/IdeaProjects/dev-refine-sentences/refine_flash.sh`
   * **Shortcut**: `Super + Shift + R`

---

## 🔄 Universal Workflow in Any Application

Works identically in **Antigravity IDE**, **Google Chrome**, **Firefox**, **ChatGPT**, **Claude**, **Slack**, or **Terminal**:

1. **Highlight rough text** in any text input field (using mouse drag or `Shift + Arrow`).
2. **Press your shortcut** (`Ctrl + Alt + R`).
3. **Inspect suggestion**:
   - The tool immediately pops up showing the **Visual Word Diff** (<span style="color:#F38BA8">deleted typos</span>, <span style="color:#A6E3A1">added fixes</span>).
   - Shows **Teach Mode** explanation (why it was changed).
   - Shows **Readability score** (e.g. *Very Easy - Grade 1*).
4. **Hit Enter**:
   - The window closes and immediately pastes the refined version over your selected text!
