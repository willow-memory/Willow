"""changed.py: what's new, edited or gone in your folder since the last check. Python 3.9+.

    python adapters/stdlib/changed/changed.py --box DIR [--now TS]

Every file of your folder (not in a hidden folder; any kind, a PDF too) is
fingerprinted by the SHA-256 of its bytes, and the check goes on the record
as one `changed` row, through the kernel's own `append`:

    the first check   every file and its fingerprint
    each later one    only what's new, edited or deleted since

so what your folder held at any check can be rebuilt from the record alone,
and the record grows by what changed, not by the size of the folder. Like
every row, it keeps places and fingerprints, never what a file says.

    Since the last check (2026-10-20 09:12):
      new      letters/2026-10-22-bank.txt
      edited   care/log.txt
      deleted  old/insurance.txt

An approved answer that cites an edited or deleted file may no longer hold:
the stale add-on says exactly which.

Exit codes, the kernel's: 0 nothing changed, or the first check; 42 something
changed since the last; 2 refused (a record that doesn't verify).
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KIND = "changed"


def fingerprints(pile: Path) -> dict[str, str]:
    """{path: SHA-256} for every file not under a hidden folder."""
    out = {}
    for p in sorted(pile.rglob("*")):
        rel = p.relative_to(pile)
        if not p.is_file() or any(part.startswith(".") for part in rel.parts):
            continue
        h = hashlib.sha256()
        try:
            with p.open("rb") as f:
                for block in iter(lambda: f.read(1 << 20), b""):
                    h.update(block)
        except OSError:
            continue
        out[rel.as_posix()] = h.hexdigest()
    return out


def last_state(rows: list[dict]) -> tuple[dict[str, str] | None, str]:
    """The folder as the last check left it, replayed from every `changed`
    row, and when that was; (None, "") before the first check."""
    state, when = None, ""
    for r in rows:
        if r["kind"] != KIND:
            continue
        if r.get("first"):
            state = dict(r.get("files", {}))
        elif state is not None:
            state.update(r.get("new", {}))
            state.update(r.get("edited", {}))
            for gone in r.get("deleted", []):
                state.pop(gone, None)
        when = str(r.get("ts", ""))
    return state, when


def diff(before: dict[str, str], now: dict[str, str]) -> dict:
    return {
        "new": {p: h for p, h in now.items() if p not in before},
        "edited": {p: h for p, h in now.items() if p in before and before[p] != h},
        "deleted": sorted(p for p in before if p not in now),
    }


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or args:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print(
            "refused: the record doesn't verify:", *breaks, sep="\n  ", file=sys.stderr
        )
        return kernel.REFUSED
    ts = opts.get("--now") or kernel.now()
    now = fingerprints(Path(kernel.config(box)["pile"]))
    before, when = last_state(rows)
    if before is None:
        kernel.append(box, ts, KIND, who=KIND, first=True, files=now)
        print(f"First check: {len(now)} file{'s' if len(now) != 1 else ''} fingerprinted. "
              "The next check says what changed since.")  # fmt: skip
        return kernel.ALIVE
    d = diff(before, now)
    kernel.append(box, ts, KIND, who=KIND, **d)
    stamp = f"{when[:10]} {when[11:16]}".strip()
    if not any(d.values()):
        print(f"Nothing changed since the last check ({stamp}).")
        return kernel.ALIVE
    print(f"Since the last check ({stamp}):")
    for label, paths in (("new", sorted(d["new"])), ("edited", sorted(d["edited"])),
                         ("deleted", d["deleted"])):  # fmt: skip
        for p in paths:
            print(f"  {label:<8} {p}")
    if d["edited"] or d["deleted"]:
        print("\nAn approved answer citing an edited or deleted file may no longer hold: "
              "the stale add-on says which.")  # fmt: skip
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
