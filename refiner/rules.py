"""Rule-based offline sentence refiner with Teach / Explanation Mode.

100% Python Standard Library. Zero external dependencies.
"""

import re
import time
from typing import Dict, List, Tuple, Any, Optional
from .base import BaseRefiner
from config.settings import ConfigManager


class RuleBasedRefiner(BaseRefiner):
    """Deterministic, rule-based sentence polisher with Teach/Explanation tracking."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or ConfigManager()
        self.last_explanations: List[str] = []

    # Common typos and shorthand normalization
    TYPO_MAP: Dict[str, str] = {
        r"\bi\b": "I",
        r"\bim\b": "I'm",
        r"\bive\b": "I've",
        r"\bid\b": "I'd",
        r"\bill\b": "I'll",
        r"\bdont\b": "don't",
        r"\bcant\b": "can't",
        r"\bwont\b": "won't",
        r"\bdidnt\b": "didn't",
        r"\bisnt\b": "isn't",
        r"\barent\b": "aren't",
        r"\bhasnt\b": "hasn't",
        r"\bhavent\b": "haven't",
        r"\bwasnt\b": "wasn't",
        r"\bwerent\b": "weren't",
        r"\bcouldnt\b": "couldn't",
        r"\bshouldnt\b": "shouldn't",
        r"\bwouldnt\b": "wouldn't",
        r"\byoure\b": "you're",
        r"\btheyre\b": "theyre",
        r"\bweve\b": "we've",
        r"\bwhats\b": "what's",
        r"\bthats\b": "that's",
        r"\btheres\b": "there's",
        r"\bhows\b": "how's",
        r"\blets\b": "let's",
        r"\bteh\b": "the",
        r"\brecieve\b": "receive",
        r"\bseperate\b": "separate",
        r"\bdefinately\b": "definitely",
        r"\boccured\b": "occurred",
        r"\baccomodate\b": "accommodate",
        r"\btruely\b": "truly",
        r"\buntill\b": "until",
        r"\bcalender\b": "calendar",
        r"\balot\b": "a lot",
        r"\bnoone\b": "no one",
        r"\bthx\b": "thanks",
        r"\bplz\b": "please",
        r"\bu\b": "you",
        r"\br\b": "are",
        r"\bur\b": "your",
        r"\bcuz\b": "because",
        r"\bcos\b": "because",
        r"\bsec\b": "second",
        r"\bmin\b": "minute",
    }

    # Common subject-verb and tense mismatches
    GRAMMAR_FIXES: List[Tuple[str, str, str]] = [
        (r"\b(he|she|it)\s+don't\b", r"\1 doesn't", "Subject-verb agreement: third-person singular uses 'doesn't'."),
        (r"\b(they|we|you)\s+doesn't\b", r"\1 don't", "Subject-verb agreement: plural pronouns use 'don't'."),
        (r"\b(they|we|you)\s+is\b", r"\1 are", "Subject-verb agreement: plural pronouns use 'are'."),
        (r"\b(he|she|it)\s+are\b", r"\1 is", "Subject-verb agreement: singular pronouns use 'is'."),
        (r"\b(i)\s+is\b", "I am", "Subject-verb agreement: 'I' pairs with 'am'."),
        (r"\b(i)\s+are\b", "I am", "Subject-verb agreement: 'I' pairs with 'am'."),
        (r"\b(he|she|it)\s+go\b", r"\1 goes", "Subject-verb agreement: third-person singular uses 'goes'."),
        (r"\b(he|she|it)\s+have\b", r"\1 has", "Subject-verb agreement: third-person singular uses 'has'."),
        (r"\b(they|we|you|I)\s+has\b", r"\1 have", "Subject-verb agreement: plural and first-person use 'have'."),
        (r"\b(he|she|it)\s+do\b", r"\1 does", "Subject-verb agreement: third-person singular uses 'does'."),
        (r"\b(he|she|it)\s+need\b", r"\1 needs", "Subject-verb agreement: third-person singular uses 'needs'."),
        (r"\b(he|she|it)\s+want\b", r"\1 wants", "Subject-verb agreement: third-person singular uses 'wants'."),
        (r"\bbuyed\b", "bought", "Irregular verb: 'buy' past tense is 'bought'."),
        (r"\bcatched\b", "caught", "Irregular verb: 'catch' past tense is 'caught'."),
        (r"\bteached\b", "taught", "Irregular verb: 'teach' past tense is 'taught'."),
        (r"\bfeeled\b", "felt", "Irregular verb: 'feel' past tense is 'felt'."),
        (r"\brunned\b", "ran", "Irregular verb: 'run' past tense is 'ran'."),
    ]

    # Filler words and redundancies for concise tone
    CONCISE_REDUNDANCIES: List[Tuple[str, str, str]] = [
        (r"\bin order to\b", "to", "Conciseness: Replaced 'in order to' with 'to'."),
        (r"\bdue to the fact that\b", "because", "Conciseness: Replaced 'due to the fact that' with 'because'."),
        (r"\bat this point in time\b", "now", "Conciseness: Replaced 'at this point in time' with 'now'."),
        (r"\bat the present time\b", "currently", "Conciseness: Replaced 'at the present time' with 'currently'."),
        (r"\bas a matter of fact\b", "in fact", "Conciseness: Replaced 'as a matter of fact' with 'in fact'."),
        (r"\bfor the purpose of\b", "for", "Conciseness: Replaced 'for the purpose of' with 'for'."),
        (r"\bin the event that\b", "if", "Conciseness: Replaced 'in the event that' with 'if'."),
        (r"\bwith reference to\b", "regarding", "Conciseness: Replaced 'with reference to' with 'regarding'."),
        (r"\bwith regard to\b", "regarding", "Conciseness: Replaced 'with regard to' with 'regarding'."),
        (r"\bbasically\b", "", "Conciseness: Removed filler word 'basically'."),
        (r"\bactually\b", "", "Conciseness: Removed filler word 'actually'."),
        (r"\bkind of\b", "", "Conciseness: Removed filler phrase 'kind of'."),
        (r"\bsort of\b", "", "Conciseness: Removed filler phrase 'sort of'."),
        (r"\bneedless to say\b", "", "Conciseness: Removed redundant phrase 'needless to say'."),
        (r"\bit goes without saying that\b", "", "Conciseness: Removed redundant phrase 'it goes without saying that'."),
    ]

    # Formal mappings for professional tone
    PROFESSIONAL_MAP: List[Tuple[str, str, str]] = [
        (r"\bgonna\b", "going to", "Formality: Replaced informal 'gonna' with 'going to'."),
        (r"\bwanna\b", "want to", "Formality: Replaced informal 'wanna' with 'want to'."),
        (r"\bgotta\b", "must", "Formality: Replaced informal 'gotta' with 'must'."),
        (r"\blemme\b", "let me", "Formality: Replaced informal 'lemme' with 'let me'."),
        (r"\bgive me a shout\b", "please contact me", "Formality: Replaced colloquialism 'give me a shout'."),
        (r"\basap\b", "as soon as possible", "Formality: Expanded acronym 'asap'."),
        (r"\bhit me up\b", "let me know", "Formality: Replaced informal 'hit me up'."),
        (r"\btalk to you later\b", "I look forward to speaking soon", "Formality: Replaced closing with professional phrase."),
        (r"\bthanks a bunch\b", "Thank you very much", "Formality: Replaced colloquial thanks."),
    ]

    # Friendly mappings for warm tone
    FRIENDLY_MAP: List[Tuple[str, str, str]] = [
        (r"\bdo not hesitate to contact\b", "feel free to reach out to", "Warmth: Softened formal contact prompt."),
        (r"\bper our conversation\b", "as we discussed", "Warmth: Used conversational phrasing."),
        (r"\bI demand\b", "could you please", "Courtesy: Softened harsh demand into polite request."),
        (r"\byou must\b", "would you mind", "Courtesy: Softened imperative instruction."),
        (r"\bprompt response required\b", "whenever you get a chance", "Courtesy: Relaxed urgency tone."),
    ]

    @property
    def name(self) -> str:
        return "Built-in Rule Engine (Offline Standard Library)"

    def is_available(self) -> bool:
        return True

    def get_last_explanations(self) -> List[str]:
        """Return the explanation log for the most recent refinement."""
        return list(self.last_explanations)

    def _expand_dynamic_variables(self, text: str) -> str:
        """Expand dynamic template variables like {{date}}, {{time}}, {{year}}, {{day}}."""
        now = time.localtime()
        date_str = time.strftime("%Y-%m-%d", now)
        time_str = time.strftime("%H:%M", now)
        year_str = time.strftime("%Y", now)
        day_str = time.strftime("%A", now)

        text = text.replace("{{date}}", date_str)
        text = text.replace("{{time}}", time_str)
        text = text.replace("{{year}}", year_str)
        text = text.replace("{{day}}", day_str)
        return text

    def refine(self, text: str, tone: str = "standard", **kwargs: Any) -> str:
        if not text or not text.strip():
            self.last_explanations = []
            return ""

        result = text.strip()
        self.last_explanations = []
        normalized_tone = tone.lower().strip()

        # Step 0: Expand user custom snippets with dynamic variables
        snippets = self.config_manager.get_snippets()
        for shortcut, expansion in snippets.items():
            pattern = rf"\b{re.escape(shortcut)}\b"
            if re.search(pattern, result, flags=re.IGNORECASE):
                resolved_expansion = self._expand_dynamic_variables(expansion)
                result = re.sub(pattern, resolved_expansion, result, flags=re.IGNORECASE)
                self.last_explanations.append(f"Snippet: Expanded '{shortcut}' → '{resolved_expansion}'.")

        # Step 1: Whitelist protection (prevent tech words from being mutated)
        whitelist = self.config_manager.get_whitelist()
        placeholders: Dict[str, str] = {}
        for idx, word in enumerate(whitelist):
            key = f"__WLTOKEN_{idx}__"
            pattern = rf"\b{re.escape(word)}\b"
            if re.search(pattern, result, flags=re.IGNORECASE):
                placeholders[key] = word
                result = re.sub(pattern, key, result, flags=re.IGNORECASE)
                self.last_explanations.append(f"Dictionary: Preserved protected term '{word}'.")

        # Step 2: Clean excess whitespace
        result = re.sub(r"[ \t]+", " ", result)

        # Step 3: Fix typos and abbreviations
        for pattern, replacement in self.TYPO_MAP.items():
            if re.search(pattern, result, flags=re.IGNORECASE):
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
                clean_term = pattern.replace(r"\b", "")
                self.last_explanations.append(f"Spelling: Fixed typo/shorthand '{clean_term}' → '{replacement}'.")

        # Step 4: Fix common grammar & irregular verbs
        for pattern, replacement, reason in self.GRAMMAR_FIXES:
            if re.search(pattern, result, flags=re.IGNORECASE):
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
                self.last_explanations.append(f"Grammar: {reason}")

        # Step 5: Apply Tone-specific transformations
        if normalized_tone == "concise":
            for pattern, replacement, reason in self.CONCISE_REDUNDANCIES:
                if re.search(pattern, result, flags=re.IGNORECASE):
                    result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
                    self.last_explanations.append(reason)
        elif normalized_tone == "professional":
            for pattern, replacement, reason in self.PROFESSIONAL_MAP:
                if re.search(pattern, result, flags=re.IGNORECASE):
                    result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
                    self.last_explanations.append(reason)
        elif normalized_tone == "friendly":
            for pattern, replacement, reason in self.FRIENDLY_MAP:
                if re.search(pattern, result, flags=re.IGNORECASE):
                    result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
                    self.last_explanations.append(reason)

        # Step 6: Fix word duplicates ("the the" -> "the", "please please" -> "please")
        dup_match = re.search(r"\b(\w+)\s+\1\b", result, flags=re.IGNORECASE)
        if dup_match:
            word = dup_match.group(1)
            result = re.sub(r"\b(\w+)\s+\1\b", r"\1", result, flags=re.IGNORECASE)
            self.last_explanations.append(f"Redundancy: Removed repeated word '{word} {word}'.")

        # Step 7: Fix punctuation spacing
        result = re.sub(r"\s+([,.:;?!])", r"\1", result)
        result = re.sub(r"([,.:;?!])([A-Za-z])", r"\1 \2", result)
        result = re.sub(r"([!?,]){2,}", r"\1", result)

        # Step 8: Clean whitespace and strip
        result = re.sub(r"[ \t]+", " ", result).strip()

        # Step 9: Capitalize sentence beginnings
        orig_first = result[0] if result else ""
        result = self._capitalize_sentences(result)
        if result and orig_first and orig_first.islower() and result[0].isupper():
            self.last_explanations.append("Formatting: Capitalized initial letter of sentence.")

        # Step 10: Ensure terminating punctuation
        result = result.strip()
        if result and result[-1] not in ".?!":
            result += "."
            self.last_explanations.append("Punctuation: Added missing ending punctuation mark ('.').")

        # Step 11: Restore Whitelist words
        for key, original_word in placeholders.items():
            result = result.replace(key, original_word)

        # Step 12: Tone Structural Formatting (Bullet points / Email)
        if normalized_tone == "bullet_points":
            result = self._format_as_bullets(result)
            self.last_explanations.append("Structure: Formatted text into markdown bullet points.")
        elif normalized_tone == "email_formal":
            result = f"Hi team,\n\n{result}\n\nBest regards,"
            self.last_explanations.append("Structure: Added professional email greeting and sign-off.")

        return result

    def _capitalize_sentences(self, text: str) -> str:
        """Capitalize first character of text and any character following sentence terminals."""
        def repl(match: re.Match) -> str:
            prefix = match.group(1)
            char = match.group(2)
            return prefix + char.upper()

        if text:
            text = text[0].upper() + text[1:]

        text = re.sub(r"([.!?]\s+)([a-z])", repl, text)
        return text

    def _format_as_bullets(self, text: str) -> str:
        """Convert sentence string into formatted markdown bullet list."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        bullets = []
        for s in sentences:
            s_clean = s.strip()
            if s_clean:
                bullets.append(f"- {s_clean}")
        return "\n".join(bullets) if bullets else text
