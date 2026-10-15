"""Debug tool: reach any scene of Super Gomoku Narabe Renju from a cold boot, by name.

    python -X utf8 tools/debug/warp.py SCENE [--rom ROM] [--out DIR] [--then "8 a;60 -"] [--every 30]
    python -X utf8 tools/debug/warp.py --all [--rom ROM] [--jobs 3]
    python -X utf8 tools/debug/warp.py --list

Scenes live in tools/debug/scenes.txt. Each run writes DIR/sheet.png (shots of the scene's own steps),
DIR/final.png, DIR/log.txt, DIR/texts.txt (text ids drawn during the scene's own steps) and the savestate
work/states/<scene>.mss. Default DIR: work/warp/<scene>. --then appends route steps (exploration).
"""
import argparse
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, "tools", "debug")
EMU = os.path.join(ROOT, ".claude", "skills", "translate-retro-game", "scripts", "emu.py")


def parse(path):
    """scenes.txt -> {name: {"desc", "base", "steps"}}; steps are ("route", n, buttons) or (kind, addr, val)."""
    scenes, cur = {}, None
    lines = []
    for no, line in enumerate(open(path, encoding="utf8"), 1):
        if line.lstrip().startswith(("lua ", "desc:")):
            lines.append((no, line.strip()))
        else:  # "#" comments; ";" separates several steps on one line
            lines += [(no, p.strip()) for p in line.split("#", 1)[0].split(";")]
    for no, s in lines:
        if not s:
            continue
        m = re.fullmatch(r"\[(\w+)\]", s)
        if m:
            cur = scenes.setdefault(m.group(1), {"desc": "", "base": None, "steps": []})
            continue
        if cur is None:
            raise SystemExit(f"{path}:{no}: step outside a [scene]")
        key, _, rest = s.partition(" ")
        if s.startswith("desc:"):
            cur["desc"] = s[5:].strip()
        elif s.startswith("base:"):
            cur["base"] = s[5:].strip()
        elif key in ("poke", "hold"):
            for kv in rest.split():
                a, v = kv.split("=")
                cur["steps"].append((key, int(a, 16), int(v, 16)))
        elif key == "lua":
            cur["steps"].append(("lua", rest, None))
        elif re.fullmatch(r"\d+ \S+", s):
            cur["steps"].append(("route", int(key), rest))
        else:
            raise SystemExit(f"{path}:{no}: bad line: {s}")
    for n, sc in scenes.items():
        if sc["base"] and sc["base"] not in scenes:
            raise SystemExit(f"scene {n}: unknown base {sc['base']}")
    return scenes


def flatten(scenes, name):
    """-> (steps from cold boot, frame where the scene's own steps start)."""
    sc = scenes[name]
    base = flatten(scenes, sc["base"])[0] if sc["base"] else []
    return base + sc["steps"], sum(st[1] for st in base if st[0] == "route")


def lua_str(s):
    return "[==[" + s + "]==]"


def run(scenes, name, rom, out, then=None, every=30, quiet=False):
    steps, mark = flatten(scenes, name)
    if then:
        for part in then.split(";"):
            n, b = part.split()
            steps.append(("route", int(n), b))
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if re.fullmatch(r"f\d+\.png|sheet\.png|final\.png", f):
            os.remove(os.path.join(out, f))
    route, acts, frame = [], [], 0
    for kind, a, b in steps:
        at = max(frame, 1)  # the driver's frame counter starts at 1
        if kind == "route":
            route.append(f"{a} {b}")
            frame += a
        elif kind == "lua":
            acts.append(f"{{{at},'lua',{lua_str(a)}}}")
        else:
            acts.append(f"{{{at},'{kind}',0x{a:06X},0x{b:02X}}}")
    total = frame
    rpath = os.path.join(out, "route.txt")
    with open(rpath, "w", encoding="utf8") as f:
        f.write("\n".join(route) + "\n")
    tag = os.path.splitext(os.path.basename(rom))[0]
    # orig states at work/states/<scene>.mss; other ROMs in a subfolder so they never clobber each other
    state = os.path.join(ROOT, "work", "states", *([] if tag == "orig" else [tag]), name + ".mss")
    os.makedirs(os.path.dirname(state), exist_ok=True)
    shots = ",".join(str(x) for x in range(mark, total, every)) or str(total - 1)
    cmd = [sys.executable, "-X", "utf8", EMU, rom, "--out", out, "--route", rpath, "--shots", shots, "--sheet",
           "--script", os.path.join(HERE, "warp.lua"), "--var", "ACTS={" + ",".join(acts) + "}",
           "--var", f"MARK={mark}", "--state-out", state, "--timeout", str(120 + total // 60)]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf8", errors="replace")
    ids = []
    log = os.path.join(out, "log.txt")
    if os.path.exists(log):
        after = mark == 0
        for line in open(log, encoding="utf8"):
            if line.startswith("MARK"):
                after = True
            elif after and line.startswith("T "):
                ids.append(line.split()[2] + " " + line.split()[3] + " " + line.split()[1])
    with open(os.path.join(out, "texts.txt"), "w", encoding="utf8") as f:
        f.write("\n".join(ids) + "\n")
    status = "ok" if r.returncode == 0 else f"FAIL exit {r.returncode}: {r.stdout[-400:]}{r.stderr[-400:]}"
    if not quiet:
        print(f"{name}: {status} ({total} frames) -> {out}")
        print("  texts: " + " ".join(i.split()[0] for i in ids))
    return name, r.returncode, status


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scene", nargs="?")
    ap.add_argument("--rom", default=os.path.join(ROOT, "rom", "orig.sfc"))
    ap.add_argument("--out")
    ap.add_argument("--scenes", default=os.path.join(HERE, "scenes.txt"))
    ap.add_argument("--then", help='extra route steps, "8 a;60 -"')
    ap.add_argument("--every", type=int, default=30, help="shot every N frames during the scene's own steps")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--selftest", action="store_true", help="parse scenes.txt and check every scene flattens")
    a = ap.parse_args()
    scenes = parse(a.scenes)
    if a.selftest:
        for n in scenes:
            steps, mark = flatten(scenes, n)
            total = sum(s[1] for s in steps if s[0] == "route")
            assert total > mark or not scenes[n]["base"], f"{n}: no steps of its own"
            assert scenes[n]["desc"], f"{n}: no desc"
        print(f"selftest ok: {len(scenes)} scenes")
        return 0
    if a.list:
        for n, sc in scenes.items():
            print(f"{n:24} {sc['desc']}")
        return 0
    rom = os.path.abspath(a.rom)
    if a.all:
        tag = os.path.splitext(os.path.basename(rom))[0]
        base = a.out or os.path.join(ROOT, "work", "warp", tag)
        with ThreadPoolExecutor(a.jobs) as ex:
            res = list(ex.map(lambda n: run(scenes, n, rom, os.path.join(base, n), every=a.every, quiet=True),
                              scenes))
        bad = [r for r in res if r[1] != 0]
        for n, _, st in res:
            print(f"{n:24} {st}")
        print(f"{len(res) - len(bad)}/{len(res)} ok -> {base}")
        return 1 if bad else 0
    if a.scene not in scenes:
        raise SystemExit(f"unknown scene {a.scene!r}; --list shows them")
    out = a.out or os.path.join(ROOT, "work", "warp", a.scene)
    return 0 if run(scenes, a.scene, rom, out, a.then, a.every)[1] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
