"""Layout model of the patched renderer, used by the build (expansion, wrapping) and the lint.

Engine model (asm/main.asm): a glyph advances VX by its width (JP glyphs 16 px); a cell operation ({sp:N}) first
rounds VX up to a whole 16 px cell, then moves N cells. {nl} starts a line, {wait} a page.

Authoring tokens in translations (expanded by expand() before encoding):
  {to:N}   pad with {sp} to cell N of the current line (N decimal). Use it to line options up with the JP cells.
Automatic: if the JP line ends with {sp:N} (the game clears to a fixed width), the EN line is padded to the same
end cell, so a shorter label still clears a longer one drawn there before.
Wrapping: entries listed in WRAP get {nl} inserted per page to fit their width (author pages with {wait} only).
"""
import json, math, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vwffont  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TOKEN = re.compile(r"(\{[a-z]+(?::[0-9A-Fa-f]+)?\}|\[[0-9A-F]{4}\])")
CELL = 16

_widths = {}


def widths(lang):
    if lang not in _widths:
        _widths[lang] = vwffont.widths_by_char(lang)
    return _widths[lang]


def limits():
    return json.load(open(os.path.join(ROOT, "data", "limits.json"), encoding="utf-8"))


def char_w(ch, lang):
    if lang == "jp":
        return CELL
    w = widths(lang)
    if ch in w:
        return w[ch]
    return CELL  # a JP glyph kept in a translation (kana in password screens)


def lines(text, lang, var_w=0, ph=None):
    """[(page, line, px_end, cell_end, text)] for each line; cell_end counts trailing {sp}."""
    out, page, line, vx, buf = [], 0, 0, 0, []

    def flush():
        out.append((page, line, vx, math.ceil(vx / CELL), "".join(buf)))

    for part in TOKEN.split(text):
        if not part:
            continue
        m = re.match(r"\{([a-z]+)(?::([0-9A-Fa-f]+))?\}", part)
        if m:
            name, arg = m[1], m[2]
            if name == "nl":
                flush(); line += 1; vx = 0; buf = []
            elif name == "wait":
                flush(); page += 1; line = 0; vx = 0; buf = []
            elif name == "sp":
                vx = (math.ceil(vx / CELL) + int(arg, 16)) * CELL
            elif name == "to":  # expands to {sp:K}, K > 0 only when the target is past the current cell
                if int(arg) > math.ceil(vx / CELL):
                    vx = int(arg) * CELL
            elif name == "num":
                vx += 2 * char_w("0", lang)
            elif name in ("var", "turn"):
                vx += var_w
            elif name == "move":
                vx += 3 * char_w("0", lang)
            elif name == "ph" and ph:
                vx += sum(char_w(c, lang) for c in ph.get(int(arg, 16), ""))
            continue
        if part.startswith("["):
            vx += CELL
            continue
        for ch in part:
            vx += char_w(ch, lang)
        buf.append(part)
    flush()
    return out


