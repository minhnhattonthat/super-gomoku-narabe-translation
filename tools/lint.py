"""Text lint for one language: widths, lines per page, option alignment, leftover Japanese.

    python -X utf8 tools/lint.py [--lang en] [--all]
Width budget per line: data/limits.json "px" for the id (measured box), else the JP line's own width (its 16 px
cells incl. trailing {sp}), which is the field the game drew it in. Exit 1 on errors.
"""
import argparse, glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textfit  # noqa: E402

ROOT = textfit.ROOT
JP_RE = re.compile(r"[぀-ヿ一-鿿]")
KANA_OK = {"g04_19", "g04_20"}  # password kana grid rows: kana are input symbols


def entries():
    for p in sorted(glob.glob(os.path.join(ROOT, "script", "g*.json"))):
        yield from json.load(open(p, encoding="utf-8"))


def var_width(lang, byid):
    return max(textfit.lines(byid[i].get(lang) or "", lang)[0][2] for i in ("g13_00", "g13_01"))


def lint(lang):
    errs = []
    lim = textfit.limits()
    byid = {e["id"]: e for e in entries()}
    vw = textfit.var_width(lang)
    for e in byid.values():
        t = e.get(lang)
        if e["kind"] != "text" or not t:
            continue
        i = e["id"]
        if JP_RE.search(t) and i not in KANA_OK:
            errs.append(f"{i}: Japanese left: {t}")
        x = textfit.expand(e, t, lang)
        en = textfit.lines(x, lang, var_w=vw)
        jp = {(p, l): c for p, l, _, c, _ in textfit.lines(e["full"], "jp", var_w=16)}
        box = lim.get(i, {})
        per_page = {}
        for p, l, px, cells, txt in en:
            per_page[p] = max(per_page.get(p, 0), l + 1)
            budget = box.get("px") or jp.get((p, l), 0) * 16
            if px > budget:
                errs.append(f"{i}: line {p}.{l} is {px} px, budget {budget}: {txt}")
        maxl = box.get("lines")
        if maxl:
            for p, n in per_page.items():
                if n > maxl:
                    errs.append(f"{i}: page {p} has {n} lines (max {maxl})")
        js, es = textfit.segments(e["full"], "jp"), textfit.segments(x, lang)
        for k, starts in js.items():
            if len(starts) > 1 and es.get(k) and len(es[k]) == len(starts) and es[k] != starts:
                errs.append(f"{i}: options start at cells {es[k]}, JP at {starts}")
        if re.search(r"(?<!\.)\.\.(?!\.)", t):
            errs.append(f"{i}: double period")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en")
    a = ap.parse_args()
    errs = lint(a.lang)
    print("\n".join(errs))
    print("%d lint errors" % len(errs))
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
