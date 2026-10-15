"""The game's LZSS ($80:8D32, Okumura style): 4 KB ring cleared to 0, start $FEE, flag byte read LSB first
(1 = literal byte, 0 = 2-byte match: pos = b0 | (b1 & $F0) << 4, len = (b1 & $0F) + 3). Stops after `packed` input bytes.

    python -X utf8 tools/lzss.py ROM OFFSET PACKED_LEN OUT.bin     (decompress a block for tiles.py)
"""
import sys

N, F, THRESHOLD, R0 = 4096, 18, 2, 0xFEE


def decompress(data, off, packed):
    ring, r, out, i, flags = bytearray(N), R0, bytearray(), off, 0
    end = off + packed
    while i < end:
        flags >>= 1
        if not flags & 0x100:
            flags = data[i] | 0xFF00
            i += 1
            if i >= end:
                break
        if flags & 1:
            c = data[i]
            i += 1
            out.append(c)
            ring[r] = c
            r = (r + 1) & (N - 1)
        else:
            b0, b1 = data[i], data[i + 1]
            i += 2
            pos, ln = b0 | (b1 & 0xF0) << 4, (b1 & 0x0F) + THRESHOLD + 1
            for k in range(ln):
                c = ring[(pos + k) & (N - 1)]
                out.append(c)
                ring[r] = c
                r = (r + 1) & (N - 1)
    return bytes(out)


def compress(raw):
    """Greedy LZSS for decompress(). Matches reach back into the already-written window only, and the initial zero
    ring for leading zero runs."""
    out, flagpos, bit = bytearray(), 0, 8
    heads = {}
    i, n = 0, len(raw)
    zero_ring = R0 - (N - F)  # ring positions still holding the initial zeros are those not yet written

    def emit_flag():
        nonlocal flagpos, bit
        flagpos = len(out)
        out.append(0)
        bit = 0

    while i < n:
        if bit == 8:
            emit_flag()
        best_len, best_pos = 0, 0
        key = raw[i:i + 3]
        if len(key) == 3:
            for j in reversed(heads.get(key, [])[-64:]):
                if i - j >= N - F:
                    break
                ln = 3
                while ln < F and i + ln < n and raw[j + ln] == raw[i + ln]:
                    ln += 1
                if ln > best_len:
                    best_len, best_pos = ln, (R0 + j) & (N - 1)
                    if ln == F:
                        break
        if best_len < 3 and raw[i] == 0 and i < N - F:
            # the never-written part of the ring is zero: positions after the write pointer
            ln = 0
            while ln < F and i + ln < n and raw[i + ln] == 0:
                ln += 1
            if ln >= 3:
                best_len, best_pos = ln, (R0 + i + F) & (N - 1)
        if best_len >= 3:
            out += bytes([best_pos & 0xFF, (best_pos >> 4) & 0xF0 | (best_len - 3)])
            step = best_len
        else:
            out[flagpos] |= 1 << bit
            out.append(raw[i])
            step = 1
        for k in range(i, min(i + step, n)):
            heads.setdefault(raw[k:k + 3], []).append(k)
        i += step
        bit += 1
    return bytes(out)


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    data = decompress(rom, int(sys.argv[2], 16), int(sys.argv[3], 16))
    open(sys.argv[4], "wb").write(data)
    print(sys.argv[4], hex(len(data)))
