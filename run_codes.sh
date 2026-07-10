# Warning: the intermediate raw_tokens file is ~16 GB.
set -euo pipefail
cd "$(dirname "$0")"

CORPUS_DIR="tmp_corpus"

python3 - <<'PY'
from pathlib import Path
from huggingface_hub import snapshot_download

local_dir = Path("tmp_corpus")
already = list(local_dir.rglob("*.jsonl.gz")) if local_dir.exists() else []
if not already:
    snapshot_download(
        repo_id="LVSTCK/macedonian-corpus-cleaned-dedup",
        repo_type="dataset",
        local_dir=str(local_dir),
        allow_patterns=["*.jsonl.gz"],
    )
gz = next(local_dir.rglob("*.jsonl.gz"))
print(f"corpus: {gz} ({gz.stat().st_size/1e6:.0f} MB compressed)")
PY

GZ_PATH=$(find "$CORPUS_DIR" -name "*.jsonl.gz" | head -1)

python3 scripts/extract_words.py \
    --input "$GZ_PATH" --mode jsonl --json-field text \
    --output data/raw_tokens.txt

python3 scripts/clean_vocab.py \
    --input data/raw_tokens.txt \
    --vocab-out resources/vocab/mkd.vocab \
    --freq-out data/word_freq.tsv \
    --min-count 10 --max-char-run 2 --max-len 25 --no-initial-double-vowel

python3 scripts/build_dict.py \
    --vocab resources/vocab/mkd.vocab \
    --dict-out resources/dict/mkd.dict \
    --qa-out data/mkd_qa.csv

python3 scripts/validate_dict.py \
    --vocab resources/vocab/mkd.vocab \
    --dict resources/dict/mkd.dict

echo
echo "Done. Outputs: resources/vocab/mkd.vocab, resources/dict/mkd.dict"
