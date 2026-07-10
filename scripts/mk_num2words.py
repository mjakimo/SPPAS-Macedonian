from __future__ import annotations

UNITS = ["нула", "еден", "два", "три", "четири", "пет", "шест", "седум", "осум", "девет"]
UNITS_FEM = ["нула", "една", "две", "три", "четири", "пет", "шест", "седум", "осум", "девет"]
TEENS = ["десет", "единаесет", "дванаесет", "тринаесет", "четиринаесет",
         "петнаесет", "шеснаесет", "седумнаесет", "осумнаесет", "деветнаесет"]
TENS = ["", "", "дваесет", "триесет", "четириесет", "педесет",
        "шеесет", "седумдесет", "осумдесет", "деведесет"]
HUNDREDS = ["", "сто", "двесте", "триста", "четиристотини", "петстотини",
            "шестотини", "седумстотини", "осумстотини", "деветстотини"]


def _under_1000(n: int, feminine: bool = False) -> list:
    # "и" goes before the last component: сто дваесет и три, сто и пет
    units = UNITS_FEM if feminine else UNITS
    parts = []
    h, rest = divmod(n, 100)
    if h:
        parts.append(HUNDREDS[h])
    if rest == 0:
        return parts
    t, u = divmod(rest, 10)
    if t == 1:
        tail = [TEENS[u]]
    elif t and u:
        tail = [TENS[t], "и", units[u]]
    elif t:
        tail = [TENS[t]]
    else:
        tail = [units[u]]
    if parts and "и" not in tail:
        parts.append("и")
    parts.extend(tail)
    return parts


def num2words(n, feminine: bool = False) -> str:
    n = int(n)
    if n < 0:
        return "минус " + num2words(-n, feminine)
    if n == 0:
        return "нула"
    if n >= 1_000_000_000_000:
        raise ValueError(f"{n} out of supported range (< 10^12)")

    words = []
    billions, n = divmod(n, 1_000_000_000)
    millions, n = divmod(n, 1_000_000)
    thousands, n = divmod(n, 1_000)

    # compounds ending in 1 (but not 11) take the singular:
    # дваесет и една илјада, дваесет и еден милион
    def _ends_in_one(k: int) -> bool:
        return k % 10 == 1 and k % 100 != 11

    if billions:
        if billions == 1:
            words.append("милијарда")
        else:
            noun = "милијарда" if _ends_in_one(billions) else "милијарди"
            words += _under_1000(billions, feminine=True) + [noun]
    if millions:
        if millions == 1:
            words.append("милион")
        else:
            noun = "милион" if _ends_in_one(millions) else "милиони"
            words += _under_1000(millions) + [noun]
    if thousands:
        if thousands == 1:
            words.append("илјада")
        else:
            noun = "илјада" if _ends_in_one(thousands) else "илјади"
            words += _under_1000(thousands, feminine=True) + [noun]
    if n:
        tail = _under_1000(n, feminine)
        # 1001 -> илјада и еден, but 1123 -> илјада сто дваесет и три
        if words and "и" not in tail and len(tail) == 1:
            words.append("и")
        words += tail
    return " ".join(words)


if __name__ == "__main__":
    cases = {
        0: "нула",
        21: "дваесет и еден",
        105: "сто и пет",
        123: "сто дваесет и три",
        999: "деветстотини деведесет и девет",
        1001: "илјада и еден",
        2024: "две илјади дваесет и четири",
        11000: "единаесет илјади",
        21000: "дваесет и една илјада",
        21000000: "дваесет и еден милион",
        123456789: "сто дваесет и три милиони четиристотини педесет и шест илјади седумстотини осумдесет и девет",
    }
    failed = 0
    for n, expected in cases.items():
        got = num2words(n)
        if got != expected:
            failed += 1
            print(f"[FAIL] {n}: got {got!r}, expected {expected!r}")
        else:
            print(f"[ok] {n} -> {got}")
    raise SystemExit(1 if failed else 0)
