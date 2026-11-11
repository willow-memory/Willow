#!/bin/bash
# Rebuild the box over this repository and run the stack. Usage: rebuild.sh SCRATCH
# A fresh box each time, so the record holds only this run; SCRATCH/kept is
# left alone, since what the stack keeps between runs is the point of it.
# The key is a scratch key init makes; nothing is ever sealed with it.
# Writes nothing into the repository but Python's own __pycache__, removed after.
set -u
[ $# -eq 1 ] || { echo "usage: rebuild.sh SCRATCH (a folder outside the repository)"; exit 2; }
HERE=$(cd "$(dirname "$0")" && pwd)
R=$(cd "$HERE/../.." && pwd)
mkdir -p "$1" && S=$(cd "$1" && pwd) || exit 2
case "$S/" in "$R"/*) echo "refused: SCRATCH is inside the repository"; exit 2;; esac
rm -rf "$S/box" "$S"/box-* "$S/run" "$S/out" "$S/scratch.key"
mkdir -p "$S/run" "$S/kept" "$S/out/sim-a" "$S/out/sim-b" "$S/out/usb" "$S/out/away"
sed -e "s#<scratch>#$S#g" -e "s#<repo>#$R#g" "$HERE/stack.md" > "$S/stack.md"
cp "$HERE/questions.txt" "$S/questions.txt"
cp "$HERE/words.txt" "$S/words.txt" && chmod 600 "$S/words.txt"
cd "$R" || exit 2
python3 kernel.py init --box "$S/box" --pile "$R" --key "$S/scratch.key" --words "$S/words.txt" >/dev/null || exit 2
start=$(date +%s)
python3 adapters/stdlib/stack/stack.py --box "$S/box" --stack "$S/stack.md" --to "$S/run" > "$S/page.md" 2> "$S/page.err"
code=$?
python3 kernel.py verify --box "$S/box"
find "$R" -name __pycache__ -type d -not -path "*/.git/*" -exec rm -rf {} + 2>/dev/null
echo "stack: exit $code, $(( $(date +%s) - start )) s; $(tail -1 "$S/run/00-stack.txt")"
echo "page: $S/page.md  each step: $S/run/"
exit $code
