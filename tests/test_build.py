import os, sys, tempfile
import pytest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build  # noqa: E402

ORIG = os.path.join(ROOT, "rom", "orig.sfc")


@pytest.fixture(scope="module")
def tmp():
    with tempfile.TemporaryDirectory() as d:
        yield d


def test_identity_build(tmp):
    out = build.build("jp", os.path.join(tmp, "id.sfc"))
    assert open(out, "rb").read() == open(ORIG, "rb").read()


@pytest.mark.parametrize("marker", [False, True])
def test_en_build(tmp, marker):
    out = build.build("en", os.path.join(tmp, "en%d.sfc" % marker), marker)
    rom = open(out, "rb").read()
    orig = open(ORIG, "rb").read()
    assert len(rom) == build.SIZE
    # nothing changed outside the header size byte and 24 bytes after each hook `org` in the original banks
    import re
    orgs = [int(m, 16) for m in re.findall(r"^org \$([0-9A-F]{6})", open(os.path.join(ROOT, "asm", "main.asm")).read(), re.M)]
    allowed = [(0x7FD7, 0x7FD8)] + [(build.textblock.lorom(a), build.textblock.lorom(a) + 24) for a in orgs if a < 0x900000]
    for i in range(len(orig)):
        if rom[i] != orig[i]:
            assert any(a <= i < b for a, b in allowed), "unexpected change at %05X" % i
