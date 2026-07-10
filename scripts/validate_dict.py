import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from g2p_macedonian import CONSONANTS, VOWELS  # noqa: E402

EXPECTED_XSAMPA_PHONES = set()
for ipa, xs in {**CONSONANTS, **VOWELS}.values():
    EXPECTED_XSAMPA_PHONES.add(xs)
# devoiced finals + the clear-l variant phone
EXPECTED_XSAMPA_PHONES |= {"p", "t", "c", "k", "f", "s", "ts", "tS", "l"}

# non-lexical entries from 03_build_dict.py, skipped by the checks below
SPECIAL_WORDS = {"#", "@@", "gb", "dummy", "еее", "ммм"}


def parse_dict_line(line: str):
    parts = line.strip().split()
    if len(parts) < 3:
        return None, None
    return parts[0], parts[2:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vocab", required=True)
    ap.add_argument("--dict", required=True)
    args = ap.parse_args()

    vocab_words = set(
        w.strip() for w in Path(args.vocab).read_text(encoding="utf-8").splitlines() if w.strip()
    )

    dict_words = set()
    seen_lines = set()
    unexpected_phones = set()
    empty_pron_count = 0
    duplicate_lines = 0

    for line in Path(args.dict).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if line in seen_lines:
            duplicate_lines += 1
        seen_lines.add(line)

        word, phones = parse_dict_line(line)
        if word is None:
            print(f"[MALFORMED LINE] {line!r}")
            continue
        if word in SPECIAL_WORDS:
            continue
        dict_words.add(word)
        if not phones:
            empty_pron_count += 1
        for ph in phones:
            if ph not in EXPECTED_XSAMPA_PHONES:
                unexpected_phones.add(ph)

    missing = vocab_words - dict_words
    extra = dict_words - vocab_words

    print("=== Validation report ===")
    print(f"Vocab words:                {len(vocab_words)}")
    print(f"Dict entries (unique word): {len(dict_words)}")
    print(f"Missing from dict:          {len(missing)}")
    if missing and len(missing) <= 20:
        print(f"  -> {sorted(missing)}")
    print(f"Extra in dict (not in vocab): {len(extra)}")
    print(f"Duplicate lines:             {duplicate_lines}")
    print(f"Empty pronunciations:        {empty_pron_count}")
    print(f"Unexpected X-SAMPA phones:   {len(unexpected_phones)}")
    if unexpected_phones:
        print(f"  -> {sorted(unexpected_phones)}")

    ok = not missing and not unexpected_phones and empty_pron_count == 0
    print("\nRESULT:", "PASS" if ok else "FAIL -- fix issues above before using with SPPAS")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
