"""Find a Japanese string (encoded with tbl/jp.tbl as 16-bit words) anywhere in the ROM.

    python -X utf8 tools/findtext.py ROM 監修 坂田 ...
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from codec import Codec

rom = open(sys.argv[1], "rb").read()
c = Codec(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tbl", "jp.tbl"))
for s in sys.argv[2:]:
    pat = c.encode(s)[:-2]
    hits, i = [], rom.find(pat)
    while i >= 0:
        hits.append("%05X" % i)
        i = rom.find(pat, i + 1)
    print(s, hits)
