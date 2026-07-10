import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mk_normalize import normalize_word, is_valid_mk_word  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, help="raw_tokens.txt from step 01")
    ap.add_argument("--vocab-out", required=True)
    ap.add_argument("--freq-out", default=None, help="optional word<TAB>count TSV")
    ap.add_argument("--min-count", type=int, default=1,
                    help="drop words seen fewer than N times")
    ap.add_argument("--min-len", type=int, default=1)
    ap.add_argument("--max-char-run", type=int, default=0,
                    help="drop words with a letter repeated more than N times in a row "
                         "(0 = off). Macedonian never triples a letter, so 2 kills "
                         "elongation spam like 'ааааа' / 'мнооогу'.")
    ap.add_argument("--max-len", type=int, default=0,
                    help="drop words longer than N chars (0 = off), filters "
                         "run-together missing-space strings")
    ap.add_argument("--no-initial-double-vowel", action="store_true",
                    help="drop words starting with a doubled vowel (аа-, оо-): these are "
                         "stutter-typos, no real word starts like that. Word-internal "
                         "double vowels are fine (вакуум).")
    args = ap.parse_args()

    run_re = re.compile(r"(.)\1{%d,}" % args.max_char_run) if args.max_char_run > 0 else None
    _VOWELS = set("аеиоуѐѝ")

    counter = Counter()
    n_run_dropped = 0
    n_len_dropped = 0
    n_dvowel_dropped = 0
    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            w = line.strip()
            if not w:
                continue
            w = normalize_word(w)
            if not is_valid_mk_word(w, min_len=args.min_len):
                continue
            if args.max_len and len(w) > args.max_len:
                n_len_dropped += 1
                continue
            if run_re and run_re.search(w):
                n_run_dropped += 1
                continue
            if args.no_initial_double_vowel and len(w) >= 2 and w[0] == w[1] and w[0] in _VOWELS:
                n_dvowel_dropped += 1
                continue
            counter[w] += 1

    kept = {w: c for w, c in counter.items() if c >= args.min_count}
    words_sorted_alpha = sorted(kept.keys())
    words_sorted_freq = sorted(kept.items(), key=lambda kv: -kv[1])

    vocab_out = Path(args.vocab_out)
    vocab_out.parent.mkdir(parents=True, exist_ok=True)
    with open(vocab_out, "w", encoding="utf-8") as f:
        for w in words_sorted_alpha:
            f.write(w + "\n")

    if args.max_len:
        print(f"Dropped by max-len={args.max_len}: {n_len_dropped} tokens")
    if run_re:
        print(f"Dropped by max-char-run={args.max_char_run}: {n_run_dropped} tokens")
    if args.no_initial_double_vowel:
        print(f"Dropped by no-initial-double-vowel: {n_dvowel_dropped} tokens")
    print(f"Unique raw tokens seen: {len(counter)}")
    print(f"Kept after min-count={args.min_count} filter: {len(kept)}")
    print(f"Wrote vocab -> {vocab_out}")

    if args.freq_out:
        freq_out = Path(args.freq_out)
        freq_out.parent.mkdir(parents=True, exist_ok=True)
        with open(freq_out, "w", encoding="utf-8") as f:
            for w, c in words_sorted_freq:
                f.write(f"{w}\t{c}\n")
        print(f"Wrote frequency list -> {freq_out}")


if __name__ == "__main__":
    main()
