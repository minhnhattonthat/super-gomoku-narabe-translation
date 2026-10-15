"""Release gate + package: lint -> tests -> build -> leftover-Japanese scan -> smoke -> checksum -> BPS (re-applied
and compared) -> zip with README. Stops at the first failure. Never uploads anything.

    python -X utf8 tools/release.py --lang en --version 1.0 [--no-smoke]
Output: release/<lang>/Super_Gomoku_Narabe_Renju_<LANG>_v<version>.zip (patch + README only).
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, zipfile, zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build, lint, textblock  # noqa: E402
from codec import Codec  # noqa: E402

ROOT = build.ROOT
SK = os.path.join(ROOT, ".claude", "skills", "translate-retro-game", "scripts")
ORIG = os.path.join(ROOT, "rom", "orig.sfc")
JP_RE = re.compile(r"[぀-ヿ一-鿿]")


def run(cmd, what):
    print("==", what)
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode:
        sys.exit(f"release stopped: {what} failed ({r.returncode})")


def leftover_japanese(rom, lang):
    """Decode the built text block; Japanese is allowed only in entries marked data (passwords, kana grid)."""
    entries = build.load_script()
    c = build.LANG_CODEC(lang)
    dec = Codec(os.path.join(ROOT, "tbl", "jp.tbl")).dec
    dec.update({v: k for k, v in c.enc.items() if v >= 0x200})
    base = build.TEXT_OFF
    ptr = [rom[base + i * 2] | rom[base + i * 2 + 1] << 8 for i in range(textblock.NGROUPS)]
    bad, gi = [], {}
    for e in entries:
        g = int(e["id"][1:3])
        off = gi.get(g, base + ptr[g] - 0x8000)
        words = []
        while True:
            w = rom[off] | rom[off + 1] << 8
            off += 2
            if w == 0x8000:
                break
            if w < 0x8000:
                words.append(dec.get(w, "?"))
        gi[g] = off
        text = "".join(words)
        if JP_RE.search(text) and e["kind"] == "text" and e["id"] not in lint.KANA_OK:
            bad.append(f"{e['id']}: {text}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en")
    ap.add_argument("--version", required=True)
    ap.add_argument("--no-smoke", action="store_true")
    a = ap.parse_args()
    py = [sys.executable, "-X", "utf8"]

    errs = lint.lint(a.lang)
    if errs:
        print("\n".join(errs))
        sys.exit(f"release stopped: {len(errs)} lint errors")
    run(py + ["tools/check.py"], "tests")
    out = build.build(a.lang, os.path.join(ROOT, "build", f"gomoku_{a.lang}.sfc"))
    rom = open(out, "rb").read()
    bad = leftover_japanese(rom, a.lang)
    if bad:
        print("\n".join(bad))
        sys.exit("release stopped: Japanese left in translated entries")
    if not a.no_smoke:
        run(py + [os.path.join(SK, "emu.py"), out, "--out", "work/qa/release_smoke", "--route",
                  "tools/routes/boot.txt", "--smoke"], "smoke boot")

    rel = os.path.join(ROOT, "release", a.lang)
    os.makedirs(rel, exist_ok=True)
    final = os.path.join(rel, f"gomoku_{a.lang}.sfc")
    shutil.copy(out, final)
    run(py + [os.path.join(SK, "bps.py"), "snes-checksum", final], "header checksum")
    name = f"Super_Gomoku_Narabe_Renju_{a.lang.upper()}_v{a.version}"
    patch = os.path.join(rel, name + ".bps")
    run(py + [os.path.join(SK, "bps.py"), "make", ORIG, final, patch], "BPS make + re-apply check")

    o, f = open(ORIG, "rb").read(), open(final, "rb").read()
    readme = open(os.path.join(ROOT, "docs", f"README_{a.lang}.txt"), encoding="utf-8").read()
    readme = readme.format(version=a.version, orig_crc="%08X" % zlib.crc32(o), orig_md5=hashlib.md5(o).hexdigest(),
                           orig_sha1=hashlib.sha1(o).hexdigest(), patched_crc="%08X" % zlib.crc32(f),
                           patched_sha1=hashlib.sha1(f).hexdigest())
    rpath = os.path.join(rel, "README.txt")
    open(rpath, "w", encoding="utf-8", newline="\r\n").write(readme)
    zpath = os.path.join(rel, name + ".zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(patch, os.path.basename(patch))
        z.write(rpath, "README.txt")
    print("release:", zpath)


if __name__ == "__main__":
    main()
