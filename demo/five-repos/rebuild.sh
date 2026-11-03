#!/bin/bash
# Rebuild the five-repo box and run a stack over it. Usage: rebuild.sh [STACK.md]
# A fresh box each time, so the record holds only this run; the key is the
# session's scratch key, never a real one. Writes nothing into any repo.
set -u
S=<scratch>
STACK=${1:-$S/five-repos.md}
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
rm -rf "$S/five-box"
cd /home/user/Willow || exit 2
WORDS=""; [ -f "$S/five-words.txt" ] && WORDS="--words $S/five-words.txt"
python3 kernel.py init --box "$S/five-box" --pile /home/user --key "$S/five.key" $WORDS >/dev/null || exit 2
python3 adapters/stdlib/stack/stack.py --box "$S/five-box" --stack "$STACK" \
    > "$S/five-stack.out" 2> "$S/five-stack.err"
code=$?
cp "$S/five-stack.out" "$S/runs-$STAMP.out"
python3 kernel.py verify --box "$S/five-box"
find /home/user/Willow -name __pycache__ -type d -not -path "*/.git/*" -exec rm -rf {} + 2>/dev/null
echo "stack $(basename "$STACK"): exit $code, $(wc -l < "$S/five-stack.out") lines, $(tail -1 "$S/five-stack.out")"
echo "page: $S/five-stack.out  (copy: $S/runs-$STAMP.out)"
exit $code
