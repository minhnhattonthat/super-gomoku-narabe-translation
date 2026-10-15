"""Text codec for the 16x16 renderer ($81:A4B2): a string is 16-bit LE words, ended by $8000.

word < $8000: glyph code (tbl/<lang>.tbl). word >= $8000: control, handler = bits 8-11 ($81:A56D table), arg = low byte:
  80 {end}       81 {ph:XX} insert phrase XX (group XX>>5 of the 83:8237 table, index XX&31)
  82 {nl}        next line ($88 += $400)               83 no-op
  84 {var:XX}    insert string chosen by RAM $9A       85 {num:XX} two digits from $0102/$0103
  86 {wait:XX}   wait for a button (blinks ▼)          87 {sp:N} N blank cells
  88 {se:XX}     sound effect XX ($8080D2)
Anything else decodes as [XXXX] and encodes back unchanged, so decode -> encode is exact.
"""
import re
from pathlib import Path

CTRL = {0x80: "end", 0x81: "ph", 0x82: "nl", 0x84: "var", 0x85: "num", 0x86: "wait", 0x87: "sp", 0x88: "se"}
CTRL_ENC = {v: k for k, v in CTRL.items()}
TOKEN = re.compile(r"\{(\w+)(?::([0-9A-Fa-f]{2}))?\}|\[([0-9A-Fa-f]{4})\]")


def load_tbl(path):
    dec = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            k, _, v = line.partition("=")
            dec[int(k, 16)] = " " if v == r"\s" else v
    enc = {}
    for k, v in dec.items():
        enc.setdefault(v, k)
    return dec, enc


class Codec:
    def __init__(self, tbl_path):
        self.dec, self.enc = load_tbl(tbl_path)
        self.maxlen = max(map(len, self.enc))

    def word_text(self, w):
        if w & 0x8000:
            hi, lo = w >> 8, w & 0xFF
            name = CTRL.get(hi)
            if name is None:
                return "[%04X]" % w
            return "{%s}" % name if lo == 0 and name in ("end", "nl") else "{%s:%02X}" % (name, lo)
        return self.dec.get(w, "[%04X]" % w)

    def decode(self, data, pos):
        """Decode through {end}; returns (text without the final {end}, bytes consumed incl. the end word)."""
        out, start = [], pos
        while True:
            w = data[pos] | data[pos + 1] << 8
            pos += 2
            if w == 0x8000:
                return "".join(out), pos - start
            out.append(self.word_text(w))

    def encode_words(self, text):
        words, i = [], 0
        while i < len(text):
            m = TOKEN.match(text, i)
            if m:
                if m[3]:
                    words.append(int(m[3], 16))
                else:
                    if m[1] not in CTRL_ENC:
                        raise ValueError(f"unknown control {{{m[1]}}} in {text!r}")
                    words.append(CTRL_ENC[m[1]] << 8 | int(m[2] or "0", 16))
                i = m.end()
                continue
            for n in range(min(self.maxlen, len(text) - i), 0, -1):
                if text[i:i + n] in self.enc:
                    words.append(self.enc[text[i:i + n]])
                    i += n
                    break
            else:
                raise ValueError(f"unencodable {text[i]!r} at {i} in {text!r}")
        return words

    def encode(self, text):
        """Bytes of the string including the $8000 terminator."""
        return b"".join(w.to_bytes(2, "little") for w in self.encode_words(text) + [0x8000])
