"""make_it_so.py: an order held for you, never carried out. Python 3.9+.

    python adapters/stdlib/make-it-so/make_it_so.py plan --box DIR --to PLAN.json --cmd "COMMAND" [--limit N] [--now TS] "what the order rests on"
    python adapters/stdlib/make-it-so/make_it_so.py check --box DIR PLAN.json

`plan` asks the box the question, as the kernel does, and writes the order
beside the passages that bear on it: your words, the COMMAND exactly as you
gave it with its SHA-256, and for each passage its file, line, id and the
SHA-256 of the file as it is now. Then it prints the order and stops. The
command is not run, not parsed and not checked for anything: it is a string
this holds for you. Nothing is changed, opened or sent; the one file written
is PLAN.json.

`check` says whether the order still stands: the command still hashes to what
was written (an edited plan is refused), and each cited file still holds the
bytes it held, so a plan made on Monday is not run on Thursday's files by
accident. It prints `holds`, or a line for each file that changed or is gone.

PLAN.json is written once, readable only by you, never over a file that
exists, and never inside the box or its pile. Its folder must already exist.
The decision to run the command is yours; nothing here approves it, writes a
seal or reads your key.

Exit codes, the kernel's: 0 planned, or the plan holds; 42 no passage holds
the question (no order is written), or the plan no longer holds; 2 refused (a
bad command line, not a box, a plan that exists or won't read).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

USAGE = (
    'usage: make_it_so.py plan --box DIR --to PLAN.json --cmd "COMMAND" "question"'
    " | check --box DIR PLAN.json"
)
LIMIT = 5  # passages an order rests on unless said (1 to 20)
SHOWN = 80  # characters of a passage's first line printed


def h256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inside(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def refuse(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def parse(argv: list[str], flags: tuple[str, ...]) -> tuple[dict, list[str]] | None:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in flags:
            if a in opts:
                return None
            opts[a] = next(it, "")
        else:
            args.append(a)
    return opts, args


def pile_of(box: Path) -> Path | str:
    if not (box / "kernel.json").exists():
        return "not a kernel box; init first"
    return Path(kernel.config(box)["pile"]).resolve()


def plan(argv: list[str]) -> int:
    got = parse(argv, ("--box", "--to", "--cmd", "--limit", "--now"))
    if got is None:
        return refuse(USAGE)
    opts, args = got
    limit = opts.get("--limit", str(LIMIT))
    if (
        not opts.get("--box")
        or not opts.get("--to")
        or not opts.get("--cmd", "").strip()
        or len(args) != 1
        or not args[0].strip()
        or args[0].startswith("--")
        or not limit.isdigit()
        or not 1 <= int(limit) <= 20
        or "\0" in opts["--cmd"]
    ):
        return refuse(USAGE)
    box = Path(opts["--box"])
    pile = pile_of(box)
    if isinstance(pile, str):
        return refuse(pile)
    to = Path(opts["--to"]).resolve()
    if inside(to, box.resolve()) or inside(to, pile):
        return refuse("PLAN must not be inside the box or its pile")
    if not to.parent.is_dir():
        return refuse(f"no such folder: {to.parent}")
    if to.exists():
        return refuse(f"{opts['--to']} exists; it is never written over")
    cfg = kernel.config(box)
    alias: dict = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            return refuse(why)
    found = kernel.rank(kernel.chunks(pile), args[0].strip(), alias or {})[: int(limit)]
    if not found:
        print("no passage holds that; no order was written")
        return kernel.ESCALATE
    cited = [
        {
            "path": p["path"],
            "line": p["line"],
            "id": p["id"],
            "file_sha256": h256((pile / p["path"]).read_bytes()),
        }
        for p in found
    ]
    order = {
        "made": opts.get("--now") or kernel.now(),
        "order": args[0].strip(),
        "command": opts["--cmd"],
        "command_sha256": h256(opts["--cmd"].encode()),
        "passages": cited,
    }
    body = json.dumps(order, indent=1, ensure_ascii=False) + "\n"
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as e:
        return refuse(f"{opts['--to']}: {e.strerror}")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"order: {order['order']}")
    print(f"command (not run): {order['command']}")
    for p, c in zip(found, cited):
        first = next((x for x in p["text"].splitlines() if x.strip()), "")
        print(f"  {c['path']}:{c['line']}  {' '.join(first.split())[:SHOWN]}")
    print(f"wrote {opts['--to']}; nothing was run. The command is yours to run.")
    return kernel.ALIVE


def check(argv: list[str]) -> int:
    got = parse(argv, ("--box",))
    if got is None:
        return refuse(USAGE)
    opts, args = got
    if not opts.get("--box") or len(args) != 1 or args[0].startswith("--"):
        return refuse(USAGE)
    pile = pile_of(Path(opts["--box"]))
    if isinstance(pile, str):
        return refuse(pile)
    try:
        order = json.loads(Path(args[0]).read_text(encoding="utf-8"))
        command, passages = order["command"], order["passages"]
        if (
            h256(command.encode()) != order["command_sha256"]
            or not isinstance(passages, list)
            or not passages
        ):
            raise ValueError
        paths = {p["path"]: p["file_sha256"] for p in passages}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return refuse(f"{args[0]} is not a plan this wrote, or has been edited")
    stale = 0
    for rel, sha in sorted(paths.items()):
        path = (pile / rel).resolve()
        if not inside(path, pile):
            return refuse(f"{rel} points outside the pile")
        try:
            now = h256(path.read_bytes())
        except OSError:
            print(f"gone: {rel}")
            stale += 1
            continue
        if now != sha:
            print(f"changed: {rel}")
            stale += 1
    if stale:
        print(f"the plan no longer holds: {stale} of {len(paths)} files differ")
        return kernel.ESCALATE
    print("holds")
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    if argv[:1] == ["plan"]:
        return plan(argv[1:])
    if argv[:1] == ["check"]:
        return check(argv[1:])
    return refuse(USAGE)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
