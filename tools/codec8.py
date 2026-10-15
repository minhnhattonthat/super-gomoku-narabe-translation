"""8-bit strings for the 8x8 font (tiles = codes, ROM $88:8000): tables at 83:801A / 83:8022, strings end with $04.

ASCII $20-$7E ($40 is drawn as ©). $81-$BD hiragana, $C6-$FD katakana in JIS X0201 order; $BE/$BF = dakuten /
handakuten, written BEFORE the kana they mark. $02 XX = control with one argument byte ({c02:XX}).
Unknown bytes decode as [XX].
"""
HIRA = "。「」、・をぁぃぅぇぉゃゅょっーあいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわん゛゜"
KATA = "ヲァィゥェォャュョッーアイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワン"

DEC = {c: chr(c) for c in range(0x20, 0x7F)}
DEC[0x40] = "©"
DEC.update({0x81 + i: ch for i, ch in enumerate(HIRA)})
DEC.update({0xC6 + i: ch for i, ch in enumerate(KATA)})
ENC = {}
for k, v in DEC.items():
    ENC.setdefault(v, k)
ENC["@"] = 0x40


def decode(data, pos):
    out, start = [], pos
    while True:
        b = data[pos]
        pos += 1
        if b == 0x04:
            return "".join(out), pos - start
        if b == 0x02:
            out.append("{c02:%02X}" % data[pos])
            pos += 1
        else:
            out.append(DEC.get(b, "[%02X]" % b))


def encode(text):
    import re
    out, i = bytearray(), 0
    while i < len(text):
        m = re.match(r"\{c02:([0-9A-Fa-f]{2})\}|\[([0-9A-Fa-f]{2})\]", text[i:])
        if m:
            out += bytes([2, int(m[1], 16)]) if m[1] else bytes([int(m[2], 16)])
            i += m.end()
            continue
        if text[i] not in ENC:
            raise ValueError(f"unencodable {text[i]!r} in {text!r}")
        out.append(ENC[text[i]])
        i += 1
    return bytes(out + b"\x04")
