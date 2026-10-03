"""Readability and linguistic metrics calculator.

100% Python Standard Library. Zero external dependencies.
"""

import re
from typing import Dict, Any


def count_syllables(word: str) -> int:
    """Estimate the number of syllables in an English word."""
    word = word.lower().strip()
    if not word:
        return 0
    if len(word) <= 3:
        return 1

    # Remove non-alphabetic characters
    word = re.sub(r"[^a-z]", "", word)
    if not word:
        return 1

    # Count vowel groups
    vowels = "aeiouy"
    count = 0
    prev_is_vowel = False

    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel

    # Adjust for silent 'e' at end of word
    if word.endswith("e") and not word.endswith("le") and len(word) > 2:
        count -= 1

    # Adjust for 'ed' endings that don't add syllables
    if word.endswith("ed") and not (word.endswith("ted") or word.endswith("ded")):
        count -= 1

    return max(1, count)


def analyze_readability(text: str) -> Dict[str, Any]:
    """Calculate Flesch Reading Ease, Flesch-Kincaid Grade Level, and text metrics."""
    if not text or not text.strip():
        return {
            "words": 0,
            "sentences": 0,
            "syllables": 0,
            "reading_ease": 100.0,
            "grade_level": 0.0,
            "reading_time_sec": 0,
            "label": "Empty",
        }

    raw = text.strip()
    words = re.findall(r"\b\w+\b", raw)
    word_count = len(words)
    if word_count == 0:
        return {
            "words": 0,
            "sentences": 0,
            "syllables": 0,
            "reading_ease": 100.0,
            "grade_level": 0.0,
            "reading_time_sec": 0,
            "label": "Empty",
        }

    # Sentences split by terminating punctuation
    sentences = re.split(r"[.!?]+", raw)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = max(1, len(sentences))

    # Syllables total
    syllable_count = sum(count_syllables(w) for w in words)

    # Flesch Reading Ease: 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
    words_per_sentence = word_count / sentence_count
    syllables_per_word = syllable_count / word_count
    ease = 206.835 - (1.015 * words_per_sentence) - (84.6 * syllables_per_word)
    ease = round(max(0.0, min(100.0, ease)), 1)

    # Flesch-Kincaid Grade Level: 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59
    grade = (0.39 * words_per_sentence) + (11.8 * syllables_per_word) - 15.59
    grade = round(max(0.0, grade), 1)

    # Human-friendly ease description
    if ease >= 80:
        label = "Very Easy"
    elif ease >= 70:
        label = "Fairly Easy"
    elif ease >= 60:
        label = "Standard"
    elif ease >= 50:
        label = "Fairly Difficult"
    else:
        label = "Difficult"

    # Average reading speed ~ 200 words per minute (3.3 words per second)
    reading_time_sec = max(1, round(word_count / 3.3))

    return {
        "words": word_count,
        "sentences": sentence_count,
        "syllables": syllable_count,
        "reading_ease": ease,
        "grade_level": grade,
        "reading_time_sec": reading_time_sec,
        "label": label,
    }
