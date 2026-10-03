# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
