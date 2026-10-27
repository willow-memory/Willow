"""ids.py: each file and passage by the names the rest of the world uses.

    python adapters/stdlib/ids/ids.py --box DIR [PATH]

Every file of your folder, named as Software Heritage names it and as IPFS
does, so what you hold can be cited, looked up in the world's archives, or
matched against anyone else's copy without sending a byte:

    notes/garden.md
      swh:1:cnt:ce013625030ba8dba906f756967f9e9ca394464a
      bafkreicysg23kiwv34eg2d7qweipxwosdo2py4ldv42nbauguluen5v6am
    2 files named

PATH narrows it to that one file and adds its passages, each by its first
line, so a single paragraph can be cited on its own:

    notes/garden.md:12
      swh:1:cnt:...

**The names are computed, not looked up.** The Software Heritage ID is
`swh:1:cnt:` and the file's git blob SHA-1, exactly as `git hash-object`
writes it, so it matches the archive's whether or not your file is there.
The IPFS name is a CIDv1, raw codec, SHA-256, base32 — what `ipfs add
--raw-leaves --cid-version=1` gives a file of one chunk — so it is computed
only for a file within one chunk (256 KiB); a bigger file's CID depends on
the chunker's choices, and a name that depends on a choice is said, not
guessed: the row says `too big for a one-chunk CID`. A passage is named by
its own text's bytes.

Nothing goes online: the names are for the world, made at home. Hidden
files and folders are never read. It only reads. Exit codes, the kernel's:
0 files named; 42 nothing in the folder, or PATH isn't a file of it; 2
refused.
"""

from __future__ import annotations

import base64
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

CHUNK = 256 * 1024  # IPFS's one-chunk ceiling: above it, the chunker chooses


def swhid(data: bytes) -> str:
    """The bytes' Software Heritage content ID: their git blob SHA-1, as
    `git hash-object` writes it."""
    h = hashlib.sha1(b"blob %d\0" % len(data) + data)
    return f"swh:1:cnt:{h.hexdigest()}"


def cid(data: bytes) -> str | None:
    """The bytes' IPFS CIDv1 (raw codec, SHA-256, base32), or None past one
    chunk, where the name depends on the chunker and is not guessed."""
    if len(data) > CHUNK:
        return None
    body = bytes([1, 0x55, 0x12, 0x20]) + hashlib.sha256(data).digest()
    return "b" + base64.b32encode(body).decode().lower().rstrip("=")


def files_of(pile: Path) -> list[Path]:
    return sorted(
        p
        for p in pile.rglob("*")
        if p.is_file()
        and not any(part.startswith(".") for part in p.relative_to(pile).parts)
    )


def named(data: bytes) -> list[str]:
    got = cid(data)
    return [f"  {swhid(data)}", f"  {got}" if got else "  too big for a one-chunk CID"]


def show_all(pile: Path) -> list[str]:
    out = []
    files = files_of(pile)
    for p in files:
        out.append(p.relative_to(pile).as_posix())
        out += named(p.read_bytes())
    out.append(f"{len(files)} file{'s' if len(files) != 1 else ''} named")
    return out


def show_one(pile: Path, rel: str) -> list[str] | None:
    p = pile / rel
    if p not in files_of(pile):
        return None
    out = [rel, *named(p.read_bytes())]
    for c in kernel.chunks(pile):
        if c["path"] == rel:
            out.append(f"{rel}:{c['line']}")
            out += named(c["text"].encode("utf-8"))
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or len(args) > 1 or any(a.startswith("-") for a in args):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    pile = Path(kernel.config(box)["pile"])
    if args:
        lines = show_one(pile, args[0])
        if lines is None:
            print(f"{args[0]} isn't a file of your folder.")
            return kernel.ESCALATE
    else:
        lines = show_all(pile)
        if not files_of(pile):
            print("Nothing in your folder to name.")
            return kernel.ESCALATE
    for line in lines:
        print(line)
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
