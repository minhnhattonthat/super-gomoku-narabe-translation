"""SNES 4bpp tile helpers: 16x16 icons (2x2 tiles laid out in 16-tile rows) <-> index grids.

    python -X utf8 tools/gfx4.py dump BLOCK.bin ICON_TILE [--cols 16]   prints the icon as hex palette indices
"""
import sys


def get_tile(data, t):
    o = t * 32
    px = []
    for y in range(8):
        p0, p1, p2, p3 = data[o + 2 * y], data[o + 2 * y + 1], data[o + 16 + 2 * y], data[o + 17 + 2 * y]
        px.append([((p0 >> (7 - x)) & 1) | ((p1 >> (7 - x)) & 1) << 1 | ((p2 >> (7 - x)) & 1) << 2 |
                   ((p3 >> (7 - x)) & 1) << 3 for x in range(8)])
    return px


def put_tile(data, t, px):
    o = t * 32
    for y in range(8):
        b = [0, 0, 0, 0]
        for x in range(8):
            v = px[y][x]
            for k in range(4):
                b[k] |= ((v >> k) & 1) << (7 - x)
        data[o + 2 * y], data[o + 2 * y + 1], data[o + 16 + 2 * y], data[o + 17 + 2 * y] = b


def get_icon(data, t, cols=16):
    """16x16 icon whose top-left tile is t (tiles t, t+1, t+cols, t+cols+1)."""
    q = [get_tile(data, n) for n in (t, t + 1, t + cols, t + cols + 1)]
    return [q[0][y] + q[1][y] for y in range(8)] + [q[2][y] + q[3][y] for y in range(8)]


def put_icon(data, t, grid, cols=16):
    for n, (dy, dx) in zip((t, t + 1, t + cols, t + cols + 1), ((0, 0), (0, 8), (8, 0), (8, 8))):
        put_tile(data, n, [row[dx:dx + 8] for row in grid[dy:dy + 8]])


def parse_grid(text):
    """16 lines of 16 hex digits ('.' = 0)."""
    rows = [l.strip() for l in text.strip().splitlines()]
    assert len(rows) == 16 and all(len(r) == 16 for r in rows), "icon must be 16x16"
    return [[0 if c == "." else int(c, 16) for c in r] for r in rows]


if __name__ == "__main__" and sys.argv[1] == "dump":
    d = open(sys.argv[2], "rb").read()
    for row in get_icon(d, int(sys.argv[3], 0)):
        print("".join("%X" % v for v in row))
