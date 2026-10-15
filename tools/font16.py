"""16x16 2bpp font of the dialogue/caption renderer ($81:A4E2).

Glyph for code c: bank $88, address $9000 + ((c & $3F8) << 6) + ((c & 7) << 5). Each row of 8 glyphs is a $200-byte
band: 16 SNES 2bpp tiles of top halves, then 16 tiles of bottom halves; glyph = 2x2 tiles.
"""
FONT_OFF = 0x41000  # LoROM $88:9000
NGLYPHS = 0x1C0     # $88:9000-$FFFF


def glyph_off(code):
    return FONT_OFF + ((code & 0x3F8) << 6) + ((code & 7) << 5)


def tile(data, off):
    rows = []
    for y in range(8):
        lo, hi = data[off + y * 2], data[off + y * 2 + 1]
        rows.append([((lo >> (7 - x)) & 1) | (((hi >> (7 - x)) & 1) << 1) for x in range(8)])
    return rows


def glyph(rom, code):
    """16 rows of 16 pixel values (0-3)."""
    o = glyph_off(code)
    tl, tr, bl, br = tile(rom, o), tile(rom, o + 16), tile(rom, o + 0x100), tile(rom, o + 0x110)
    return [tl[y] + tr[y] for y in range(8)] + [bl[y] + br[y] for y in range(8)]
