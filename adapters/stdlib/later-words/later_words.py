"""later_words.py: a box made again with a words list it lacked, its record carried over as it was. Python 3.9+.

    python adapters/stdlib/later-words/later_words.py --box DIR --words FILE --to NEWDIR

A box takes its words list only when the kernel makes it: `init --words`
writes the list's place into kernel.json, and nothing afterwards changes it.
A box made without one stays without. So this makes the box again, at NEWDIR,
over the same files with the same key, and the list at FILE (kept like your
key: outside the box, readable only by you).

The record is not rewritten: its rows are laid down again, in order, through
the kernel's own `append`, each with the very fields it had, so the chain
comes out byte for byte the one you had, and every seal and decline in it
still proves under your key. The proposals and the answers written under the
box are copied as they are. Before it says it is done it checks that the new
record is the old one's bytes and that the kernel's own `verify` holds. DIR is
never touched: carry on in NEWDIR when you are satisfied, and keep DIR until
then. From the next bite on, each row says which list it read (its SHA-256).

It never reads or makes your key: a key that isn't where the box says it is
refuses the run, rather than `init` making a new one. A box that has a words
list already, or whose record doesn't verify, is refused.

Exit codes, the kernel's: 0 made again; 2 refused, or a bad command line.
"""

from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: later_words.py --box DIR --words FILE --to NEWDIR"
#: what the kernel's append makes itself, so a replayed row doesn't pass it on
OWN = ("n", "kind", "who", "ts", "where", "prev", "hash")
CARRIED = ("proposals", "written")


def quiet(fn, *args) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = fn(*args)
    return code, out.getvalue().strip()


def inside(path: Path, folder: Path) -> bool:
    return path == folder or folder in path.parents


def in_a_box(path: Path) -> bool:
    return any((p / "kernel.json").exists() for p in (path, *path.parents))


def refusal(old: Path, words: Path, new: Path) -> str | None:
    """Why this box can't be made again, or None. Nothing is written yet."""
    if not (old / "kernel.json").is_file():
        return f"{old} is not a kernel box"
    cfg = kernel.config(old)
    if "words" in cfg:
        return "this box has a words list already; this adds one it lacks"
    if set(cfg) != {"pile", "key"}:
        return "its kernel.json holds more than a pile and a key; made again, it would lose it"  # fmt: skip
    if not Path(cfg["key"]).is_file():
        return f"your key is not where the box says ({cfg['key']}); this never makes or reads one"  # fmt: skip
    if not Path(cfg["pile"]).is_dir():
        return f"the box's files, {cfg['pile']}, are not a folder"
    code, said = quiet(kernel.verify, old)
    if code != kernel.ALIVE:
        return f"the box doesn't verify; mend that first. It said: {said}"
    rows = kernel.read(old / "record.jsonl")[0]
    boot = {
        "n": 0, "kind": "boot", "who": "kernel", "family": "kernel",
        "standing": "unattested", "version": kernel.VERSION,
        "ts": rows[0]["ts"] if rows else "",
        "where": None, "loop": "open", "pile_sha256": kernel.h256(cfg["pile"]),
        "prev": kernel.GENESIS,
    }  # fmt: skip
    boot["hash"] = kernel.h256(kernel.canon(boot))
    if not rows or rows[0] != boot:
        return "the record began under another kernel or another pile; its first row can't be made again as it was"  # fmt: skip
    if inside(words, old) or inside(words, new):
        return "the words list can't live inside a box"
    if inside(new, old) or inside(old, new):
        return "the new box can't be inside the old, nor the old inside it"
    if in_a_box(new):
        return f"{new} is inside a box"
    if not new.parent.is_dir():
        return f"{new.parent} is not a folder: make it first"
    if new.exists() and (not new.is_dir() or any(new.iterdir())):
        return f"{new} is there already, and not empty"
    return kernel.read_words(words, new)[2]


def carry(old: Path, new: Path) -> None:
    """The proposals and answers, byte for byte, before the box is a box."""
    for name in CARRIED:
        for p in sorted((old / name).rglob("*")) if (old / name).is_dir() else []:
            if p.is_file():
                to = new / name / p.relative_to(old / name)
                to.parent.mkdir(parents=True, exist_ok=True)
                to.write_bytes(p.read_bytes())


def again(old: Path, words: Path, new: Path) -> tuple[int, str]:
    """(exit code, what to tell the person)."""
    old, words, new = old.resolve(), words.expanduser().resolve(), new.resolve()
    if (why := refusal(old, words, new)) is not None:
        return kernel.REFUSED, f"refused: {why}"
    cfg, rows = kernel.config(old), kernel.read(old / "record.jsonl")[0]
    new.mkdir(exist_ok=True)
    carry(old, new)
    code, said = quiet(kernel.init, new, Path(cfg["pile"]), Path(cfg["key"]), rows[0]["ts"], words)  # fmt: skip
    if code != kernel.ALIVE:
        return code, f"refused: {said}"
    for r in rows[1:]:
        fields = {k: v for k, v in r.items() if k not in OWN}
        kernel.append(new, r["ts"], r["kind"], r["who"], where=r["where"], **fields)
    if (new / "record.jsonl").read_bytes() != (old / "record.jsonl").read_bytes():
        return kernel.REFUSED, f"refused: the record made again differs from the old; do not use {new}"  # fmt: skip
    code, said = quiet(kernel.verify, new)
    if code != kernel.ALIVE:
        return kernel.REFUSED, f"refused: {new} doesn't verify; do not use it. It said: {said}"  # fmt: skip
    return kernel.ALIVE, (
        f"made again: {new}\n"
        f"its record is the old one's, {len(rows)} rows byte for byte; {said}\n"
        f"its words list: {words}; the box reads it from the next bite on\n"
        f"{old} is untouched: carry on in {new}, and keep the old until you are satisfied\n"
    )  # fmt: skip


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--words", "--to"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if args or not all(opts.get(k) for k in ("--box", "--words", "--to")):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    code, said = again(Path(opts["--box"]), Path(opts["--words"]), Path(opts["--to"]))
    print(said.rstrip("\n"), file=sys.stderr if code == kernel.REFUSED else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
