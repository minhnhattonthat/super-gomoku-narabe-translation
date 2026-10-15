"""Labelled sheet of the 16x16 2bpp font (bank $88:9000) for building and checking tbl/jp.tbl.

    python -X utf8 tools/fontsheet.py ROM OUT.png [--from 0] [--to 0x1C0] [--tbl tbl/jp.tbl]
With --tbl, each cell also shows the table's character (rendered with a system font) under the glyph.
"""
import argparse, os, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from font16 import glyph  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom"); ap.add_argument("out")
    ap.add_argument("--from", dest="lo", type=lambda s: int(s, 0), default=0)
    ap.add_argument("--to", dest="hi", type=lambda s: int(s, 0), default=0x1C0)
    ap.add_argument("--tbl")
    a = ap.parse_args()
    rom = open(a.rom, "rb").read()
    tbl = {}
    if a.tbl:
        for line in open(a.tbl, encoding="utf-8"):
            line = line.rstrip("\n")
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                tbl[int(k, 16)] = v
    jp = None
    for f in ("C:/Windows/Fonts/msgothic.ttc", "C:/Windows/Fonts/YuGothM.ttc"):
        if os.path.exists(f):
            jp = ImageFont.truetype(f, 16)
            break
    cols, z, cw, ch = 16, 2, 48, 64
    n = a.hi - a.lo
    img = Image.new("RGB", (cols * cw, (n + cols - 1) // cols * ch), (40, 40, 60))
    d = ImageDraw.Draw(img)
    for i in range(n):
        code = a.lo + i
        x, y = (i % cols) * cw, (i // cols) * ch
        g = glyph(rom, code)
        for py in range(16):
            for px in range(16):
                v = g[py][px]
                if v:
                    c = (255, 255, 255) if v == 3 else (170, 170, 170) if v == 2 else (100, 100, 100)
                    d.rectangle([x + 8 + px * z, y + 10 + py * z, x + 8 + px * z + 1, y + 10 + py * z + 1], fill=c)
        d.text((x + 2, y), "%03X" % code, fill=(255, 200, 0))
        if code in tbl and jp:
            d.text((x + 30, y + 44), tbl[code][:2], fill=(0, 255, 120), font=jp)
    img.save(a.out)
    print(a.out)


if __name__ == "__main__":
    main()
