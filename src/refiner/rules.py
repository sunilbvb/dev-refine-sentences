"""Rule-based offline sentence refiner with Pre-compiled Regex and Teach Mode.

100% Python Standard Library. Zero external dependencies.
"""

import re
import time
from typing import Dict, List, Tuple, Any, Optional, Pattern
from .base import BaseRefiner
from .spelling import SpellingEngine
from config.settings import ConfigManager


# Global pre-compiled regexes for maximum throughput
RE_SPACES = re.compile(r"[ \t]+")
RE_DUPLICATE_WORDS = re.compile(r"\b(\w+)\s+\1\b", re.IGNORECASE)
RE_PUNCT_SPACE_BEFORE = re.compile(r"\s+([,.:;?!])")
RE_PUNCT_SPACE_AFTER = re.compile(r"([,.:;?!])([A-Za-z])")
RE_PUNCT_COLLAPSE = re.compile(r"([!?,]){2,}")
RE_SENTENCE_START = re.compile(r"([.!?]\s+)([a-z])")
RE_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


class RuleBasedRefiner(BaseRefiner):
    """Deterministic, rule-based sentence polisher with Pre-compiled Regexes and Caching."""

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
        r"\btheyre\b": "they're",
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
        r"\bpls\b": "please",
        r"\basap\b": "as soon as possible",
        r"\bbtw\b": "by the way",
        r"\bfyi\b": "for your information",
        r"\brn\b": "right now",
        r"\btmrw\b": "tomorrow",
        r"\byday\b": "yesterday",
        r"\bmsg\b": "message",
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
        # Duplicate verb / copula collision
        (r"\b(are\s+is|is\s+are)\b", "are", "Grammar: Removed duplicate verb 'are is' → 'are'."),
        (r"\b(was\s+were|were\s+was)\b", "were", "Grammar: Removed duplicate past-tense verb."),
        (r"\b(has\s+have|have\s+has)\b", "have", "Grammar: Removed duplicate auxiliary verb."),
        (r"\b(will\s+would|would\s+will)\b", "will", "Grammar: Removed duplicate modal verb."),
        (r"\b(can\s+could|could\s+can)\b", "can", "Grammar: Removed duplicate modal verb."),
        (r"\b(do\s+does|does\s+do)\b", "do", "Grammar: Removed duplicate auxiliary verb."),

        # Subjective/objective pronoun before noun instead of possessive determiner
        (r"\bI\s+(students?|friends?|parents?|colleagues?|teachers?|people|kids|children|folks|guys|team|family|boss|work|project|code|computer|laptop|phone|room|home|house|car|job|office|class|school|university|dog|cat|sister|brother|mother|father|wife|husband|son|daughter)\b", r"My \1", "Grammar: Corrected pronoun 'I' to possessive 'My' before noun."),
        (r"\bme\s+(students?|friends?|parents?|colleagues?|teachers?|people|kids|children|folks|guys|team|family|boss|work|project|code|computer|laptop|phone|room|home|house|car|job|office|class|school|university|dog|cat|sister|brother|mother|father|wife|husband|son|daughter)\b", r"My \1", "Grammar: Corrected pronoun 'me' to possessive 'My' before noun."),
        (r"\bhe\s+(students?|friends?|parents?|colleagues?|team|family|boss|project|computer|car|job|dog|cat)\b", r"His \1", "Grammar: Corrected pronoun 'he' to possessive 'His'."),
        (r"\bshe\s+(students?|friends?|parents?|colleagues?|team|family|boss|project|computer|car|job|dog|cat)\b", r"Her \1", "Grammar: Corrected pronoun 'she' to possessive 'Her'."),
        (r"\bthey\s+(students?|friends?|parents?|colleagues?|team|family|boss|project|computer|car|job|dog|cat)\b", r"Their \1", "Grammar: Corrected pronoun 'they' to possessive 'Their'."),

        # Missing copula (be-verb) before adjective
        (r"\b(he|she|it)\s+(very\s+good|very\s+great|very\s+nice|very\s+bad|very\s+happy|good|great|nice|happy|ready|busy|smart|awesome)\b", r"\1 is \2", "Grammar: Added missing auxiliary verb 'is'."),
        (r"\b(they|we|you)\s+(very\s+good|very\s+great|very\s+nice|very\s+bad|very\s+happy|good|great|nice|happy|ready|busy|smart|awesome)\b", r"\1 are \2", "Grammar: Added missing auxiliary verb 'are'."),
        (r"\bI\s+(very\s+good|very\s+great|very\s+nice|very\s+bad|very\s+happy|good|great|nice|happy|ready|busy|smart|awesome)\b", r"I am \1", "Grammar: Added missing auxiliary verb 'am'."),

        # Past-tense after auxiliary 'did' / 'didn't'
        (r"\b(did\s+not|didn't)\s+saw\b", r"\1 see", "Grammar: Auxiliary 'did' takes base verb 'see'."),
        (r"\b(did\s+not|didn't)\s+went\b", r"\1 go", "Grammar: Auxiliary 'did' takes base verb 'go'."),
        (r"\b(did\s+not|didn't)\s+came\b", r"\1 come", "Grammar: Auxiliary 'did' takes base verb 'come'."),
        (r"\b(did\s+not|didn't)\s+ate\b", r"\1 eat", "Grammar: Auxiliary 'did' takes base verb 'eat'."),
        (r"\b(did\s+not|didn't)\s+knew\b", r"\1 know", "Grammar: Auxiliary 'did' takes base verb 'know'."),

        # Double negatives
        (r"\b(don't|doesn't|didn't)\s+have\s+no\b", r"\1 have any", "Grammar: Resolved double negative."),
        (r"\b(don't|doesn't|didn't)\s+know\s+nothing\b", r"\1 know anything", "Grammar: Resolved double negative."),
        (r"\b(can't|couldn't)\s+see\s+nothing\b", r"\1 see anything", "Grammar: Resolved double negative."),
        (r"\b(can't|couldn't)\s+find\s+no\b", r"\1 find any", "Grammar: Resolved double negative."),

        # Redundant comparatives & irregular plurals
        (r"\bmore\s+better\b", "better", "Grammar: Removed redundant comparative 'more better' → 'better'."),
        (r"\bmore\s+faster\b", "faster", "Grammar: Removed redundant comparative 'more faster' → 'faster'."),
        (r"\bmore\s+easier\b", "easier", "Grammar: Removed redundant comparative 'more easier' → 'easier'."),
        (r"\bchilds\b", "children", "Irregular plural: 'child' plural is 'children'."),
        (r"\bpeoples\b", "people", "Irregular plural: 'people' is already plural."),
        (r"\bfoots\b", "feet", "Irregular plural: 'foot' plural is 'feet'."),
        (r"\btooths\b", "teeth", "Irregular plural: 'tooth' plural is 'teeth'."),
        (r"\bfeeled\b", "felt", "Irregular verb: 'feel' past tense is 'felt'."),
        (r"\brunned\b", "ran", "Irregular verb: 'run' past tense is 'ran'."),

        # Contextual verb slips and prepositions
        (r"\bI\s+wasn\s+(other|to\b|[a-z]+s\b)", r"I want \1", "Grammar: Corrected mistyped verb 'wasn' → 'want'."),
        (r"\bcontribute\s+on\b", "contribute to", "Grammar: Preposition 'contribute' pairs with 'to', not 'on'."),
        (r"\bso\s+(would|could|will)\s+be\s+(great|good|nice|awesome|helpful|better)\b", r"so it \1 be \2", "Grammar: Added missing dummy subject 'it' ('so would be' → 'so it would be')."),
        (r"\b(also|however|furthermore|therefore)\s+please\b", r"\1, please", "Punctuation: Added comma after introductory adverb."),
        (r"\bgit\s+(branch|repository|repo|rules?|commit|push|pull|standard)\b", r"Git \1", "Formatting: Capitalized Git tool name."),
        (r"\bthe\s+Git\s+standard\s+rules\b", "standard Git rules", "Phrasing: Refined 'the Git standard rules' → 'standard Git rules'."),
        (r"\bGit\s+standard\s+rules\b", "standard Git rules", "Phrasing: Refined 'Git standard rules' → 'standard Git rules'."),
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

    # Class-level pre-compiled regex structures (compiled once for lifetime of process)
    _COMPILED_TYPOS: List[Tuple[Pattern, str, str]] = [
        (re.compile(p, re.IGNORECASE), repl, p.replace(r"\b", "")) for p, repl in TYPO_MAP.items()
    ]
    _COMPILED_GRAMMAR: List[Tuple[Pattern, str, str]] = [
        (re.compile(p, re.IGNORECASE), repl, reason) for p, repl, reason in GRAMMAR_FIXES
    ]
    _COMPILED_CONCISE: List[Tuple[Pattern, str, str]] = [
        (re.compile(p, re.IGNORECASE), repl, reason) for p, repl, reason in CONCISE_REDUNDANCIES
    ]
    _COMPILED_PRO: List[Tuple[Pattern, str, str]] = [
        (re.compile(p, re.IGNORECASE), repl, reason) for p, repl, reason in PROFESSIONAL_MAP
    ]
    _COMPILED_FRIENDLY: List[Tuple[Pattern, str, str]] = [
        (re.compile(p, re.IGNORECASE), repl, reason) for p, repl, reason in FRIENDLY_MAP
    ]

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or ConfigManager()
        self.spelling_engine = SpellingEngine()
        self.last_explanations: List[str] = []
        # In-memory LRU cache for 0ms repeated refinements
        self._cache: Dict[Tuple[str, str], Tuple[str, List[str]]] = {}

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

        cache_key = (text.strip(), tone.lower().strip())
        if cache_key in self._cache:
            cached_result, cached_explanations = self._cache[cache_key]
            self.last_explanations = list(cached_explanations)
            return cached_result

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

        # Step 2: Clean excess whitespace using precompiled regex
        result = RE_SPACES.sub(" ", result)

        # Step 3: Fast shorthand & typo expansions using precompiled regexes
        for rx, replacement, clean_term in self._COMPILED_TYPOS:
            if rx.search(result):
                result = rx.sub(replacement, result)
                self.last_explanations.append(f"Spelling: Fixed typo/shorthand '{clean_term}' → '{replacement}'.")

        # Step 4: Contextual phrasing & grammar pass before spelling
        for rx, replacement, reason in self._COMPILED_GRAMMAR:
            if rx.search(result):
                result = rx.sub(replacement, result)
                self.last_explanations.append(reason if reason.startswith("Grammar:") else f"Grammar: {reason}")

        # Step 5: Spelling pass (Norvig edit-distance + developer dictionary)
        result, spelling_corrections = self.spelling_engine.correct_text(result, whitelist=whitelist)
        for orig_w, fixed_w in spelling_corrections:
            self.last_explanations.append(f"Spelling: Fixed typo '{orig_w}' → '{fixed_w}'.")

        # Step 6: Post-spelling grammar & irregular verbs cleanup pass
        for rx, replacement, reason in self._COMPILED_GRAMMAR:
            if rx.search(result):
                result = rx.sub(replacement, result)
                msg = reason if reason.startswith("Grammar:") else f"Grammar: {reason}"
                if msg not in self.last_explanations:
                    self.last_explanations.append(msg)

        # Step 5: Apply Tone-specific transformations using precompiled regexes
        if normalized_tone == "concise":
            for rx, replacement, reason in self._COMPILED_CONCISE:
                if rx.search(result):
                    result = rx.sub(replacement, result)
                    self.last_explanations.append(reason)
        elif normalized_tone == "professional":
            for rx, replacement, reason in self._COMPILED_PRO:
                if rx.search(result):
                    result = rx.sub(replacement, result)
                    self.last_explanations.append(reason)
        elif normalized_tone == "friendly":
            for rx, replacement, reason in self._COMPILED_FRIENDLY:
                if rx.search(result):
                    result = rx.sub(replacement, result)
                    self.last_explanations.append(reason)

        # Step 6: Fix word duplicates using precompiled regex
        dup_match = RE_DUPLICATE_WORDS.search(result)
        if dup_match:
            word = dup_match.group(1)
            result = RE_DUPLICATE_WORDS.sub(r"\1", result)
            self.last_explanations.append(f"Redundancy: Removed repeated word '{word} {word}'.")

        # Step 7: Fix punctuation spacing using precompiled regexes
        result = RE_PUNCT_SPACE_BEFORE.sub(r"\1", result)
        result = RE_PUNCT_SPACE_AFTER.sub(r"\1 \2", result)
        result = RE_PUNCT_COLLAPSE.sub(r"\1", result)

        # Step 8: Clean whitespace and strip
        result = RE_SPACES.sub(" ", result).strip()

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

        # Store in LRU cache (limit size to 256)
        if len(self._cache) > 256:
            self._cache.pop(next(iter(self._cache)))
        self._cache[cache_key] = (result, list(self.last_explanations))

        return result

    def _capitalize_sentences(self, text: str) -> str:
        """Capitalize first character of text and any character following sentence terminals."""
        def repl(match: re.Match) -> str:
            prefix = match.group(1)
            char = match.group(2)
            return prefix + char.upper()

        if text:
            text = text[0].upper() + text[1:]

        text = RE_SENTENCE_START.sub(repl, text)
        return text

    def _format_as_bullets(self, text: str) -> str:
        """Convert sentence string into formatted markdown bullet list."""
        sentences = RE_SENTENCE_SPLIT.split(text)
        bullets = []
        for s in sentences:
            s_clean = s.strip()
            if s_clean:
                bullets.append(f"- {s_clean}")
        return "\n".join(bullets) if bullets else text
