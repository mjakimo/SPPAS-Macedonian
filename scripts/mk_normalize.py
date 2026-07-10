from __future__ import annotations
import re
import unicodedata

# Macedonian Cyrillic, 31 letters + the accented forms ѐ/ѝ (ѝ is a real word, the clitic "to her").
MK_CYRILLIC_CHARS = set(
    "абвгдѓежзѕијклљмнњопрстќуфхцчџш"
    "АБВГДЃЕЖЗЅИЈКЛЉМНЊОПРСТЌУФХЦЧЏШ"
    "ѐЀѝЍ"
)

# Latin letters that look identical to Cyrillic ones and show up as copy-paste contamination in scraped text..
LATIN_TO_CYRILLIC_HOMOGLYPHS = {
    "A": "А", "a": "а",
    "B": "В",
    "C": "С", "c": "с",
    "E": "Е", "e": "е",
    "H": "Н",
    "J": "Ј", "j": "ј",
    "K": "К",
    "M": "М",
    "O": "О", "o": "о",
    "P": "Р", "p": "р",
    "T": "Т",
    "X": "Х", "x": "х",
    "y": "у",
}

# tokenize on Cyrillic + homoglyphs so contaminated tokens survive whole
_TOKEN_CHARS = "".join(sorted(MK_CYRILLIC_CHARS | set(LATIN_TO_CYRILLIC_HOMOGLYPHS)))
TOKEN_RE = re.compile("[" + re.escape(_TOKEN_CHARS) + "]+", re.UNICODE)


def normalize_homoglyphs(word: str) -> str:
    """Repair Latin look-alikes, but only if the token already has some
    Cyrillic in it — otherwise we'd mangle genuinely Latin words."""
    if not any(ch in MK_CYRILLIC_CHARS for ch in word):
        return word
    return "".join(LATIN_TO_CYRILLIC_HOMOGLYPHS.get(ch, ch) for ch in word)


def normalize_word(word: str) -> str:
    # homoglyph table is case-sensitive, so repair before lowercasing
    word = unicodedata.normalize("NFC", word)
    word = normalize_homoglyphs(word)
    return word.lower()


def is_valid_mk_word(word: str, min_len: int = 1) -> bool:
    if len(word) < min_len:
        return False
    return all(ch in MK_CYRILLIC_CHARS for ch in word)
