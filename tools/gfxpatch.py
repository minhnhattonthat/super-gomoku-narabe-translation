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


# ---- certificates (BG1 palette 5: 0 clear, 1 black, 2-8 greys). Tiles 0x05BDD5 are shared by four raw 32x32
# tilemaps at 0x30002 + k*0x800 (2-byte header before each; table B ids 30-33 via $81:9168, maps at $81:940C):
# 0 名人戦 (tournament, $81:D148), 1 二手勝ち, 2 四追い, 3 追い詰め (puzzle category -> id table $81:CE5F).
# The JP text is vertical; the translation is horizontal, one character per 8x16 cell (tiles depend on the
# letters used, not the text length).
CERT_MAPS = 0x30002
CERT_SEAL = [[0x02, 0x03, 0x04], [0x12, 0x13, 0x14], [0x05, 0x06, 0x07], [0x15, 0x16, 0x17]]
CERT_TEXT = {
    "en": {"lines": ["This award is", "presented to you", "in honor of your"],
           "tournament": ["victory in every", "round of the", "Master Cup."],
           "puzzle": ["solving the hard", "{cat}", "problems."],
           "cats": ["Chase-Down", "Win in Two", "Four-Chase"]},
}


def cert_texts(lang):
    t = CERT_TEXT[lang]
    out = []
    for k, cat in ((0, None), (1, t["cats"][1]), (2, t["cats"][2]), (3, t["cats"][0])):
        tail = t["tournament"] if cat is None else [s.replace("{cat}", cat) for s in t["puzzle"]]
        out.append(t["lines"] + tail)
    return out


