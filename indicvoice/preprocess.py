"""Text preprocessing, sentence splitting, script validation, and glossary substitution."""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from indicvoice.errors import EmptyInputError, ScriptMismatchError, TextTooLongError

# Unicode Script Ranges
SCRIPT_RANGES = {
    "Oriya": [(0x0B00, 0x0B7F)],
    "Devanagari": [(0x0900, 0x097F)],
    "Bengali": [(0x0980, 0x09FF)],
    "Tamil": [(0x0B80, 0x0BFF)],
    "Telugu": [(0x0C00, 0x0C7F)],
    "Kannada": [(0x0C80, 0x0CFF)],
    "Malayalam": [(0x0D00, 0x0D7F)],
    "Gujarati": [(0x0A80, 0x0AFF)],
    "Gurmukhi": [(0x0A00, 0x0A7F)],
    "Latin": [
        (0x0041, 0x005A),  # A-Z
        (0x0061, 0x007A),  # a-z
        (0x00C0, 0x024F),  # Latin Extended
    ],
}

# Common abbreviations to prevent premature splitting
ABBREVIATIONS = (
    r"(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|eg|e\.g|ie|i\.e|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\."
)


def clean_text(text: str) -> str:
    """Normalize unicode, strip extraneous whitespace and invisible characters."""
    if not text:
        return ""
    # Unicode NFKC normalization
    normalized = unicodedata.normalize("NFKC", text)
    # Replace multiple spaces/tabs with single space
    normalized = re.sub(r"[ \t]+", " ", normalized)
    # Replace 3 or more newlines with double newline
    normalized = re.sub(r"\n\s*\n+", "\n\n", normalized)
    return normalized.strip()


def detect_script(text: str) -> str:
    """Identify the dominant script of the text based on Unicode character counts."""
    counts: dict[str, int] = {script: 0 for script in SCRIPT_RANGES}
    other_count = 0

    for char in text:
        if not char.isalnum():
            continue
        code = ord(char)
        matched = False
        for script, ranges in SCRIPT_RANGES.items():
            for start, end in ranges:
                if start <= code <= end:
                    counts[script] += 1
                    matched = True
                    break
            if matched:
                break
        if not matched:
            other_count += 1

    # Return script with maximum character count
    dominant = max(counts, key=counts.get)
    if counts[dominant] == 0:
        return "Unknown"
    return dominant


def check_script(
    text: str,
    expected_script: str,
    language_name: str,
) -> None:
    """Verify that text matches the expected script.

    Raises:
        ScriptMismatchError: If the dominant script does not match expected_script.
    """
    detected = detect_script(text)
    if detected in ("Unknown",):
        return

    # Check for direct match or script compatibility (e.g. Bengali/Assamese)
    if detected != expected_script:
        # Assamese uses Bengali script
        if language_name.lower() == "assamese" and detected == "Bengali":
            return
        raise ScriptMismatchError(
            language=language_name,
            detected_script=detected,
            expected_script=expected_script,
        )


def split_sentences(text: str) -> list[str]:
    """Split text into sentences across both English and Indic punctuation marks.

    Handles '.', '!', '?', purna virama '।' (U+0964), and deergh virama '॥' (U+0965).
    """
    cleaned = clean_text(text)
    if not cleaned:
        return []

    # Protect abbreviations by temporarily replacing period with placeholder
    protected = cleaned

    def _replace_abbrev(match: re.Match) -> str:
        return match.group(0).replace(".", "§DOT§")

    protected = re.sub(ABBREVIATIONS, _replace_abbrev, protected, flags=re.IGNORECASE)

    # Split on sentence boundaries:
    # 1. Purna virama (।) or deergh virama (॥)
    # 2. English terminators (. ! ?) followed by whitespace or end of string
    # 3. Newlines
    pattern = r"(?<=[।॥!?])\s+|(?<=[.])\s+(?=[A-Z0-9\u0900-\u0D7F])|\n+"
    raw_sentences = re.split(pattern, protected)

    sentences: list[str] = []
    for s in raw_sentences:
        # Restore protected periods
        restored = s.replace("§DOT§", ".").strip()
        if restored:
            sentences.append(restored)

    return sentences if sentences else [cleaned]


def apply_glossary(text: str, glossary: dict[str, str]) -> str:
    """Replace glossary terms (case-insensitively for Latin terms)."""
    if not glossary:
        return text

    result = text
    # Sort terms by length descending to prevent partial prefix replacements
    sorted_terms = sorted(glossary.keys(), key=len, reverse=True)
    for term in sorted_terms:
        replacement = glossary[term]
        # Use regex word boundaries for Latin words
        if re.match(r"^[A-Za-z0-9_]+$", term):
            pattern = rf"\b{re.escape(term)}\b"
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        else:
            result = result.replace(term, replacement)

    return result


def preprocess(
    text: str,
    max_chars: int = 2000,
    expected_script: Optional[str] = None,
    language_name: Optional[str] = None,
    skip_translation: bool = False,
    glossary: Optional[dict[str, str]] = None,
) -> list[str]:
    """Complete preprocessing pipeline: validation, script check, glossary, sentence split."""
    if not text or not text.strip():
        raise EmptyInputError()

    char_len = len(text)
    if char_len > max_chars:
        raise TextTooLongError(current_len=char_len, max_chars=max_chars)

    cleaned = clean_text(text)

    # Enforce script check if translation is skipped and expected script is specified
    if skip_translation and expected_script and language_name:
        check_script(cleaned, expected_script=expected_script, language_name=language_name)

    # Apply glossary terms if translating from English
    if not skip_translation and glossary:
        cleaned = apply_glossary(cleaned, glossary)

    sentences = split_sentences(cleaned)
    if not sentences:
        raise EmptyInputError()

    return sentences
