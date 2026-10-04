"""Offline spelling correction engine and developer lexicon.

100% Python Standard Library. Zero external dependencies.
Uses Norvig edit-distance candidate ranking + curated developer dictionary.
"""

import re
import os
from collections import Counter
from typing import Dict, List, Set, Tuple, Optional, Any


# Common known typo mappings (immediate O(1) resolution)
COMMON_TYPOS: Dict[str, str] = {
    # Portmanteaus and compound phrases
    "updatodate": "up to date",
    "uptodate": "up to date",
    "cantwait": "can't wait",
    "alot": "a lot",
    "noone": "no one",
    "asap": "as soon as possible",
    "fyi": "for your information",
    "btw": "by the way",
    "inorder": "in order",
    
    # Common typing slips & transposed letters
    "crete": "create",
    "develpo": "develop",
    "develoepr": "developer",
    "develoeprs": "developers",
    "follwo": "follow",
    "stndard": "standard",
    "stnadard": "standard",
    "comit": "commit",
    "comits": "commits",
    "branhc": "branch",
    "branhces": "branches",
    "funciton": "function",
    "funcitons": "functions",
    "pakcage": "package",
    "libary": "library",
    "direcotry": "directory",
    "configuraiton": "configuration",
    "configuraion": "configuration",
    "notificaiton": "notification",
    "widnows": "windows",
    "descriptom": "description",
    "descripton": "description",
    "sentnece": "sentence",
    "sentneces": "sentences",
    "oyu": "you",
    "teh": "the",
    "thier": "their",
    "recieve": "receive",
    "recieved": "received",
    "seperate": "separate",
    "definately": "definitely",
    "occured": "occurred",
    "untill": "until",
    "calender": "calendar",
    "truely": "truly",
    "accomodate": "accommodate",
    "reponse": "response",
    "reqeust": "request",
    "artfact": "artifact",
    "artfacts": "artifacts",
    "shrotcut": "shortcut",
    "shrotcuts": "shortcuts",
    "daemno": "daemon",
    "scren": "screen",
    "clikc": "click",
    "pastd": "pasted",
    "runing": "running",
}

