from __future__ import annotations
import unicodedata
from dataclasses import dataclass


ALLOW_LOAN_ALLOPHONES = False  # (ŋ)/(w) — off, they'd need a conditioning rule


# letter -> (IPA, X-SAMPA)
# <л> is the dark /ɫ/ ("5"); clear [l] before е/и is an allophone and only shows up in the pronunciation variants, not in the base mapping.
CONSONANTS = {
    "п": ("p", "p"),
    "б": ("b", "b"),
    "т": ("t", "t"),
    "д": ("d", "d"),
    "ѓ": ("ɟ", "J\\"),
    "ќ": ("c", "c"),
    "к": ("k", "k"),
    "г": ("g", "g"),
    "м": ("m", "m"),
    "н": ("n", "n"),
    "њ": ("ɲ", "J"),
    "ѕ": ("ʣ", "dz"),
    "ц": ("ʦ", "ts"),
    "џ": ("ʤ", "dZ"),
    "ч": ("ʧ", "tS"),
    "ф": ("f", "f"),
    "в": ("v", "v"),
    "с": ("s", "s"),
    "з": ("z", "z"),
    "ш": ("ʃ", "S"),
    "ж": ("ʒ", "Z"),
    "х": ("x", "x"),
    "л": ("ɫ", "5"),
    "љ": ("ʎ", "L"),
    "р": ("r", "r"),
    "ј": ("j", "j"),
}

VOWELS = {
    "а": ("a", "a"),
    "е": ("ɛ", "E"),
    "и": ("i", "i"),
    "о": ("ɔ", "O"),
    "у": ("u", "u"),
    # accented forms map to the same phones (ѝ is the clitic "to her" for eg.)
    "ѐ": ("ɛ", "E"),
    "ѝ": ("i", "i"),
}

LETTER_MAP = {**CONSONANTS, **VOWELS}

# word-final devoicing, the one rule the spelling doesn't show:
# леб -> [лep]. Sonorants don't devoice.
FINAL_DEVOICING = {
    ("b", "b"): ("p", "p"),
    ("d", "d"): ("t", "t"),
    ("ɟ", "J\\"): ("c", "c"),
    ("g", "g"): ("k", "k"),
    ("v", "v"): ("f", "f"),
    ("z", "z"): ("s", "s"),
    ("ʣ", "dz"): ("ʦ", "ts"),
    ("ʤ", "dZ"): ("ʧ", "tS"),
    ("ʒ", "Z"): ("ʃ", "S"),
}


@dataclass
class Phonemization:
    word: str
    ipa: str
    ipa_phones: list
    xsampa: str
    xsampa_phones: list


def phonemize(word: str) -> Phonemization:
    word = unicodedata.normalize("NFC", word).lower().strip()

    ipa_phones = []
    xsampa_phones = []
    unknown = []

    for ch in word:
        if ch in LETTER_MAP:
            ipa, xs = LETTER_MAP[ch]
            ipa_phones.append(ipa)
            xsampa_phones.append(xs)
        else:
            unknown.append(ch)

    if unknown:
        # fail loudly instead of silently dropping a phone
        raise ValueError(f"Unmapped character(s) {unknown!r} in word {word!r}")

    if ipa_phones:
        last = (ipa_phones[-1], xsampa_phones[-1])
        if last in FINAL_DEVOICING:
            new_ipa, new_xs = FINAL_DEVOICING[last]
            ipa_phones[-1] = new_ipa
            xsampa_phones[-1] = new_xs

    return Phonemization(
        word=word,
        ipa=".".join(ipa_phones),
        ipa_phones=ipa_phones,
        xsampa=" ".join(xsampa_phones),
        xsampa_phones=xsampa_phones,
    )


def to_ipa(word: str) -> str:
    return phonemize(word).ipa


def to_xsampa(word: str) -> str:
    return phonemize(word).xsampa


# --- pronunciation variants -------------------------------------------------
# The dict lists one line per variant and the SPPAS aligner picks the best
# match. Two variants worth having:
#   - voiced final: devoicing doesn't apply before a voiced obstruent in
#     connected speech (град голем), so keep the underlying form too
#   - clear l: 5 -> l before front vowels

_VOICED_FINAL_XS = {xs for (_ipa, xs) in FINAL_DEVOICING}
CLEAR_L_TRIGGERS = {"E", "i"}


def _clear_l(phones: list) -> list | None:
    out = list(phones)
    changed = False
    for i in range(len(out) - 1):
        if out[i] == "5" and out[i + 1] in CLEAR_L_TRIGGERS:
            out[i] = "l"
            changed = True
    return out if changed else None


def phonemize_variants(word: str) -> list:
    """All pronunciations for the dict: primary first, then variants."""
    word = unicodedata.normalize("NFC", word).lower().strip()
    primary = phonemize(word).xsampa_phones
    variants = [primary]

    if primary and word and word[-1] in CONSONANTS:
        underlying = CONSONANTS[word[-1]][1]
        if underlying in _VOICED_FINAL_XS and primary[-1] != underlying:
            variants.append(primary[:-1] + [underlying])

    for v in list(variants):
        cl = _clear_l(v)
        if cl is not None:
            variants.append(cl)

    seen = set()
    out = []
    for v in variants:
        key = tuple(v)
        if key not in seen:
            seen.add(key)
            out.append(v)
    return out


if __name__ == "__main__":
    for w in ["леб", "прст", "три", "клуч", "страв", "град", "лист", "мало"]:
        p = phonemize(w)
        vs = " | ".join(" ".join(v) for v in phonemize_variants(w))
        print(f"{p.word:<8} {p.ipa:<18} {vs}")
    # known gap: syllabic /r/ (прст) is emitted as plain r; if syllabification needs the nucleus marked, that's a post-processing rule...