def segments(text, lang):
    """Start cell of each text run per line: {(page, line): [cells]} (a run starts after a cell operation)."""
    res, page, line, vx, fresh = {}, 0, 0, 0, True
    for part in TOKEN.split(text):
        if not part:
            continue
        m = re.match(r"\{([a-z]+)(?::([0-9A-Fa-f]+))?\}", part)
        if m:
            name, arg = m[1], m[2]
            if name in ("nl", "wait"):
                page, line = (page + 1, 0) if name == "wait" else (page, line + 1)
                vx, fresh = 0, True
            elif name == "sp":
                vx = (math.ceil(vx / CELL) + int(arg, 16)) * CELL
                fresh = True
            elif name == "to":
                if int(arg) > math.ceil(vx / CELL):
                    vx = int(arg) * CELL
                    fresh = True
            continue
        if fresh:
            res.setdefault((page, line), []).append(vx // CELL)
            fresh = False
        vx += sum(char_w(c, lang) for c in part) if not part.startswith("[") else CELL
    return res


def wrap_page(page, maxpx, lang):
    """Greedy-then-balanced wrap of one page (no {nl}); control tokens stick to the following word."""
    words = page.split(" ")

    def w(s):
        return lines(s, lang)[0][2]

    out, cur = [], ""
    for word in words:
        cand = word if not cur else cur + " " + word
        if w(cand) <= maxpx or not cur:
            cur = cand
        else:
            out.append(cur)
            cur = word
    out.append(cur)
    # balance: pull words down while the previous line stays the longer one (avoid one-word last lines)
    for i in range(len(out) - 1, 0, -1):
        while True:
            prev = out[i - 1].split(" ")
            if len(prev) < 2:
                break
            moved = prev[-1] + " " + out[i]
            if w(moved) > maxpx or w(" ".join(prev[:-1])) < w(moved):
                break
            out[i - 1], out[i] = " ".join(prev[:-1]), moved
    return "{nl}".join(out)


def var_width(lang):
    """Widest {var} string (group 13: Black / White) in this language."""
    import glob
    best = 0
    for p in glob.glob(os.path.join(ROOT, "script", "g13.json")):
        for e in json.load(open(p, encoding="utf-8")):
            t = e.get(lang) or ""
            if t:
                best = max(best, lines(t, lang)[0][2])
    return best


def jp_end_cells(jp):
    """{(page, line): end cell} for JP lines that end with {sp} (fixed-width fields)."""
    res, page, line = {}, 0, 0
    for seg in re.split(r"(\{nl\}|\{wait:[0-9A-F]+\})", jp):
        if seg == "{nl}":
            line += 1
            continue
        if seg.startswith("{wait"):
            page, line = page + 1, 0
            continue
        if re.search(r"\{sp:[0-9A-F]+\}$", seg):
            res[(page, line)] = lines(seg, "jp")[0][3]
    return res


def expand(e, text, lang):
    """Authoring text -> engine text: wrap, then pad fixed-width fields, then {to:N} -> {sp:N}."""
    lim = limits().get(e["id"], {})
    if lim.get("wrap"):
        pages = text.split("{wait:00}")
        text = "{wait:00}".join(wrap_page(p, lim["px"], lang) if p else p for p in pages)
    ends = jp_end_cells(e["full"])
    out, page, line = [], 0, 0
    for seg in re.split(r"(\{nl\}|\{wait:[0-9A-F]+\})", text):
        if seg == "{nl}" or seg.startswith("{wait"):
            out.append(seg)
            page, line = (page + 1, 0) if seg.startswith("{wait") else (page, line + 1)
            continue
        if (page, line) in ends and not re.search(r"\{(sp:[0-9A-F]+|to:\d+)\}$", seg):
            seg += "{to:%d}" % ends[(page, line)]
        out.append(seg)
    text = "".join(out)

    # {center:N}: leading spaces so the text up to the next control code is centred on pixel N of the line
    def center(text):
        m = re.search(r"\{center:(\d+)\}", text)
        run = re.match(r"[^{\[]*", text[m.end():]).group(0)
        w = lines(run, lang)[0][2]
        sp = char_w(" ", lang)
        n = max(round((int(m[1]) - w / 2 - lines(text[:m.start()], lang)[-1][2]) / sp), 0)
        return text[:m.start()] + " " * n + text[m.end():]

    while "{center:" in text:
        text = center(text)

    # {to:N} -> {sp:K} with K from the layout up to that point on its line ({var} counted at its widest)
    def repl(text):
        m = re.search(r"\{to:(\d+)\}", text)
        head = text[:m.start()]
        cur = lines(head, lang, var_w=var_width(lang))[-1]
        k = max(int(m[1]) - cur[3], 0)
        return head + ("{sp:%02X}" % k if k else "") + text[m.end():]

    while "{to:" in text:
        text = repl(text)
    return text