# Core English and software engineering vocabulary with frequency weights
BASE_VOCABULARY: Dict[str, int] = {
    # High frequency function words
    "the": 10000, "be": 8000, "is": 9500, "am": 8500, "are": 9000, "was": 8000, "were": 7500,
    "been": 7000, "being": 6500, "has": 7000, "had": 7000, "done": 6000, "did": 6500,
    "step": 2000, "ready": 2000, "send": 2500, "sent": 2000, "worry": 1500,
    "to": 9000, "of": 7500, "and": 7000, "a": 7000, "in": 6500,
    "that": 6000, "have": 5500, "i": 5000, "it": 5000, "for": 4800, "not": 4600, "on": 4500,
    "with": 4400, "he": 4200, "as": 4000, "you": 4000, "do": 3800, "at": 3600, "this": 3500,
    "but": 3400, "his": 3300, "by": 3200, "from": 3100, "they": 3000, "we": 2900, "say": 2800,
    "her": 2700, "she": 2600, "or": 2500, "an": 2400, "will": 2300, "my": 2200, "one": 2100,
    "all": 2000, "would": 1900, "there": 1800, "their": 1700, "what": 1600, "so": 1500,
    "up": 1400, "out": 1300, "if": 1200, "about": 1100, "who": 1000, "get": 1000, "which": 950,
    "go": 900, "me": 850, "when": 800, "make": 750, "can": 700, "like": 680, "time": 660,
    "no": 640, "just": 620, "him": 600, "know": 580, "take": 560, "people": 540, "into": 520,
    "year": 500, "your": 480, "good": 460, "some": 440, "could": 420, "them": 400, "see": 380,
    "other": 360, "than": 340, "then": 320, "now": 300, "look": 290, "only": 280, "come": 270,
    "its": 260, "over": 250, "think": 240, "also": 230, "back": 220, "after": 210, "use": 200,
    "two": 190, "how": 180, "our": 170, "work": 160, "first": 150, "well": 140, "way": 130,
    "even": 120, "new": 110, "want": 500, "because": 450, "any": 400, "these": 380, "give": 360,
    "day": 340, "most": 320, "us": 300, "great": 450, "please": 550, "help": 400, "need": 420,
    "should": 390, "date": 350, "update": 500, "rules": 450, "rule": 420, "follow": 480,
    
    # Software engineering & developer domain lexicon
    "git": 800, "branch": 600, "branches": 550, "develop": 650, "developer": 700, "developers": 750,
    "development": 500, "create": 700, "created": 600, "creating": 550, "standard": 600, "standards": 550,
    "commit": 650, "commits": 600, "committed": 550, "push": 600, "pull": 600, "merge": 550,
    "rebase": 500, "checkout": 450, "repository": 600, "repositories": 500, "repo": 650, "repos": 500,
    "remote": 550, "origin": 500, "main": 600, "master": 450, "feature": 550, "features": 500,
    "bug": 500, "bugfix": 500, "fix": 600, "fixed": 550, "fixes": 500, "issue": 550, "issues": 500,
    "code": 750, "coding": 500, "test": 700, "tests": 650, "testing": 600, "tested": 550,
    "tool": 700, "tools": 650, "project": 700, "projects": 600, "contribute": 550, "contributed": 500,
    "contributing": 500, "contributor": 500, "contributors": 500, "review": 550, "request": 600,
    "requests": 550, "response": 600, "responses": 550, "daemon": 500, "service": 600, "services": 550,
    "server": 650, "servers": 550, "client": 600, "clients": 550, "api": 700, "apis": 600,
    "sdk": 500, "library": 600, "libraries": 550, "package": 600, "packages": 550, "module": 600,
    "modules": 550, "function": 650, "functions": 600, "method": 600, "methods": 550, "class": 600,
    "classes": 550, "object": 550, "objects": 500, "file": 650, "files": 600, "directory": 600,
    "directories": 550, "folder": 550, "folders": 500, "script": 600, "scripts": 550, "command": 600,
    "commands": 550, "terminal": 550, "shell": 550, "bash": 500, "python": 600, "linux": 550,
    "windows": 550, "macos": 500, "macbook": 450, "shortcut": 550, "shortcuts": 500, "key": 550,
    "keyboard": 500, "screen": 500, "window": 550, "modal": 500, "popup": 500, "paste": 550,
    "copy": 550, "clipboard": 600, "notification": 550, "notifications": 500, "config": 600,
    "configuration": 550, "settings": 600, "system": 650, "version": 600, "build": 600,
    "status": 600, "online": 500, "offline": 500, "engine": 550, "refine": 600, "sentence": 600,
    "sentences": 550, "text": 650, "word": 600, "words": 550, "grammar": 550, "spelling": 550,
}


