# Architecture & System Design: Universal Sentence Refiner

This document describes the architectural design, component interactions, and execution lifecycle of the Universal Sentence Refiner.

---

## 1. Architectural Principles & Constraints

1. **Zero Third-Party Pip Packages**:
   The entire backend is built strictly using the Python 3 standard library (`re`, `urllib.request`, `tkinter`, `difflib`, `subprocess`, `argparse`, `shutil`, `json`, `pathlib`, `os`, `time`).
2. **Dual-Path Intelligence (Offline + Cloud AI)**:
   - **Offline Path**: Fully private deterministic rule engine with explanation tracking ("Teach Mode"), local Ollama daemon, or local LanguageTool server.
   - **Cloud AI Path**: Native HTTPS client (`urllib.request`) connecting directly to Google Gemini, OpenAI (ChatGPT), and Anthropic (Claude) without third-party SDKs.
3. **Cross-Application Interoperability**:
   Works universally across any application running on Linux (Electron apps like Antigravity IDE/Slack/VS Code, Chromium/Firefox browsers, native GTK/Qt applications, and terminals).
4. **Clean Domain Separation**:
   Code is partitioned into focused, single-responsibility subpackages:
   - `refiner/`: NLP, rule-based polisher, Teach mode explanations, and AI API connectors.
   - `metrics/`: Linguistic readability analysis (Flesch Reading Ease, Grade Level).
   - `config/`: Configuration, whitelist, dynamic snippets expander, and API keys.
   - `history/`: Persistent audit logging and undo buffer.
   - `clipboard/`: Cross-environment clipboard extraction and population.
   - `injector/`: OS-level keystroke injection and desktop notifications.
   - `ui/`: Desktop graphical user interface (Tkinter), diff tokenizer, and settings dialog.
   - `tests/`: Automated unit test suite.

---

## 2. Component Flow Diagram

```mermaid
flowchart TD
    subgraph OS_Environment ["Linux OS / Desktop Environment"]
        UserAction["User Selects Text in Any Input Field"]
        HotKeyPopup["Popup Shortcut (Ctrl+Alt+R)"]
        HotKeyFlash["Flash Shortcut (Super+Shift+R)"]
        TriggerPopup["refine_trigger.sh"]
        TriggerFlash["refine_flash.sh"]
    end

    subgraph Core_Application ["Python Core Application (main.py)"]
        Manager["refiner.RefinerManager"]
        ConfigMgr["config.ConfigManager"]
        HistoryMgr["history.HistoryManager"]
        ClipboardMgr["clipboard.ClipboardManager"]
        KeyInj["injector.KeyInjector"]
        DiffEngine["ui.diff_highlighter"]
        MetricsEngine["metrics.readability"]
        PopupUI["ui.RefinePopup (Tkinter)"]
        SettingsUI["ui.SettingsDialog"]

        subgraph Local_Engines ["Local & Offline Engines"]
            RuleEngine["RuleBasedRefiner (Teach Mode + Templates + Whitelist)"]
            OllamaEngine["OllamaRefiner (Local HTTP)"]
            LTEngine["LanguageToolRefiner (Local HTTP)"]
        end

        subgraph Cloud_Engines ["Cloud AI Engines (Zero-Pip HTTPS)"]
            GeminiEngine["GeminiRefiner (gemini-1.5-flash)"]
            OpenAIEngine["OpenAIRefiner (gpt-4o-mini)"]
            ClaudeEngine["ClaudeRefiner (claude-3-5-haiku)"]
        end
    end

    UserAction --> HotKeyPopup
    UserAction --> HotKeyFlash
    HotKeyPopup --> TriggerPopup
    HotKeyFlash --> TriggerFlash
    TriggerPopup --> Core_Application
    TriggerFlash --> Core_Application

    Core_Application --> ClipboardMgr
    ClipboardMgr -->|Read raw text| Manager
    ConfigMgr -->|API Keys & Whitelist| Manager

    Manager -->|Default Auto| RuleEngine
    Manager -.->|Optional Key| GeminiEngine
    Manager -.->|Optional Key| OpenAIEngine
    Manager -.->|Optional Key| ClaudeEngine
    Manager -.->|Optional Daemon| OllamaEngine
    Manager -.->|Optional Daemon| LTEngine

    Local_Engines -->|Refined text| DiffEngine
    Cloud_Engines -->|Refined text| DiffEngine
    DiffEngine -->|Word diff tokens| PopupUI
    RuleEngine -->|Explanations| PopupUI
    MetricsEngine -->|Readability & Ease| PopupUI
    HistoryMgr -->|Past entries| PopupUI
    PopupUI -->|Settings button| SettingsUI

    PopupUI -->|User applies edit| HistoryMgr
    PopupUI -->|Final text| ClipboardMgr
    ClipboardMgr -->|Write refined text| KeyInj
    KeyInj -->|Paste / Notify| UserAction
```

---

## 3. Subpackage Breakdown

### `refiner/`
- [`base.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/refiner/base.py): Abstract `BaseRefiner` interface.
- [`rules.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/refiner/rules.py): Offline deterministic NLP rules engine with whitelist masking, dynamic snippet expansion (`{{date}}`, `{{time}}`, `{{year}}`), typo resolution, grammar correction, and Teach Mode explanation tracking.
- [`gemini.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/refiner/gemini.py): Standard library HTTP client for Google Gemini API.
- [`openai.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/refiner/openai.py): Standard library HTTP client for OpenAI API.
- [`claude.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/refiner/claude.py): Standard library HTTP client for Anthropic Claude API.
- [`ollama.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/refiner/ollama.py): Standard library HTTP client for local Ollama instances.
- [`languagetool.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/refiner/languagetool.py): Standard library HTTP client for local LanguageTool server.
- [`manager.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/refiner/manager.py): Engine coordinator providing automatic fallback resolution across offline and cloud backends.

### `metrics/`
- [`readability.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/metrics/readability.py): Flesch Reading Ease, Flesch-Kincaid Grade Level, and syllable counter.

### `config/`
- [`settings.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/config/settings.py): Manages `~/.config/refine_tool/config.json`, technical term whitelist, shortcut snippet expansions, and API keys.

### `history/`
- [`history_manager.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/history/history_manager.py): Persistent audit log and undo buffer storing the last 50 refinements.

### `clipboard/`
- [`manager.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/clipboard/manager.py): Universal clipboard interface with multi-backend fallback.

### `injector/`
- [`injector.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/injector/injector.py): Keystroke injection via `ydotool`, `wtype`, or `xdotool`. Sends desktop notifications via `notify-send`.

### `ui/`
- [`diff_highlighter.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/ui/diff_highlighter.py): Word-level diff tokenizer powered by `difflib.SequenceMatcher`.
- [`settings_dialog.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/ui/settings_dialog.py): Tabbed settings GUI for keys, whitelist, and snippets.
- [`popup.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/ui/popup.py): Clean, dark-mode Tkinter modal providing live word diff rendering, Teach Mode explanations, readability metrics, and tone selection.

### `tests/`
- [`test_all.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/tests/test_all.py): Unit test suite covering all domains and functionality (16 passing tests).
