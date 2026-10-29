"""nicknames.py: the names you call people, as a words list. Python 3.9+.

    python adapters/stdlib/nicknames/nicknames.py --from FOLDER --to FILE [--both]
    python adapters/stdlib/nicknames/nicknames.py --box DIR --to FILE [--both]

Ask "when is Mum's appointment" of files that only ever say "Margaret" and
they hold nothing: a word matches as written. A words list teaches the kernel
that one word is another (see [starter-words](../starter-words/)), and this
writes one from what your own files say:

    # notes/family.txt:3 (2 mentions)
    mum = margaret

Where a family word (mum, mom, dad, gran, nana, grandad, auntie, uncle, sis,
bro, hubby and their kin; not father, mother, brother or sister, which are
often a title as in Father Liam) sits beside a capitalised name in one of these
shapes, the nickname is read as the name:

    Mum (Margaret)       Margaret (Mum)       Margaret, my mum
    Auntie Jean          my mum Margaret      my mum is Margaret

A day, a month and a word like "The" is no name. With --both the list also
reads the name as the nickname, so "Margaret" finds what is written "Mum".
Each line is shown above with the file and line of its first mention and how
many there were, so you can see why it is there. A nickname that two names
claim ("mum" for Margaret in one file and Mary in another) is kept with both
and said, since it may be two people or a slip; read it before you use it.

FILE is the kernel's words list: write it where your box's words list lives,
outside the box, readable only by you. It is written once, never over a file
that exists, and checks that the kernel reads it before it is kept. Files are
only read. Nothing here decides who a nickname *is*; it copies what you wrote.

Exit codes, the kernel's: 0 written; 42 no nickname found, nothing written;
2 refused (a bad command line, an existing FILE).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

KIN = (
    "mum mummy mom mommy mama mam dad daddy papa pop pops gran granny grannie grandma "
    "grandmother nan nana nanna grandpa granddad grandad grandfather auntie aunty aunt uncle sis bro "
    "hubby husband wife"
).split()
K = "(?P<kin>" + "|".join(sorted(KIN, key=len, reverse=True)) + ")"
N = r"(?P<name>[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]{2,})"
POSS = r"(?:[Mm]y|[Oo]ur)"
ANY = "|".join(sorted(KIN, key=len, reverse=True))
KIN_RX = r"(?:[Mm]y |[Oo]ur )?" + K.replace("(?P<kin>", "(?P<kin>(?i:") + ")"
CAP = (
    "(?P<kin>"
    + "|".join(sorted((k.capitalize() for k in KIN), key=len, reverse=True))
    + ")"
)
SHAPES = [
    re.compile(rf"\b{KIN_RX}\s*\(\s*{N}\s*\)"),  # Mum (Margaret)
    re.compile(rf"\b{N}\s*\(\s*{KIN_RX}\s*\)"),  # Margaret (Mum)
    re.compile(rf"\b{N},?\s+{POSS}\s+(?P<kin>(?i:{ANY}))\b"),  # Margaret, my mum
    re.compile(rf"\b{POSS}\s+(?P<kin>(?i:{ANY}))\s+(?:is\s+|was\s+)?{N}\b"),  # my mum Margaret
    re.compile(rf"\b{CAP}\s+(?:(?:is|was)\s+)?{N}\b"),  # Auntie Jean, Grandad was Albert
]  # fmt: skip
NOT_NAMES = set(
    "the this that these those and but then there their they when what where why how who which with without from into "
    "monday tuesday wednesday thursday friday saturday sunday mon tue tues wed weds thu thur thurs fri sat sun january february march april may june july august "
    "september october november december said says called asked told came went will would could should has have had was "
    "were been are not yes thanks please also again today tomorrow yesterday tonight morning evening night day week "
    "christmas easter birthday dinner lunch breakfast appointment".split()
)


def mentions(folder: Path):
    """((nickname, name), file, line) for each place a nickname sits beside a name."""
    for p in sorted(folder.rglob("*")):
        rel = p.relative_to(folder)
        if (
            not p.is_file()
            or any(part.startswith(".") for part in rel.parts)
            or p.stat().st_size > kernel.MAX_FILE
        ):
            continue
        try:
            raw = p.read_bytes()
            if b"\0" in raw[: kernel.SNIFF]:
                continue
            text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            seen = set()
            for rx in SHAPES:
                for m in rx.finditer(line):
                    nick, name = m.group("kin").lower(), m.group("name").lower()
                    if name in NOT_NAMES or name in KIN or (nick, name) in seen:
                        continue
                    seen.add((nick, name))
                    yield (nick, name), rel.as_posix(), n


def collect(folder: Path):
    """{(nickname, name): (file, line, count)}, first mention kept."""
    found: dict[tuple[str, str], list] = {}
    for key, file, line in mentions(folder):
        if key in found:
            found[key][2] += 1
        else:
            found[key] = [file, line, 1]
    return {k: tuple(v) for k, v in found.items()}


def render(found: dict, both: bool) -> tuple[str, list[str]]:
    """(the words list, the nicknames two names claim)."""
    lines = [
        "# written by nicknames.py from what these files say; read it before you use it",
        "",
    ]
    by_nick: dict[str, list[str]] = {}
    for (nick, name), _ in sorted(found.items()):
        by_nick.setdefault(nick, []).append(name)
    for nick, names in sorted(by_nick.items()):
        for name in names:
            file, line, count = found[(nick, name)]
            lines.append(
                f"# {file}:{line} ({count} mention{'s' if count != 1 else ''}) {nick} = {name}"
            )
        lines.append(f"{nick} = {', '.join(names)}")
    if both:
        by_name: dict[str, list[str]] = {}
        for (nick, name), _ in sorted(found.items()):
            by_name.setdefault(name, []).append(nick)
        lines.append("")
        lines.append(
            "# the other way: the name finds what is written with the nickname"
        )
        for name, nicks in sorted(by_name.items()):
            lines.append(f"{name} = {', '.join(nicks)}")
    return "\n".join(lines) + "\n", sorted(
        n for n, names in by_nick.items() if len(names) > 1
    )


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--from", "--box", "--to"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    both = "--both" in args
    args = [a for a in args if a != "--both"]
    if (
        args
        or not opts.get("--to")
        or bool(opts.get("--from")) == bool(opts.get("--box"))
    ):
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    if opts.get("--box"):
        box = Path(opts["--box"])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        folder = Path(kernel.config(box)["pile"])
    else:
        folder = Path(opts["--from"])
    if not folder.is_dir():
        print(f"refused: {folder} isn't a folder", file=sys.stderr)
        return kernel.REFUSED
    to = Path(opts["--to"])
    found = collect(folder)
    if not found:
        print("No nickname found beside a name, so no words list was written.")
        return kernel.ESCALATE
    text, claimed = render(found, both)
    listed, why = kernel.parse_words(text)
    if why is not None:
        print(f"refused: the list it made doesn't read: {why}", file=sys.stderr)
        return kernel.REFUSED
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as e:
        print(f"refused: could not write {to}: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    for (nick, name), (file, line, count) in sorted(found.items()):
        print(
            f"{nick} = {name}    {file}:{line}  ({count} mention{'s' if count != 1 else ''})"
        )
    for nick in claimed:
        print(
            f"note: {nick!r} is claimed by more than one name; it may be two people. Read it.",
            file=sys.stderr,
        )
    print(f"wrote {to}: {len(listed)} nickname{'s' if len(listed) != 1 else ''}")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
