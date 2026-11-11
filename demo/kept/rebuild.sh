#!/bin/bash
# Rebuild the box and run the stack. Usage: rebuild.sh SCRATCH [COMMIT]
#
# The pile is not this checkout. It is the repository as it was at one
# commit, cloned into SCRATCH/pile: the last commit before this folder
# existed, unless you name another. A stack kept inside the folder it asks
# finds its own questions and its own report, so the pile is pinned to
# before there was either. Name a later COMMIT and it will find itself again.
#
# A fresh box each time, so the record holds only this run; SCRATCH/kept is
# left alone, since what the stack keeps between runs is the point of it.
# The key is a scratch key init makes; nothing is ever sealed with it.
# Writes nothing into the repository but Python's own __pycache__, removed after.
set -u
PINNED=82983e876c5cb9943142050dcc0815201c0c671e
[ $# -eq 1 ] || [ $# -eq 2 ] || { echo "usage: rebuild.sh SCRATCH [COMMIT] (SCRATCH a folder outside the repository)"; exit 2; }
HERE=$(cd "$(dirname "$0")" && pwd)
R=$(cd "$HERE/../.." && pwd)
mkdir -p "$1" && S=$(cd "$1" && pwd) || exit 2
case "$S/" in "$R"/*) echo "refused: SCRATCH is inside the repository"; exit 2;; esac
AT=${2:-$PINNED}
git -C "$R" cat-file -e "$AT^{commit}" 2>/dev/null || { echo "refused: this checkout does not hold commit $AT; fetch it first"; exit 2; }
rm -rf "$S/box" "$S"/box-* "$S/run" "$S/out" "$S/pile" "$S/scratch.key"
mkdir -p "$S/run" "$S/kept" "$S/out/sim-a" "$S/out/sim-b" "$S/out/usb" "$S/out/away"
git clone -q --no-hardlinks "$R" "$S/pile" && git -C "$S/pile" checkout -q --detach "$AT" || exit 2
sed -e "s#<scratch>#$S#g" -e "s#<pile>#$S/pile#g" -e "s#<repo>#$R#g" "$HERE/stack.md" > "$S/stack.md"
cp "$HERE/questions.txt" "$S/questions.txt"
cp "$HERE/words.txt" "$S/words.txt" && chmod 600 "$S/words.txt"
cd "$R" || exit 2
python3 kernel.py init --box "$S/box" --pile "$S/pile" --key "$S/scratch.key" --words "$S/words.txt" >/dev/null || exit 2
start=$(date +%s)
python3 adapters/stdlib/stack/stack.py --box "$S/box" --stack "$S/stack.md" --to "$S/run" > "$S/page.md" 2> "$S/page.err"
code=$?
python3 kernel.py verify --box "$S/box"
find "$R" -name __pycache__ -type d -not -path "*/.git/*" -exec rm -rf {} + 2>/dev/null
echo "pile: the repository at $(git -C "$S/pile" rev-parse --short HEAD), $(git -C "$S/pile" rev-list --count HEAD) commits"
echo "stack: exit $code, $(( $(date +%s) - start )) s; $(tail -1 "$S/run/00-stack.txt")"
echo "page: $S/page.md  each step: $S/run/"
exit $code
