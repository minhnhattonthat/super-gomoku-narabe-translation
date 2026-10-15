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
    # nothing outside the hook sites, the header size byte and the new banks changed
    allowed = [(0x7FD7, 0x7FD8), (0x20BA, 0x20C0), (0xA35A, 0xA35E), (0xA3B5, 0xA3B9), (0xA4CC, 0xA4D1),
               (0xA4E2, 0xA4E7), (0xA5D9, 0xA5DB), (0xA756, 0xA75F), (0xA779, 0xA782), (0xA7A9, 0xA7AC),
               (0xA7B3, 0xA7B8), (0xA7C4, 0xA7CD), (0xA7F6, 0xA7F9), (0xA86D, 0xA873)]
    for i in range(len(orig)):
        if rom[i] != orig[i]:
            assert any(a <= i < b for a, b in allowed), "unexpected change at %05X" % i
