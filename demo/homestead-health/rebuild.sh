#!/bin/bash
# Build the box and ask it the questions. Usage: rebuild.sh SCRATCH [SOURCES]
#
# The pile is the six repositories sources.json names, each at its commit,
# and nothing else. They are cloned into SCRATCH/sources, or taken from
# SOURCES when that folder already holds a clone of each under its name.
# A fresh box each time, on a scratch key init makes; nothing is sealed.
# Writes SCRATCH and nothing in this repository.
set -u
[ $# -eq 1 ] || [ $# -eq 2 ] || { echo "usage: rebuild.sh SCRATCH [SOURCES] (SCRATCH a folder outside the repository)"; exit 2; }
HERE=$(cd "$(dirname "$0")" && pwd)
R=$(cd "$HERE/../.." && pwd)
mkdir -p "$1" && S=$(cd "$1" && pwd) || exit 2
case "$S/" in "$R"/*) echo "refused: SCRATCH is inside the repository"; exit 2;; esac
FROM=${2:-$S/sources}
rm -rf "$S/box" "$S/pile" "$S/scratch.key"
mkdir -p "$S/pile" "$FROM"
python3 - "$HERE/sources.json" <<'PY' > "$S/sources.tsv" || exit 2
import json, sys
for s in json.load(open(sys.argv[1]))["sources"]:
    print(s["name"], s["address"], s["commit"], s["as"], sep="\t")
PY
while IFS=$'\t' read -r name address commit as; do
  [ -d "$FROM/$name/.git" ] || git clone -q "$address" "$FROM/$name" || exit 2
  git -C "$FROM/$name" cat-file -e "$commit^{commit}" 2>/dev/null || git -C "$FROM/$name" fetch -q origin "$commit" || { echo "refused: $name does not hold commit $commit"; exit 2; }
  mkdir -p "$S/pile/$as" && git -C "$FROM/$name" archive "$commit" | tar -x -C "$S/pile/$as" || exit 2
  echo "pile: $name at ${commit:0:7}, $(git -C "$FROM/$name" ls-tree -r --name-only "$commit" | wc -l | tr -d ' ') files"
done < "$S/sources.tsv"
cd "$R" || exit 2
python3 kernel.py init --box "$S/box" --pile "$S/pile" --key "$S/scratch.key" >/dev/null || exit 2
while IFS= read -r q; do
  [ -n "$q" ] || continue
  python3 kernel.py bite --box "$S/box" "$q" | python3 -c '
import json, sys
d = json.load(sys.stdin)
first = (d.get("served") or [{}])[0].get("where", "")
print(sys.argv[1], d["state"], first, sep="  |  ")' "$q"
done < "$HERE/questions.txt" > "$S/asks.txt"
cat "$S/asks.txt"
python3 kernel.py verify --box "$S/box"
find "$R" -name __pycache__ -type d -not -path "*/.git/*" -exec rm -rf {} + 2>/dev/null
echo "box: $S/box  pile: $S/pile"
