"""The 16-bit text block in bank $83: group pointer table at 83:8237 (14 x 16-bit), then the strings.

A text id is (group, index): group = id >> 5 via the table, index = id & 31 counted by $8000 terminators
($81:A7B0 for screen text, $81:A763 for {ph} = group 12, $81:A742 for {var} = group 13).
"""
TABLE = 0x18237     # 83:8237
NGROUPS = 14
END = 0x1A2D7       # first byte after the block (palette data follows)
BANK83 = 0x18000


def lorom(addr):
    return ((addr & 0x7F0000) >> 1) | (addr & 0x7FFF)


def groups(rom):
    """[(group, index, offset, length_bytes_incl_end)] for every string in the original block."""
    ptrs = [rom[TABLE + i * 2] | rom[TABLE + i * 2 + 1] << 8 for i in range(NGROUPS)]
    offs = [BANK83 + (p - 0x8000) for p in ptrs] + [END]
    out = []
    for g in range(NGROUPS):
        pos, i = offs[g], 0
        while pos < offs[g + 1]:
            n = pos
            while rom[n] | rom[n + 1] << 8 != 0x8000:
                n += 2
            out.append((g, i, pos, n + 2 - pos))
            pos, i = n + 2, i + 1
        assert pos == offs[g + 1], (g, hex(pos))
    return out


def pack(strings_by_group, base_cpu):
    """strings_by_group: list of 14 lists of encoded strings (bytes incl. $8000). Returns (table+strings bytes),
    with the table at base_cpu (16-bit pointers, same bank)."""
    table, body = bytearray(), bytearray()
    pos = (base_cpu & 0xFFFF) + NGROUPS * 2
    for grp in strings_by_group:
        table += (pos + len(body)).to_bytes(2, "little")
        for s in grp:
            body += s
    blob = bytes(table + body)
    assert (base_cpu & 0xFFFF) + len(blob) <= 0x10000, "text block crosses the bank"
    return blob
