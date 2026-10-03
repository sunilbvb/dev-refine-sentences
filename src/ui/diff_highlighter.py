"""Word-level diff tokenizer using Python Standard Library difflib."""

import re
import difflib
from typing import List, Tuple


def compute_word_diff(original: str, refined: str) -> List[Tuple[str, str]]:
    """Compute word-by-word diff between original and refined strings.

    Returns:
        List of tuples: (tag, text)
        where tag is one of: 'equal', 'del', 'add'
    """
    # Tokenize preserving spaces and punctuation
    words_orig = re.findall(r"\w+|\s+|[^\w\s]", original)
    words_ref = re.findall(r"\w+|\s+|[^\w\s]", refined)

    matcher = difflib.SequenceMatcher(None, words_orig, words_ref)
    tokens: List[Tuple[str, str]] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            tokens.append(("equal", "".join(words_orig[i1:i2])))
        elif tag == "delete":
            tokens.append(("del", "".join(words_orig[i1:i2])))
        elif tag == "insert":
            tokens.append(("add", "".join(words_ref[j1:j2])))
        elif tag == "replace":
            tokens.append(("del", "".join(words_orig[i1:i2])))
            tokens.append(("add", "".join(words_ref[j1:j2])))

    return tokens
