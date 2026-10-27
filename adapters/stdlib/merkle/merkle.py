"""merkle.py: one row of the record proven with a handful of hashes.

    python adapters/stdlib/merkle/merkle.py root  --box DIR
    python adapters/stdlib/merkle/merkle.py prove --box DIR --row N --to FILE
    python adapters/stdlib/merkle/merkle.py check --proof FILE [--root HEX]

The record's chain proves the whole file: to check one row you read every
row. A Merkle tree over the same lines proves any one row with about
log-many hashes, so a row can be shown to someone who holds only the root —
a friend, a lawyer, a future you — without sending the record.

- `root` prints the tree's root over the record as it stands, and how many
  rows it covers. Keep it where you keep your tip pin: a root kept outside
  the box is what a proof is checked against.
- `prove` writes FILE: the row's own line, its place, the root, and the
  sibling hashes up to it. The proof is self-contained and about
  log2(N) hashes long — 8 hashes prove a row of a 177-row record.
- `check` reads FILE and needs no box: it rehashes the line, folds the
  siblings, and says whether the proof holds together and what root it
  reaches. Alone that is self-consistency, so alone it exits 42: whether
  that root is your record's, only your own copy of the root can say. With
  `--root HEX` it answers: 0 the row stands under your root, 2 it does not.

**The tree, exactly.** A leaf is SHA-256 over a zero byte and the row's own
line (the record's canonical JSON, newline off); a node is SHA-256 over a
one byte and its two children, left then right, so a leaf can never pose as
a node; a level's odd last node rises unchanged. The same record gives the
same root anywhere, and a changed, added or dropped row changes it.

The chain stays the record's spine and [tip-pin](../tip-pin/) stays how the
tip is held; this adds only the short proof. Nothing here writes the record
or reads the key, and FILE is never inside your folder or the box, never
over a file that exists.

Exit codes, the kernel's: 0 the root printed, the proof written, or the row
stands; 42 a proof alone, with no root of yours to answer to; 2 refused, a
proof that does not hold together among the refusals.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

LEAF, NODE = b"\x00", b"\x01"


def leaf_of(line: str) -> str:
    return hashlib.sha256(LEAF + line.encode("utf-8")).hexdigest()


def node_of(left: str, right: str) -> str:
    return hashlib.sha256(NODE + bytes.fromhex(left) + bytes.fromhex(right)).hexdigest()


def lines_of(box: Path) -> list[str]:
    """The record's lines, each a row's canonical JSON, the chain checked on
    the way in: a proof over a broken record would prove the break."""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        raise Refused("; ".join(breaks))
    return [kernel.canon(r) for r in rows]


def root_of(leaves: list[str]) -> str:
    level = list(leaves)
    while len(level) > 1:
        nxt = [node_of(level[i], level[i + 1]) for i in range(0, len(level) - 1, 2)]
        if len(level) % 2:
            nxt.append(level[-1])  # the odd last node rises unchanged
        level = nxt
    return level[0]


def path_of(leaves: list[str], n: int) -> list[dict]:
    """Row n's siblings up to the root: [{side, hash}], side being where the
    sibling stands. An odd node that rises adds nothing to the path."""
    out, level, at = [], list(leaves), n
    while len(level) > 1:
        mate = at ^ 1
        if mate < len(level):
            side = "left" if mate < at else "right"
            out.append({"side": side, "hash": level[mate]})
        nxt = [node_of(level[i], level[i + 1]) for i in range(0, len(level) - 1, 2)]
        if len(level) % 2:
            nxt.append(
                level[-1]
            )  # the odd riser's place in the next level is at//2 too
        level, at = nxt, at // 2
    return out


def fold(leaf: str, path: list[dict]) -> str:
    got = leaf
    for step in path:
        if step["side"] == "left":
            got = node_of(step["hash"], got)
        else:
            got = node_of(got, step["hash"])
    return got


class Refused(Exception):
    pass


def do_root(box: Path) -> int:
    lines = lines_of(box)
    root = root_of([leaf_of(x) for x in lines])
    print(f"root {root} over {len(lines)} row{'s' if len(lines) != 1 else ''}")
    return kernel.ALIVE


def do_prove(box: Path, n: int, to: Path) -> int:
    lines = lines_of(box)
    if not 0 <= n < len(lines):
        raise Refused(f"the record has rows 0 to {len(lines) - 1}, not {n}")
    pile = Path(kernel.config(box)["pile"])
    for name, under in (("your folder", pile), ("the box", box)):
        if to.resolve().is_relative_to(under.resolve()):
            raise Refused(f"FILE is inside {name}")
    leaves = [leaf_of(x) for x in lines]
    page = {
        "row": n,
        "rows": len(lines),
        "line": lines[n],
        "path": path_of(leaves, n),
        "root": root_of(leaves),
    }
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as e:
        raise Refused(f"could not write {to}: {type(e).__name__}")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(page, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"row {n} of {len(lines)}: a proof of {len(page['path'])}"
          f" hash{'es' if len(page['path']) != 1 else ''} to {to}")  # fmt: skip
    return kernel.ALIVE


def do_check(proof: Path, root: str | None) -> int:
    try:
        page = json.loads(proof.read_text(encoding="utf-8"))
        n, line, path = page["row"], page["line"], page["path"]
        said_root, rows = page["root"], page["rows"]
        assert all(step["side"] in ("left", "right") for step in path)
    except (OSError, ValueError, KeyError, TypeError, AssertionError) as e:
        raise Refused(f"{proof} isn't a proof: {type(e).__name__}")
    got = fold(leaf_of(line), path)
    if got != said_root:
        raise Refused(
            "the proof doesn't hold together: its hashes don't reach its root"
        )
    if root is None:
        print(f"the proof holds together: row {n} of {rows} under root {got}.")
        print("Whether that root is your record's, only your own copy can say.")
        return kernel.ESCALATE
    if got != root.lower():
        raise Refused("the row does NOT stand under your root")
    print(f"row {n} of {rows} stands under your root.")
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    verb, rest = (argv[0], argv[1:]) if argv else ("", [])
    opts, args, it = {}, [], iter(rest)
    for a in it:
        if a in ("--box", "--row", "--to", "--proof", "--root"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    boxed = verb in ("root", "prove")
    bad = (
        args
        or (boxed and not opts.get("--box"))
        or (
            verb == "prove"
            and (not opts.get("--to") or not opts.get("--row", "").isdigit())
        )
        or (verb == "root" and (opts.get("--to") or opts.get("--row")))
        or (verb == "check" and (not opts.get("--proof") or opts.get("--box")))
        or verb not in ("root", "prove", "check")
    )
    if bad:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    try:
        if boxed:
            box = Path(opts["--box"])
            if not (box / "kernel.json").exists():
                raise Refused("not a kernel box; init first")
            if verb == "root":
                return do_root(box)
            return do_prove(box, int(opts["--row"]), Path(opts["--to"]))
        return do_check(Path(opts["--proof"]), opts.get("--root"))
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
