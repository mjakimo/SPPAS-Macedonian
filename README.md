# Macedonian resources for SPPAS

Word list, pronunciation dictionary and related files for Macedonian (mkd),
built for use with [SPPAS](https://sppas.org). Made during my M1 internship
at ATILF (CNRS), based on the phonological description in Mario Jakimoski, Mathilde Hutin: Phonologie du macédonien. 2026. ⟨hal-05667849⟩.

The text data comes from the
[LVSTCK macedonian-corpus-cleaned-dedup](https://huggingface.co/datasets/LVSTCK/macedonian-corpus-cleaned-dedup)
corpus (~1.4 billion tokens of web text).

## What's in this repository

| file | what it is |
|---|---|
| `resources/vocab/mkd.vocab` | word list, 593,791 words, one per line |
| `resources/dict/mkd.dict (zipped)` | pronunciation dictionary (X-SAMPA), ~700k lines including variants |
| `data/mkd_qa.csv (zipped)` | word / IPA / X-SAMPA table for manual review |
| `data/word_freq.tsv` | word frequencies, for tuning the filters |
| `scripts/` | the pipeline that built all of the above |

To use with SPPAS, drop `mkd.vocab` and `mkd.dict` into the `resources/vocab/`
and `resources/dict/` folders of your SPPAS install.

## A few things to know

- Phones are X-SAMPA (that's what SPPAS uses internally), IPA only appears
  in the QA csv.
- The lateral written `л` is encoded as dark /ɫ/ (X-SAMPA `5`). A clear-l
  variant before front vowels is included as an alternative pronunciation.
- Word-final devoicing is applied (леб = `l E p`), with the underlying
  voiced form kept as a variant since devoicing doesn't happen before a
  voiced obstruent in connected speech.
- The dictionary starts with the usual SPPAS special entries (silence `#`,
  laughter `@@`, garbage `gb`, and the fillers `еее`, `ммм`).
- Vocabulary filters: words seen less than 10 times were dropped, plus some
  web-noise cleanup (letter elongations like "ааааа", words over 25 chars,
  stutter-typos starting with a doubled vowel).

## What's missing

- **Acoustic model**, so no forced alignment yet. This is sitll in the works and will be published very soon.


## Rebuilding from scratch

```bash
bash run_codes.sh
```

Downloads the corpus (~several GB), tokenizes it (the intermediate file is
~16 GB), builds and validates everything. Takes around 30–40 minutes total.

If you only change the G2P, you can just need steps 03 and 04 (which will take only a few minutes):

```bash
python3 scripts/build_dict.py --vocab resources/vocab/mkd.vocab \
    --dict-out resources/dict/mkd.dict --qa-out data/mkd_qa.csv
python3 scripts/validate_dict.py --vocab resources/vocab/mkd.vocab \
    --dict resources/dict/mkd.dict
```
