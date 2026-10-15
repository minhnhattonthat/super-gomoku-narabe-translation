"""Dump the 16-bit text block to script/gNN.json (never overwrites a file that exists unless --force).

Entry: {"id": "g05_24", "off": "18AD5", "jp": ..., "full": jp with {ph:XX} expanded, "en": "", "vi": "", "kind": "text"}
kind "data" = not to translate (password answers compared to input, placeholders).
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from codec import Codec  # noqa: E402
import textblock  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def dump(rom):
    c = Codec(os.path.join(ROOT, "tbl", "jp.tbl"))
    rows = [(g, i, off, c.decode(rom, off)[0]) for g, i, off, _ in textblock.groups(rom)]
    phr = {i: t for g, i, _, t in rows if g == 12}
    out = {}
    for g, i, off, t in rows:
        full = re.sub(r"\{ph:([0-9A-F]{2})\}", lambda m: phr.get(int(m[1], 16), m[0]), t)
        out.setdefault(g, []).append({"id": "g%02d_%02d" % (g, i), "off": "%05X" % off, "jp": t, "full": full,
                                      "en": "", "vi": "", "kind": "text"})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    rom = open(a.rom, "rb").read()
    os.makedirs(os.path.join(ROOT, "script"), exist_ok=True)
    for g, entries in dump(rom).items():
        path = os.path.join(ROOT, "script", "g%02d.json" % g)
        if os.path.exists(path) and not a.force:
            print("exists, skipped:", path)
            continue
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(entries, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print("wrote", path, len(entries))


if __name__ == "__main__":
    main()
