# Contributing to Universal Sentence Refiner

First off, thank you for considering contributing to Universal Sentence Refiner! 🎉 

This project aims to provide a lightweight, system-wide sentence refinement tool that works across any input field on Linux with **zero external pip dependencies**.

---

## 🏛️ Guiding Architectural Principles

Before writing code, please review our core architectural rules:

1. **Zero Third-Party Pip Dependencies (Mandatory)**:
   - The entire core must rely **100% on the Python Standard Library** (`re`, `urllib.request`, `tkinter`, `difflib`, `subprocess`, `argparse`, `json`, `pathlib`).
   - Do **not** add `requirements.txt` with external pip dependencies like `requests`, `openai`, `google-generativeai`, `pydantic`, etc. Use native stdlib equivalents.
2. **Modular Architecture Standards**:
   - Maintain a clean, minimal root directory.
   - Group related domain utilities into dedicated sub-packages with an `__init__.py` (e.g. `refiner/`, `metrics/`, `config/`, `history/`, `clipboard/`, `injector/`, `ui/`).
   - If refactoring or moving modules, provide zero-breakage backward compatibility shims.
3. **Living Documentation**:
   - Whenever modules or features are added or changed, update `README.md`, `ARCHITECTURE.md`, and `FAQ.md`.

---

## 🛠️ Development Setup

No virtual environment or `pip install` is required! All you need is Python 3.9+ installed on your Linux machine.

```bash
# Clone the repository
git clone https://github.com/your-username/dev-refine-sentences.git
cd dev-refine-sentences

# Run the test suite
python3 -m unittest discover -s tests -p "test_*.py"
```

---

## 🧪 Running & Adding Tests

Every new feature or rule enhancement must include unit tests in `tests/test_all.py`.

To run all unit tests:
```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

All tests must pass before submitting a pull request.

---

## 💡 How to Add New Rules or Tones

### 1. Adding a Grammar or Typo Rule
Open [`refiner/rules.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/refiner/rules.py):
* For typo corrections, add an entry to `TYPO_MAP`:
  ```python
  r"\bteh\b": "the",
  ```
* For grammar corrections with Teach Mode explanations, add an entry to `GRAMMAR_FIXES`:
  ```python
  (r"\b(he|she|it)\s+go\b", r"\1 goes", "Subject-verb agreement: singular takes 'goes'."),
  ```

### 2. Adding an AI Model Connector
Create a new file in `refiner/` inheriting from `BaseRefiner` in [`refiner/base.py`](file:///home/sunil-bakale/IdeaProjects/dev-refine-sentences/refiner/base.py) using `urllib.request`.

---

## 📬 Pull Request Process

1. Fork the repo and create your branch from `main`:
   ```bash
   git checkout -b feature/amazing-feature
   ```
2. Make your changes adhering to the Zero-Pip standard.
3. Run the test suite to ensure all unit tests pass:
   ```bash
   python3 -m unittest discover -s tests -p "test_*.py"
   ```
4. Commit with clean, descriptive commit messages:
   ```bash
   git commit -m "feat(refiner): add rule for conditional clauses"
   ```
5. Push to your fork and submit a Pull Request!
