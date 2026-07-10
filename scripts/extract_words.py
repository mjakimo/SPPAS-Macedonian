import argparse
import bz2
import gzip
import json
import re
import sys
import zipfile
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mk_normalize import TOKEN_RE, normalize_homoglyphs  # noqa: E402

XML_TAG_RE = re.compile(r"<[^>]+>")
WIKILINK_RE = re.compile(r"\[\[([^\]|]+\|)?([^\]]+)\]\]")
TEMPLATE_RE = re.compile(r"\{\{[^{}]*\}\}")
REF_RE = re.compile(r"<ref[^>]*>.*?</ref>", re.DOTALL)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
HTML_ENTITY_RE = re.compile(r"&[a-zA-Z#0-9]+;")
URL_RE = re.compile(r"https?://\S+")


def strip_wikitext(text: str) -> str:
    text = REF_RE.sub(" ", text)
    text = COMMENT_RE.sub(" ", text)
    text = TEMPLATE_RE.sub(" ", text)
    text = WIKILINK_RE.sub(r"\2", text)
    text = XML_TAG_RE.sub(" ", text)
    text = URL_RE.sub(" ", text)
    text = HTML_ENTITY_RE.sub(" ", text)
    return text


@contextmanager
def _open_text(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".bz2":
        f = bz2.open(path, "rt", encoding="utf-8", errors="ignore")
    elif suffix == ".gz":
        f = gzip.open(path, "rt", encoding="utf-8", errors="ignore")
    else:
        f = open(path, "r", encoding="utf-8", errors="ignore")
    try:
        yield f
    finally:
        f.close()


def iter_text_streams(path: Path):
    """Yield (name, stream) for a file, directory or zip archive."""
    if path.is_dir():
        for fp in sorted(path.rglob("*")):
            if fp.is_dir():
                continue
            try:
                with _open_text(fp) as f:
                    yield str(fp), f
            except Exception as e:
                print(f"[skip] {fp}: {e}", file=sys.stderr)
        return

    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            for member in zf.namelist():
                if member.endswith("/"):
                    continue
                inner = member.lower()
                with zf.open(member) as raw:
                    if inner.endswith(".bz2"):
                        stream = bz2.open(raw, "rt", encoding="utf-8", errors="ignore")
                    elif inner.endswith(".gz"):
                        stream = gzip.open(raw, "rt", encoding="utf-8", errors="ignore")
                    else:
                        stream = (line.decode("utf-8", "ignore") for line in raw)
                        stream = _LineIter(stream)
                    yield f"{path}::{member}", stream
        return

    with _open_text(path) as f:
        yield str(path), f


class _LineIter:
    def __init__(self, gen):
        self._gen = gen

    def __iter__(self):
        return self._gen

    def read(self):
        return "".join(self._gen)


def iter_xml_text_blocks(stream):
    buf = []
    in_text = False
    for line in stream:
        if "<text" in line and not in_text:
            in_text = True
            line = re.sub(r"^.*?<text[^>]*>", "", line)
        if in_text:
            if "</text>" in line:
                line = line.split("</text>")[0]
                buf.append(line)
                yield "".join(buf)
                buf = []
                in_text = False
            else:
                buf.append(line)


def extract_tokens_from_text(text: str):
    cleaned = strip_wikitext(text)
    for m in TOKEN_RE.finditer(cleaned):
        yield normalize_homoglyphs(m.group(0))


def extract_tokens_plain(text: str):
    # jsonl corpora are already clean prose, skip the wikitext pass
    for m in TOKEN_RE.finditer(text):
        yield normalize_homoglyphs(m.group(0))


def iter_jsonl_texts(stream, field: str):
    for lineno, line in enumerate(stream, 1):
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line).get(field, "")
        except json.JSONDecodeError as e:
            # don't kill a multi-hour run over one bad line
            print(f"[skip] malformed JSON at line {lineno}: {e}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--mode", choices=["xml", "text", "jsonl"], default="text")
    ap.add_argument("--json-field", default="text",
                    help="JSON key holding the document text (jsonl mode)")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n_tokens = 0
    with open(out_path, "w", encoding="utf-8") as out_f:
        for name, stream in iter_text_streams(in_path):
            if args.mode == "xml":
                for block in iter_xml_text_blocks(stream):
                    for tok in extract_tokens_from_text(block):
                        out_f.write(tok + "\n")
                        n_tokens += 1
            elif args.mode == "jsonl":
                for text in iter_jsonl_texts(stream, args.json_field):
                    for tok in extract_tokens_plain(text):
                        out_f.write(tok + "\n")
                        n_tokens += 1
            else:
                content = stream.read()
                for tok in extract_tokens_from_text(content):
                    out_f.write(tok + "\n")
                    n_tokens += 1

    print(f"Extracted {n_tokens} raw tokens -> {out_path}")


if __name__ == "__main__":
    main()
