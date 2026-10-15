"""Build a translated ROM.

    python -X utf8 tools/build.py --lang en [--marker] [--out build/gomoku_en.sfc]
    python -X utf8 tools/build.py --lang jp           # identity: re-encodes the text in place, no engine patch

Lang builds: expand to 1 MB, text block -> $91:8000, VWF font -> $92:8000 (widths $92:C000), asm/main.asm via asar.
An entry with kind "data", or with no translation in --lang, is written from its Japanese.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from codec import Codec  # noqa: E402
import gfxpatch, textblock, textfit, vwffont  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ASAR = os.path.join(ROOT, "tools", "asar", "asar.exe")
TEXT_CPU, TEXT_OFF = 0x918000, 0x88000
FONT_OFF, FONTW_OFF, SHTAB_OFF = 0x90000, 0x94000, 0x95000
SIZE = 0x100000
PRE_OFF = 0xD0000  # $9A:8000.. pre-shifted VWF glyphs (asm/main.asm draw_pre), 64 glyphs per bank, up to $9F


def preshift(font):
    """For each glyph n and shift s (1-8): 16 rows x (tile A word, tile B word), each word = plane0 | plane1 << 8,
    the glyph row shifted right by s from the left edge of tile A."""
    n = len(font) // 32
    assert n <= 6 * 64, "pre-shifted font does not fit in banks $9A-$9F"
    out = bytearray(b"\xFF" * 0x30000)
    for g in range(n):
        base = (g >> 6) * 0x8000 + (g & 63) * 512
        for s in range(1, 9):
            o = base + (s - 1) * 64
            for r in range(16):
                p0, p1 = font[g * 32 + 2 * r], font[g * 32 + 2 * r + 1]
                g0, g1 = (p0 << 8) >> s, (p1 << 8) >> s
                out[o + r * 4:o + r * 4 + 4] = bytes([g0 >> 8, g1 >> 8, g0 & 0xFF, g1 & 0xFF])
    return bytes(out)


def load_script():
    entries = []
    for path in sorted(glob.glob(os.path.join(ROOT, "script", "g*.json"))):
        entries += json.load(open(path, encoding="utf-8"))
    return entries


def marker(e):
    """Keep the control codes, replace each text run: first run = id, later runs = 'x'."""
    parts, first = re.split(r"(\{[^}]*\}|\[[0-9A-F]{4}\])", e["full"]), True
    out = []
    for p in parts:
        if not p:
            continue
        if p.startswith("{") or p.startswith("["):
            out.append(p)
        else:
            out.append(e["id"][1:].replace("_", "-") if first else "x")
            first = False
    return "".join(out)


def text_for(e, lang, mark):
    if e["kind"] != "text" or lang == "jp":
        return None
    if mark:
        return marker(e) if mark is True or re.match(mark, e["id"]) else None
    return e.get(lang) or None


def build(lang, out, mark=False, rom_path=None, overrides=None):
    rom = bytearray(open(rom_path or os.path.join(ROOT, "rom", "orig.sfc"), "rb").read())
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    jp = Codec(os.path.join(ROOT, "tbl", "jp.tbl"))
    entries = load_script()
    groups = [[] for _ in range(textblock.NGROUPS)]
    for e in entries:
        g = int(e["id"][1:3])
        t = text_for(e, lang, mark)
        if overrides and e["id"] in overrides:
            t = overrides[e["id"]]
        if t is None:
            groups[g].append(jp.encode(e["jp"]))
        else:
            if not mark:
                t = textfit.expand(e, t, lang)
            groups[g].append(LANG_CODEC(lang).encode(t))
    if lang == "jp":  # identity
        blob = textblock.pack(groups, 0x838237)
        assert len(blob) == textblock.END - textblock.TABLE
        rom[textblock.TABLE:textblock.END] = blob
        open(out, "wb").write(rom)
        return out
    rom += b"\xFF" * (SIZE - len(rom))
    rom[0x7FD7] = 0x0A  # header: 1 MB
    blob = textblock.pack(groups, TEXT_CPU)
    rom[TEXT_OFF:TEXT_OFF + len(blob)] = blob
    font, widths, _ = vwffont.build(lang)
    assert len(font) <= 0x4000 and len(widths) <= 0x1000
    rom[FONT_OFF:FONT_OFF + len(font)] = font
    rom[FONTW_OFF:FONTW_OFF + len(widths)] = widths
    gfxpatch.apply(rom, lang)
    rom[PRE_OFF:PRE_OFF + 0x30000] = preshift(font)
    for s in range(1, 9):  # SHTAB ($92:D000) for draw8
        for p in range(256):
            o = SHTAB_OFF + (s - 1) * 512 + p * 2
            rom[o:o + 2] = ((p << 8) >> s).to_bytes(2, "little")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    tmp = out + ".tmp"
    open(tmp, "wb").write(rom)
    r = subprocess.run([ASAR, "--no-title-check", "--fix-checksum=off", os.path.join(ROOT, "asm", "main.asm"), tmp],
                       capture_output=True, text=True)
    if r.returncode:
        os.remove(tmp)
        sys.exit("asar failed:\n" + r.stdout + r.stderr)
    os.replace(tmp, out)
    return out


_codecs = {}


def LANG_CODEC(lang):
    """The language's VWF table, falling back to JP glyphs for characters it lacks (kana on password screens)."""
    if lang not in _codecs:
        vwffont.write_tbl(lang)
        c = Codec(os.path.join(ROOT, "tbl", lang + ".tbl"))
        jp = Codec(os.path.join(ROOT, "tbl", "jp.tbl"))
        for ch, code in jp.enc.items():
            c.enc.setdefault(ch, code)
        c.maxlen = max(map(len, c.enc))
        _codecs[lang] = c
    return _codecs[lang]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en")
    ap.add_argument("--marker", nargs="?", const=True, default=False,
                    help="marker text for every line, or only for ids matching this regex (bisecting)")
    ap.add_argument("--set", action="append", default=[], metavar="ID=TEXT",
                    help="QA override of one line (width tests, torture lines)")
    ap.add_argument("--out")
    a = ap.parse_args()
    out = a.out or os.path.join(ROOT, "build", "gomoku_%s%s.sfc" % (a.lang, "_marker" if a.marker else ""))
    print(build(a.lang, out, a.marker, overrides=dict(s.split("=", 1) for s in a.set)))


if __name__ == "__main__":
    main()
