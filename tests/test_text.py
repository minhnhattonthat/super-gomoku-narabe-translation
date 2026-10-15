import os, sys
import pytest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "tools"))
from codec import Codec  # noqa: E402
import codec8, textblock  # noqa: E402

ROM = os.path.join(ROOT, "rom", "orig.sfc")


@pytest.fixture(scope="module")
def rom():
    if not os.path.exists(ROM):
        pytest.fail("rom/orig.sfc missing (copy the Japanese ROM there)")
    return open(ROM, "rb").read()


def test_block_roundtrip_and_coverage(rom):
    c = Codec(os.path.join(ROOT, "tbl", "jp.tbl"))
    strs = textblock.groups(rom)
    by_group = [[] for _ in range(textblock.NGROUPS)]
    for g, i, off, n in strs:
        text, used = c.decode(rom, off)
        assert used == n
        assert c.encode(text) == rom[off:off + n], (g, i, text)
        assert "[" not in text, (g, i, text)  # every word decodes to a glyph or a known control
        by_group[g].append(rom[off:off + n])
    # identity: repacking the decoded block at its own address gives the original bytes, table included
    blob = textblock.pack(by_group, 0x838237)
    assert blob == rom[textblock.TABLE:textblock.END]


def test_codec8_roundtrip(rom):
    off = 0x18032
    while off < 0x18237:
        text, n = codec8.decode(rom, off)
        assert codec8.encode(text) == rom[off:off + n]
        off += n