class SpellingEngine:
    """Norvig Edit-Distance Spell Checker with Developer Vocabulary."""

    def __init__(self, load_system_dict: bool = True):
        self.words: Counter = Counter(BASE_VOCABULARY)
        self.alphabet: str = "abcdefghijklmnopqrstuvwxyz"
        self._compiled_typos = {
            re.compile(rf"\b{re.escape(k)}\b", re.IGNORECASE): (k, v)
            for k, v in COMMON_TYPOS.items()
        }

        if load_system_dict:
            self._load_system_words()

    def _load_system_words(self) -> None:
        """Optionally load valid words from standard Unix dictionary."""
        dict_paths = ["/usr/share/dict/words", "/usr/dict/words"]
        for p in dict_paths:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            w = line.strip().lower()
                            if w.isalpha() and 3 <= len(w) <= 20 and w not in self.words:
                                self.words[w] = 10
                    break
                except Exception:
                    pass

    def is_protected_token(self, token: str) -> bool:
        """Check if token is an identifier, number, code, acronym, or URL."""
        if not token:
            return True
        # Numbers or versions like v1.2.0 or 123
        if re.search(r"\d", token):
            return True
        # Code identifiers (snake_case, kebab-case, paths, URLs)
        if any(ch in token for ch in ["_", "-", "/", "\\", ".", ":", "@"]):
            return True
        # camelCase or PascalCase
        if token[1:].lower() != token[1:] and not token.isupper():
            return True
        # Short uppercase acronyms (API, PR, UI, SDK, CLI, RAM, CPU)
        if token.isupper() and len(token) <= 5:
            return True
        # Single letters other than 'a' and 'i'
        if len(token) == 1 and token.lower() not in ("a", "i"):
            return True
        return False

    def _edits1(self, word: str) -> Set[str]:
        """Generate all edits that are one edit distance away from `word`."""
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [L + R[1:] for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
        replaces = [L + c + R[1:] for L, R in splits if R for c in self.alphabet]
        inserts = [L + c + R for L, R in splits for c in self.alphabet]
        return set(deletes + transposes + replaces + inserts)

    def _edits2(self, word: str) -> Set[str]:
        """Generate all edits that are two edit distances away from `word`."""
        return set(e2 for e1 in self._edits1(word) for e2 in self._edits1(e1) if e2 in self.words)

    def correct_word(self, word: str, whitelist: Optional[List[str]] = None) -> Tuple[str, bool]:
        """Suggest correction for a single word. Returns (corrected_word, changed)."""
        if self.is_protected_token(word):
            return word, False

        # Check user whitelist
        if whitelist:
            for wl in whitelist:
                if word.lower() == wl.lower():
                    return word, False

        w_lower = word.lower()

        # Check explicit typo map
        if w_lower in COMMON_TYPOS:
            replacement = COMMON_TYPOS[w_lower]
            return self._match_case(word, replacement), True

        # Words with length < 4 should never be modified by edit distance
        if len(w_lower) < 4:
            return word, False

        # If already a valid word in vocabulary, leave intact
        if w_lower in self.words:
            return word, False

        # Look for edit distance 1 candidates
        e1_candidates = [cand for cand in self._edits1(w_lower) if cand in self.words]
        if e1_candidates:
            best = max(e1_candidates, key=lambda c: self.words[c])
            return self._match_case(word, best), True

        # If word is long enough, try edit distance 2 candidates
        if len(w_lower) >= 5:
            e2_candidates = list(self._edits2(w_lower))
            if e2_candidates:
                best = max(e2_candidates, key=lambda c: self.words[c])
                return self._match_case(word, best), True

        return word, False

    def correct_phrase_typos(self, text: str) -> Tuple[str, List[Tuple[str, str]]]:
        """Apply pre-compiled known compound/portmanteau typo mappings."""
        corrections: List[Tuple[str, str]] = []
        result = text
        for rx, (orig, repl) in self._compiled_typos.items():
            if rx.search(result):
                result = rx.sub(repl, result)
                corrections.append((orig, repl))
        return result, corrections

    def correct_text(
        self, text: str, whitelist: Optional[List[str]] = None
    ) -> Tuple[str, List[Tuple[str, str]]]:
        """Run complete spell-checking pass on sentence preserving delimiters."""
        # 1. Quick phrase/compound substitution
        result, phrase_corrections = self.correct_phrase_typos(text)
        all_corrections: List[Tuple[str, str]] = list(phrase_corrections)

        # 2. Tokenize into words and non-words
        tokens = re.split(r"(\b[A-Za-z0-9_-]+\b)", result)
        changed_any = False
        new_tokens = []

        for token in tokens:
            if re.match(r"^[A-Za-z]+$", token):
                corrected, changed = self.correct_word(token, whitelist=whitelist)
                if changed:
                    all_corrections.append((token, corrected))
                    new_tokens.append(corrected)
                    changed_any = True
                else:
                    new_tokens.append(token)
            else:
                new_tokens.append(token)

        final_text = "".join(new_tokens) if changed_any else result
        return final_text, all_corrections

    def _match_case(self, original: str, replacement: str) -> str:
        """Preserve case pattern of original word in replacement."""
        if original.isupper():
            return replacement.upper()
        if original.istitle():
            return replacement.capitalize()
        return replacement
