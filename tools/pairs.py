"""Reviewer pairs file: `>> id | JP` / `EN` for every translated entry, in id order, +-2 neighbours as context.

    python -X utf8 tools/pairs.py OUT.txt [--lang en] [--ref en]   (--ref adds an earlier language for comparison)
"""
import argparse, glob, json, os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--ref")
    a = ap.parse_args()
    es = []
    for p in sorted(glob.glob(os.path.join(ROOT, "script", "g*.json"))):
        es += json.load(open(p, encoding="utf-8"))
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        for i, e in enumerate(es):
            if e["kind"] != "text" or not e.get(a.lang):
                continue
            ctx = [x["id"] for x in es[max(0, i - 2):i]]
            f.write(">> %s | %s   (context: %s)\n" % (e["id"], e["full"], ", ".join(ctx)))
            if a.ref:
                f.write("   %s: %s\n" % (a.ref.upper(), e.get(a.ref, "")))
            f.write("   %s: %s\n\n" % (a.lang.upper(), e[a.lang]))
    print(a.out)


if __name__ == "__main__":
    main()
