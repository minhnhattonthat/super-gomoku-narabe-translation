"""Set TSV entries: python tsvset.py FILE.tsv CHANGES.tsv (CHANGES: id<TAB>text lines)."""
import sys
path, changes = sys.argv[1], sys.argv[2]
new = dict(l.rstrip("\n").split("\t", 1) for l in open(changes, encoding="utf-8") if "\t" in l)
out, seen = [], set()
for line in open(path, encoding="utf-8"):
    line = line.rstrip("\n")
    k = line.split("\t", 1)[0]
    if k in new:
        line = k + "\t" + new[k]
        seen.add(k)
    out.append(line)
missing = set(new) - seen
assert not missing, missing
open(path, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print("updated", len(seen))
