"""VWF font: font/<lang>.txt (pixel art) -> glyph data + widths for bank $92, and tbl/<lang>.tbl.

Code = $200 + n. ASCII characters use n = ord(c) (so '0' = $230, 'A' = $241); other glyphs get the next free n from
$80 upward. Art row 0 -> cell row 2 (rows 0-1 stay free for marks). Vietnamese ("vi") = the English letters plus
precomposed letters made from them and font/vi_marks.txt (compose_vi).
"""
import os, unicodedata

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NAMES = {"space": " "}
TOP = 2      # cell row of art row 0
XHEIGHT = 5  # cell row of the lowercase x-height top
SHADOW = 1   # colour of the drop shadow
INK = 3


def parse(path, nrows=12):
    """[(name, rows)] in file order; nrows=None accepts any row count (marks)."""
    glyphs, cur = [], None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or (line.startswith("#") and (cur is None or (nrows and len(cur[1]) == nrows))):
            continue
        if line.startswith("="):
            name = line[1:]
            cur = (NAMES.get(name, name), [])
            glyphs.append(cur)
            continue
        cur[1].append(line)
    if nrows:
        for ch, rows in glyphs:
            assert len(rows) == nrows, (ch, len(rows))
    return glyphs


def ink(rows, top=TOP, left=0):
    return {(left + x, top + y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == "#"}


def finish(pts, width=None):
    """16x8 pixel values (ink + drop shadow) and advance width (ink width + 1, max 8)."""
    px = [[0] * 8 for _ in range(16)]
    for x, y in pts:
        assert 0 <= x < 7 and 0 <= y < 16, ("glyph out of its 7x16 box", x, y)
        px[y][x] = INK
    for y in range(15, 0, -1):
        for x in range(7, 0, -1):
            if px[y][x] == 0 and px[y - 1][x - 1] == INK:
                px[y][x] = SHADOW
    if width is None:
        width = max(x for x, _ in pts) + 1 if pts else 3
    return px, min(width + 1, 8)


def tile_bytes(px):
    out = bytearray()
    for y in range(16):
        p0 = p1 = 0
        for x in range(8):
            v = px[y][x]
            p0 |= (v & 1) << (7 - x)
            p1 |= (v >> 1) << (7 - x)
        out += bytes([p0, p1])
    return bytes(out)


# Vietnamese: letter -> (base ASCII letter, base mark or None, tone or None)
VI_BASES = {"ă": ("a", "breve"), "â": ("a", "circumflex"), "ê": ("e", "circumflex"), "ô": ("o", "circumflex"),
            "ơ": ("o", "horn"), "ư": ("u", "horn"), "a": ("a", None), "e": ("e", None), "i": ("i", None),
            "o": ("o", None), "u": ("u", None), "y": ("y", None)}
TONES = {"́": "acute", "̀": "grave", "̉": "hook", "̃": "tilde", "̣": "dot"}


def vi_letters():
    """Every precomposed Vietnamese letter (both cases) except plain ASCII, with (base, mark, tone)."""
    out = {}
    for v, (base, mark) in VI_BASES.items():
        for tone in [None] + list(TONES):
            ch = unicodedata.normalize("NFC", v + (tone or ""))
            info = (base, mark, TONES.get(tone))
            for c, b in ((ch, base), (ch.upper(), base.upper())):
                if len(c) == 1 and ord(c) >= 0x80:
                    out[c] = (b, info[1], info[2])
    out["đ"] = ("d", "bar", None)
    out["Đ"] = ("D", "bar", None)
    return out


def compose_vi(base_ink, marks, base, mark, tone):
    pts = set(base_ink)
    xs = [x for x, _ in pts]
    lo, hi = min(xs), max(xs)
    upper = base.isupper()
    if base == "i":  # the dot gives way to a tone mark
        pts = {(x, y) for x, y in pts if y >= XHEIGHT} if tone and tone != "dot" else pts

    def put(name, top, cx=None, left=None):
        rows = marks[name]
        w = max(len(r) for r in rows)
        if left is None:
            left = round((lo + hi + 1) / 2 - w / 2) if cx is None else cx
        pts.update(ink(rows, top, max(left, 0)))
        return max(left, 0) + w

    if mark == "horn":  # small hook at the top right
        y0 = TOP if upper else XHEIGHT
        pts.update({(hi + 1, y0 - 1), (hi + 1, y0)})
    elif mark == "bar":  # đ: bar across the ascender; Đ: across the stem
        if upper:
            pts = {(x + 1, y) for x, y in pts} | {(0, TOP + 4), (1, TOP + 4), (2, TOP + 4)}
        else:
            stem = hi
            pts.update({(stem - 2, TOP + 1), (stem - 1, TOP + 1), (stem, TOP + 1)})
            if stem + 1 < 7:
                pts.add((stem + 1, TOP + 1))
    if tone == "dot":
        put("dot", TOP + 10)
        tone = None
    base_mark = mark if mark in ("breve", "circumflex") else None
    if upper:
        if base_mark and tone:
            end = put(base_mark, 0, left=lo)
            put(tone, 0, left=min(end - 1, 7 - max(len(r) for r in marks[tone])))
        elif base_mark or tone:
            put(base_mark or tone, 0)
    else:
        if base_mark:
            put(base_mark, 2)
            if tone:
                put(tone, 0)
        elif tone:
            put(tone, 2)
    return pts


def build(lang):
    """Returns (font bytes for n = 0..N-1, width bytes, {char: code})."""
    src = "en" if lang == "vi" else lang
    glyphs = [(ch, ink(rows), max(len(r) for r in rows) if not any("#" in r for r in rows) else None)
              for ch, rows in parse(os.path.join(ROOT, "font", src + ".txt"))]
    if lang == "vi":
        marks = dict(parse(os.path.join(ROOT, "font", "vi_marks.txt"), nrows=None))
        base = {ch: pts for ch, pts, _ in glyphs}
        for ch, (b, mark, tone) in sorted(vi_letters().items()):
            glyphs.append((ch, compose_vi(base[b], marks, b, mark, tone), None))
    codes, nxt = {}, 0x80
    for ch, _, _ in glyphs:
        if len(ch) == 1 and ord(ch) < 0x80:
            codes[ch] = ord(ch)
        else:
            codes[ch] = nxt
            nxt += 1
    n = max(max(codes.values()) + 1, 0x80)
    font, widths = bytearray(32 * n), bytearray(n)  # unused codes (e.g. $27F) draw nothing: width 0
    for ch, pts, w in glyphs:
        px, adv = finish(pts, w)
        i = codes[ch]
        font[i * 32:i * 32 + 32] = tile_bytes(px)
        widths[i] = adv
    return bytes(font), bytes(widths), {ch: 0x200 + i for ch, i in codes.items()}


def write_tbl(lang):
    _, widths, codes = build(lang)
    path = os.path.join(ROOT, "tbl", lang + ".tbl")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("# generated by tools/vwffont.py from font/%s: code=char\n" % lang)
        for ch, code in sorted(codes.items(), key=lambda kv: kv[1]):
            f.write("%03X=%s\n" % (code, "\\s" if ch == " " else ch))
    return path


def widths_by_char(lang):
    _, widths, codes = build(lang)
    return {ch: widths[code - 0x200] for ch, code in codes.items()}


if __name__ == "__main__":
    import sys
    print(write_tbl(sys.argv[1] if len(sys.argv) > 1 else "en"))
