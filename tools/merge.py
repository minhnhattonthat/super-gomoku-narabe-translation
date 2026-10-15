"""Merge a translation TSV (id<TAB>text) into script/gNN.json for one language, after validation.

    python -X utf8 tools/merge.py trans/en.tsv --lang en
Text "=DATA" marks the entry as data (kept Japanese in every language). "=JP" keeps the Japanese for this language.
Refuses the whole file on any error (unknown id, control codes differing from the JP, unencodable characters).
"""
import argparse, collections, glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402

ROOT = build.ROOT
KEEP = re.compile(r"\{(nl|wait|se|num|var)(?::[0-9A-F]{2})?\}")


def ctrl_multiset(text):
    return collections.Counter(m.group(0) for m in KEEP.finditer(text))


def read_tsv(path):
    rows = {}
    for n, line in enumerate(open(path, encoding="utf-8-sig"), 1):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        if "\t" not in line:
            sys.exit(f"{path}:{n}: no TAB")
        k, v = line.split("\t", 1)
        if k in rows:
            sys.exit(f"{path}:{n}: duplicate id {k}")
        rows[k] = v
    return rows


def check(e, text, lang):
    """List of error strings for one translation."""
    errs = []
    want, got = ctrl_multiset(e["full"]), ctrl_multiset(text)
    # {nl} is free inside wrapped entries; elsewhere it must match too
    if build.textfit.limits().get(e["id"], {}).get("wrap"):
        want.pop("{nl}", None), got.pop("{nl}", None)
    if want != got:
        errs.append("control codes differ: jp %s en %s" % (dict(want), dict(got)))
    if re.search(r"\{ph:", text):
        errs.append("{ph} is Japanese grammar; write the text out")
    try:
        build.LANG_CODEC(lang).encode_words(re.sub(r"\{(to|center):\d+\}", "", text))
    except ValueError as ex:
        errs.append(str(ex))
    if re.search(r"\{num:[0-9A-F]{2}\}(st|nd|rd|th)\b", text):
        errs.append("ordinal suffix after a number")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv")
    ap.add_argument("--lang", default="en")
    a = ap.parse_args()
    rows = read_tsv(a.tsv)
    files = {p: json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(ROOT, "script", "g*.json")))}
    byid = {e["id"]: e for es in files.values() for e in es}
    errors = []
    for k, v in rows.items():
        if k not in byid:
            errors.append(f"{k}: unknown id")
            continue
        if v in ("=DATA", "=JP"):
            continue
        errors += [f"{k}: {m}" for m in check(byid[k], v, a.lang)]
    if errors:
        print("\n".join(errors))
        sys.exit("merge refused: %d errors" % len(errors))
    for k, v in rows.items():
        e = byid[k]
        if v == "=DATA":
            e["kind"], e[a.lang] = "data", ""
        elif v == "=JP":
            e[a.lang] = ""
        else:
            e[a.lang] = v
    for p, es in files.items():
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            json.dump(es, f, ensure_ascii=False, indent=1)
            f.write("\n")
    print("merged %d entries" % len(rows))


if __name__ == "__main__":
    main()
