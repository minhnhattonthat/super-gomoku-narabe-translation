"""Graphics text: edit LZSS blocks, recompress them into free banks and repoint every reference.

Each asset: the original block (file offset, packed length), every place that names it (refs), and an edit function
over the decompressed bytes. The original block stays in place untouched; the new one goes to GFX_OFF and up.
Ref kinds: addr16 (low 16 bits of the CPU address), bank16 (16-bit bank operand), bank8, ptr24, len16.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lzss, gfx4  # noqa: E402

GFX_OFF = 0x98000      # $93:8000.. (LoROM), banks $93-$9F free in the 1 MB ROM


def cpu(off):
    return 0x800000 | (off >> 15) << 16 | 0x8000 | (off & 0x7FFF)


# ---- panel icons (BG2, palette 3: 1 tan, 2 white, 3 light blue, 5/6 grey, 7 black, 8 brown)
def _icon(bg, pts, shade=()):
    g = [[bg] * 16 for _ in range(16)]
    for x in range(16):
        g[0][x] = 7
    for y in range(16):
        g[y][0] = 7
    for x, y in pts:
        g[y][x] = 7
    for x, y in shade:
        g[y][x] = 5
    return g


def _tri(base_x, top, h, right):
    """Filled triangle h rows tall from row top, flat side on column base_x, pointing right (right=True) or left."""
    pts = set()
    half = h // 2
    for i in range(h):
        d = i if i < half else h - 1 - i
        for k in range(d + 1):
            pts.add((base_x + k if right else base_x - k, top + i))
    return pts


def icon_replay():   # 再 (replay move by move): play arrow + bar
    pts = _tri(5, 3, 10, right=True) | {(x, y) for x in (11, 12) for y in range(3, 13)}
    return _icon(3, pts, {(x + 1, y + 1) for x, y in pts if (x + 1, y + 1) not in pts and x < 14 and y < 15})


def icon_start():    # 始 (back to the start): bar + double left arrow
    pts = {(x, y) for x in (2, 3) for y in range(3, 13)} | _tri(8, 3, 10, False) | _tri(13, 3, 10, False)
    return _icon(1, pts, {(x + 1, y + 1) for x, y in pts if (x + 1, y + 1) not in pts and x < 14 and y < 15})


def icon_resign():   # 投了 (resign): white flag
    g = _icon(1, {(4, y) for y in range(2, 15)} | {(3, 14), (5, 14)})
    for y in range(3, 10):
        for x in range(5, 14):
            edge = y in (3, 9) or x == 13
            g[y][x] = 7 if edge else 2
    for x, y in ((9, 5), (10, 6), (8, 7)):  # a fold
        g[y][x] = 6
    return g


def edit_panel(raw):
    raw = bytearray(raw)
    gfx4.put_icon(raw, 4, icon_replay())
    gfx4.put_icon(raw, 6, icon_start())
    gfx4.put_icon(raw, 14, icon_resign())
    return bytes(raw)


# ---- mode-menu options card (BG1 palette 6, 8x8 tiles from $A8, 16 tiles per row): 設 -> a gear
def edit_card(raw):
    import math
    raw = bytearray(raw)
    tiles = [[0xA8 + r * 16 + c for c in range(8)] for r in range(8)]
    px = [[0] * 64 for _ in range(64)]
    for r in range(8):
        for c in range(8):
            t = gfx4.get_tile(raw, tiles[r][c])
            for y in range(8):
                px[r * 8 + y][c * 8:c * 8 + 8] = t[y]
    cx, cy = 31.5, 31.0
    for y in range(64):
        for x in range(64):
            d = math.hypot(x - cx, y - cy)
            if d <= 16.5:
                px[y][x] = 0xF  # medallion face
            a = math.atan2(y - cy, x - cx)
            tooth = (math.cos(8 * a) > 0.3)
            outer = 13.0 if tooth else 10.0
            if 4.0 <= d <= outer:
                px[y][x] = 0x8  # gear body (dark green, like the kanji strokes)
            elif outer < d <= outer + 1.0 or 3.0 <= d < 4.0:
                px[y][x] = 0xE  # cream outline
    for r in range(8):
        for c in range(8):
            gfx4.put_tile(raw, tiles[r][c], [px[r * 8 + y][c * 8:c * 8 + 8] for y in range(8)])
    return bytes(raw)


ASSETS = [
    {"name": "panel_icons", "off": 0x04F52A, "len": 0x926, "edit": edit_panel,
     "refs": [("addr16", 0x1CE1), ("bank16", 0x1CE6), ("len16", 0x1CEB), ("ptr24", 0x89CC), ("len16", 0x8A35)]},
    {"name": "mode_cards", "off": 0x05615A, "len": 0x14E3, "edit": edit_card,
     "refs": [("ptr24", 0x89E1), ("len16", 0x8A43), ("addr16", 0x922A), ("bank16", 0x9270), ("len16", 0x92B6)]},
]


def ref_sites():
    """[(file offset, size)] of every byte apply() may change in the original banks."""
    size = {"addr16": 2, "bank16": 2, "bank8": 1, "ptr24": 3, "len16": 2}
    return [(o, size[k]) for a in ASSETS for k, o in a["refs"]]


def apply(rom):
    """Edit, recompress and repoint every asset in rom (bytearray, already 1 MB)."""
    pos = GFX_OFF
    for a in ASSETS:
        raw = lzss.decompress(rom, a["off"], a["len"])
        new = lzss.compress(a["edit"](raw))
        assert lzss.decompress(new, 0, len(new)) == a["edit"](raw)
        if (pos & 0x7FFF) + len(new) > 0x8000:  # never cross a bank
            pos = (pos | 0x7FFF) + 1
        rom[pos:pos + len(new)] = new
        c = cpu(pos)
        for kind, o in a["refs"]:
            if kind == "addr16":
                rom[o:o + 2] = (c & 0xFFFF).to_bytes(2, "little")
            elif kind == "bank16":
                rom[o:o + 2] = (c >> 16).to_bytes(2, "little")
            elif kind == "bank8":
                rom[o] = c >> 16
            elif kind == "ptr24":
                rom[o:o + 3] = c.to_bytes(3, "little")
            elif kind == "len16":
                rom[o:o + 2] = len(new).to_bytes(2, "little")
        pos += len(new)
    assert pos <= 0x100000