def edit_certs(raw, rom, lang):
    import vwffont
    font_bytes, _, codes = vwffont.build(lang)
    raw = bytearray(raw)
    keep = {0} | {t for row in CERT_SEAL for t in row}
    free = [t for t in range(len(raw) // 32) if t not in keep]
    tiles = {}  # (top/bottom, char) -> tile

    def cell_tiles(ch):
        if ch == " ":
            return 0, 0
        if ch not in tiles:
            n = codes[ch] - 0x200
            g = font_bytes[n * 32:n * 32 + 32]
            w = max((x for y in range(16) for x in range(8)
                     if (g[2 * y] | g[2 * y + 1]) & (0x80 >> x)), default=0) + 1
            dx = (8 - w) // 2
            pair = []
            for half in (0, 8):
                px = []
                for y in range(half, half + 8):
                    p0, p1 = g[2 * y], g[2 * y + 1]
                    row = [((p0 >> (7 - x)) & 1) | ((p1 >> (7 - x)) & 1) << 1 for x in range(8)]
                    row = [0] * dx + row[:8 - dx]
                    px.append([{0: 0, 1: 6, 2: 4, 3: 1}[v] for v in row])  # ink black, shadow light grey
                t = free.pop(0)
                gfx4.put_tile(raw, t, px)
                pair.append(t)
            tiles[ch] = tuple(pair)
        return tiles[ch]

    for k, lines in enumerate(cert_texts(lang)):
        base = CERT_MAPS + k * 0x800
        ent = lambda t: (t | 0x1400).to_bytes(2, "little")
        for row in range(8, 22):
            for col in range(4, 28):
                rom[base + (row * 32 + col) * 2:base + (row * 32 + col) * 2 + 2] = ent(0)
        for r, line in enumerate(lines):
            assert len(line) <= 22, line
            c0 = 16 - (len(line) + 1) // 2
            for i, ch in enumerate(line):
                top, bot = cell_tiles(ch)
                for dr, t in ((0, top), (1, bot)):
                    o = base + ((8 + 2 * r + dr) * 32 + c0 + i) * 2
                    rom[o:o + 2] = ent(t)
        for dr, trow in enumerate(CERT_SEAL):
            for dc, t in enumerate(trow):
                o = base + ((18 + dr) * 32 + 23 + dc) * 2
                rom[o:o + 2] = ent(t)
    return bytes(raw)


# ---- title logo (OBJ, palette 0: F dark outline, 3/4/5 pink shades). The brush-written 連珠 ("Renju") stays as
# the logo; the pink vertical スーパー五目ならべ (two 64 px columns of 16x16 sprites at x 168) becomes SUPER / GOMOKU,
# upright letters stacked like the Japanese. The metasprite at 0x101D5 used tile $28 twice (ー): its 4th record
# gets the free tile $0A.
TITLE_COLS = [[0x08, 0x28, 0x48, 0x0A], [0x0C, 0x2C, 0x0E, 0x2E]]
TITLE_META_TILE = 0x101E1
LETTERS = {
    "S": [".######.", "########", "##......", "##......", ".######.", "......##", "......##", "########",
          ".######."],
    "U": ["##....##"] * 7 + ["########", ".######."],
    "P": ["#######.", "########", "##....##", "##....##", "########", "#######.", "##......", "##......",
          "##......"],
    "E": ["########", "########", "##......", "##......", "######..", "##......", "##......", "########",
          "########"],
    "R": ["#######.", "########", "##....##", "##....##", "########", "#######.", "##..##..", "##...##.",
          "##....##"],
    "G": [".######.", "########", "##......", "##......", "##..####", "##..####", "##....##", "########",
          ".######."],
    "O": [".######.", "########"] + ["##....##"] * 5 + ["########", ".######."],
    "M": ["##....##", "###..###", "########", "##.##.##", "##.##.##"] + ["##....##"] * 4,
    "K": ["##....##", "##...##.", "##..##..", "##.##...", "####....", "##.##...", "##..##..", "##...##.",
          "##....##"],
}
TITLE_WORDS = {"en": ["SUPER", "GOMOKU"]}


def edit_title(raw, rom, lang):
    raw = bytearray(raw)
    words = TITLE_WORDS.get(lang, TITLE_WORDS["en"])
    for tiles, word in zip(TITLE_COLS, words):
        img = [[0] * 16 for _ in range(64)]
        step = 64 / len(word)
        for i, ch in enumerate(word):
            top = int(i * step + (step - 11) / 2) + 1
            for y, row in enumerate(LETTERS[ch]):
                for x, c in enumerate(row):
                    if c == "#":
                        img[top + y][4 + x] = 3 if y < 4 else 4
        out = [row[:] for row in img]
        for y in range(64):
            for x in range(16):
                if img[y][x] == 0 and any(0 <= y + dy < 64 and 0 <= x + dx < 16 and img[y + dy][x + dx]
                                          for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                    out[y][x] = 0xF
        for k, t in enumerate(tiles):
            gfx4.put_icon(raw, t, [row for row in out[k * 16:k * 16 + 16]])
    rom[TITLE_META_TILE] = 0x0A
    return bytes(raw)


ASSETS = [
    {"name": "panel_icons", "off": 0x04F52A, "len": 0x926, "edit": edit_panel,
     "refs": [("addr16", 0x1CE1), ("bank16", 0x1CE6), ("len16", 0x1CEB), ("ptr24", 0x89CC), ("len16", 0x8A35)]},
    {"name": "mode_cards", "off": 0x05615A, "len": 0x14E3, "edit": edit_card,
     "refs": [("ptr24", 0x89E1), ("len16", 0x8A43), ("addr16", 0x922A), ("bank16", 0x9270), ("len16", 0x92B6)]},
    {"name": "title_logo", "off": 0x05ABAC, "len": 0xBDE, "edit": edit_title, "raw": [(TITLE_META_TILE, 1)],
     "refs": [("ptr24", 0x89C6), ("len16", 0x8A31), ("ptr24", 0x8E74), ("len16", 0x8E81), ("addr16", 0xAB6E),
              ("bank16", 0xAB73), ("len16", 0xAB78)]},
    {"name": "certificates", "off": 0x05BDD5, "len": 0x1264, "edit": edit_certs, "raw": [(CERT_MAPS, 0x2000)],
     "refs": [("addr16", 0x925E + 2 * i) for i in range(4)] + [("bank16", 0x92A4 + 2 * i) for i in range(4)] +
             [("len16", 0x92EA + 2 * i) for i in range(4)]},
]


def ref_sites():
    """[(file offset, size)] of every byte apply() may change in the original banks."""
    size = {"addr16": 2, "bank16": 2, "bank8": 1, "ptr24": 3, "len16": 2}
    return [(o, size[k]) for a in ASSETS for k, o in a["refs"]] + [r for a in ASSETS for r in a.get("raw", [])]


def apply(rom, lang):
    """Edit, recompress and repoint every asset in rom (bytearray, already 1 MB)."""
    import inspect
    pos = GFX_OFF
    for a in ASSETS:
        raw = lzss.decompress(rom, a["off"], a["len"])
        edit = a["edit"]
        edited = edit(raw, rom, lang) if len(inspect.signature(edit).parameters) == 3 else edit(raw)
        new = lzss.compress(edited)
        assert lzss.decompress(new, 0, len(new)) == edited
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
