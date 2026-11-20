"""words_later.py: a box made again with a words list it lacked, its record
kept as it was. Python 3.9+.

    python adapters/stdlib/words-later/words_later.py make --box OLD --words LIST --to NEW
    python adapters/stdlib/words-later/words_later.py check --box DIR

A box takes its words list when it is made: `init --words`. A box made
without one has no way to be given one afterwards, and making it afresh
would start a new record and leave every answer sealed on the old one
behind.

`make` writes NEW, a box that reads the same pile and sources with the same
key as OLD, names LIST as its words list, and holds OLD's record byte for
byte. Nothing is added to the record and nothing in it is changed, so every
row hashes as it did and every seal still proves under the same key. OLD is
not touched: it is the person's to keep or put away, and the two lines that
put NEW in OLD's place are printed, never run.

From then on a question asked of NEW is read through LIST, and each ask's
row says so with the list's hash, as it would in any box made with one.
Nothing before that is rewritten: an answer sealed without a list was sealed
without one.

`check` says whether a box names a words list, and whether the kernel can
read it.

Refused, and nothing written: an OLD that isn't a box, whose record doesn't
verify, or that already names a list (it says which); a LIST the kernel
wouldn't take (not a words list, readable beyond its owner, inside either
box); a NEW that is there, or whose folder isn't.

Exit codes, the kernel's: `make` 0 made; `check` 0 it names a list the
kernel reads, 42 it names none; 2 refused.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


def refuse(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def settings(box: Path) -> dict | None:
    """A box's own settings, or None when the folder is not a box."""
    try:
        cfg = json.loads((box / "kernel.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return cfg if isinstance(cfg, dict) and (box / "record.jsonl").is_file() else None


def options(argv: list[str], names: tuple[str, ...]) -> dict | None:
    got, it = {}, iter(argv)
    for a in it:
        value = next(it, "")
        if a not in names or a in got or not value:
            return None
        got[a] = Path(value)
    return got if set(got) == set(names) else None


def check(box: Path) -> int:
    cfg = settings(box)
    if cfg is None:
        return refuse(f"{box} is not a box")
    if not cfg.get("words"):
        print(f"no words list: {box} was made without one")
        return kernel.ESCALATE
    alias, _sha, why = kernel.read_words(Path(cfg["words"]), box)
    if why:
        return refuse(f"{box} names {cfg['words']}, and {why}")
    print(f"words list: {box} reads {cfg['words']}, {len(alias)} words")
    return kernel.ALIVE


def make(old: Path, words: Path, new: Path) -> int:
    cfg = settings(old)
    if cfg is None:
        return refuse(f"{old} is not a box")
    if cfg.get("words"):
        return refuse(f"{old} already names a words list, {cfg['words']}")
    rows, breaks = kernel.read(old / "record.jsonl")
    if breaks:
        return refuse(f"{old}'s record doesn't verify: " + "; ".join(breaks))
    if new.exists():
        return refuse(f"{new} is already there")
    if not new.parent.is_dir():
        return refuse(f"--to {new}: its folder isn't there")
    for box in (old, new):
        alias, _sha, why = kernel.read_words(words, box)
        if why:
            return refuse(why)
    record = (old / "record.jsonl").read_bytes()
    # The record goes in first and the settings last: until the settings are
    # there the folder is not a box, so no half-made box is ever left behind.
    new.mkdir()
    (new / "record.jsonl").write_bytes(record)
    made = dict(cfg, words=str(words.resolve()))
    (new / "kernel.json").write_text(json.dumps(made, sort_keys=True) + "\n")
    again, breaks = kernel.read(new / "record.jsonl")
    if breaks or len(again) != len(rows):  # a copy that isn't the record it copied
        return refuse(
            f"{new}'s record did not come out as {old}'s: " + "; ".join(breaks)
        )
    print(f"made: {new}, with {old}'s record as it was ({len(rows)} rows), "
          f"reading {words} ({len(alias)} words)")  # fmt: skip
    print(f"{old} is as it was. To put the new box in its place, when you choose:")
    print(f"  mv {old} {old}.before-words")
    print(f"  mv {new} {old}")
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("make", "check"):
        return usage()
    if argv[0] == "check":
        got = options(argv[1:], ("--box",))
        return check(got["--box"]) if got else usage()
    got = options(argv[1:], ("--box", "--words", "--to"))
    return make(got["--box"], got["--words"], got["--to"]) if got else usage()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
