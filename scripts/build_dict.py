import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from g2p_macedonian import phonemize, phonemize_variants  # noqa: E402


SPECIAL_ENTRIES = [
    ("#", ["#"]),
    ("@@", ["@@"]),
    ("gb", ["gb"]),
    ("dummy", ["dummy"]),
    ("еее", ["E"]),
    ("ммм", ["m"]),
]


def format_entry(word: str, xsampa_phones: list) -> str:
    phone_str = " ".join(xsampa_phones)
    return f"{word} [{word}] {phone_str}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vocab", required=True)
    ap.add_argument("--dict-out", required=True)
    ap.add_argument("--qa-out", default=None)
    args = ap.parse_args()

    vocab_path = Path(args.vocab)
    dict_out = Path(args.dict_out)
    dict_out.parent.mkdir(parents=True, exist_ok=True)

    words = [w.strip() for w in vocab_path.read_text(encoding="utf-8").splitlines() if w.strip()]

    n_ok = 0
    n_failed = 0
    n_variant_lines = 0
    qa_rows = []

    with open(dict_out, "w", encoding="utf-8") as dict_f:
        for sp_word, sp_phones in SPECIAL_ENTRIES:
            dict_f.write(format_entry(sp_word, sp_phones) + "\n")
        for word in words:
            try:
                p = phonemize(word)
                variants = phonemize_variants(word)
            except ValueError as e:
                print(f"[SKIP] {e}", file=sys.stderr)
                n_failed += 1
                continue
            for v in variants:
                dict_f.write(format_entry(word, v) + "\n")
            n_variant_lines += len(variants) - 1
            qa_rows.append((word, p.ipa, p.xsampa))
            n_ok += 1

    print(f"Phonemized {n_ok} words -> {dict_out}")
    print(f"Special entries: {len(SPECIAL_ENTRIES)}; extra pronunciation-variant lines: {n_variant_lines}")
    if n_failed:
        print(f"WARNING: {n_failed} words failed and were skipped.")

    if args.qa_out:
        qa_out = Path(args.qa_out)
        qa_out.parent.mkdir(parents=True, exist_ok=True)
        with open(qa_out, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["word", "ipa", "xsampa"])
            writer.writerows(qa_rows)
        print(f"Wrote QA table -> {qa_out}")


if __name__ == "__main__":
    main()
