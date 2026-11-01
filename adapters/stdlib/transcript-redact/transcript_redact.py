"""transcript_redact.py: a transcript fit to share, each removal listed.

    python adapters/stdlib/transcript-redact/transcript_redact.py --from FILE --to FILE

An agent transcript is full of your machine: API keys in tool output, your
home path in every file name, your email in a config dump. This writes a
copy with those taken out and lists each removal by line, so you can read
what left before the transcript does:

    line 12   a key        [redacted:key]        sk-…w8Qa
    line 40   a home path  /home/[redacted]      /home/…drew
    line 57   an email     [redacted:email]      …e@example.org
    wrote FILE: 3 removals on 3 lines

**What is taken out, exactly.**

- **keys**: the shapes keys wear — sk- and similar prefixed tokens, GitHub's
  ghp_ and github_pat_ families, AWS's AKIA ids, Slack's xox tokens,
  Google's AIza, a JWT's three dotted base64 blocks, and every key shape the
  privacy add-on knows (its own shapes still work if it was deleted) — each
  replaced with `[redacted:key]`; a private key block goes whole, on one line
  with its breaks written `\\n` or over many, BEGIN to END;
- **home paths**: the account name in /home/NAME, /Users/NAME and
  C:\\Users\\NAME becomes [redacted], the rest of the path kept, so the
  transcript still reads;
- **emails**: name@host becomes `[redacted:email]`.

Each removal is listed with its line and a stub — the last few characters
of a key, the first letter of an email — enough to recognise, nothing worth
keeping. The copy is written even when nothing is removed ("0 removals"),
so the file you share is always the one this wrote, and running it twice
gives the same bytes. A transcript that is JSON stays JSON: nothing
replaced holds a quote or a backslash.

What it cannot see is said: a password in prose, a name, a secret with no
shape. [secrets-audit](../secrets-audit/) hunts those across the folder;
this cleans one file you're about to share.

FILE is written once, readable only by you, never over a file that exists.
Exit codes, the kernel's: 0 written; 2 refused.
"""

from __future__ import annotations

import os
import re
import sys
import types
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402


def privacy_keys() -> list[re.Pattern]:
    """The privacy add-on's key shapes, from its source; none if it was deleted."""
    path = STDLIB / "privacy" / "privacy.py"
    if not path.is_file():
        return []
    mod = types.ModuleType("redact_privacy")
    mod.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
    return list(mod.KEYS)


_PEM = r"(?:RSA |EC |OPENSSH |DSA |PGP |ENCRYPTED )?PRIVATE KEY(?: BLOCK)?"
#: a private key block on one line, its line breaks real or written `\n` (as a
#: JSON transcript holds one), never past a quote, so JSON stays JSON
PEM = re.compile(
    rf"-----BEGIN {_PEM}-----(?:\\[nr]|[A-Za-z0-9+/=:,. \t]|-(?!----))*(?:-----END {_PEM}-----)?"
)
PEM_BEGIN = re.compile(rf"-----BEGIN {_PEM}-----")
PEM_END = re.compile(rf"-----END {_PEM}-----")
KEY = re.compile(
    r"\b(?:sk|pk|rk)-[A-Za-z0-9_-]{16,}"
    r"|\bgh[pousr]_[A-Za-z0-9]{16,}"
    r"|\bgithub_pat_[A-Za-z0-9_]{20,}"
    r"|\bAKIA[0-9A-Z]{16}\b"
    r"|\bxox[baprs]-[A-Za-z0-9-]{10,}"
    r"|\bAIza[A-Za-z0-9_-]{30,}"
    r"|\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{6,}\b"
)
HOME = re.compile(
    r"(?P<base>/home/|/Users/|C:\\{1,2}Users\\{1,2})(?P<name>[A-Za-z0-9._-]+)"
)
# An address starts at a word's edge, or just after a JSON escape (\n, \t ...)
# whose letter is never taken as part of it: "\n@AGENTS.md" is no email, and
# taking its n would leave "\[" behind, which JSON can't read.
EMAIL = re.compile(
    r"(?:(?<=\\[nrtbf])|(?<![\w.%+\\-]))[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
#: this file's own shapes and the privacy add-on's, so it never takes out less
#: than either; a match holding a quote or a backslash is left to PEM
KEYS = [PEM, *privacy_keys(), KEY]


def redact(line: str) -> tuple[str, list[tuple[str, str, str]]]:
    """(the line with removals made, [(kind, what it became, a stub)])."""
    out = []

    def key(m: re.Match) -> str:
        if m.re is not PEM and ('"' in m.group() or "\\" in m.group()):
            return m.group()
        out.append(("a key", "[redacted:key]", "…" + m.group()[-4:]))
        return "[redacted:key]"

    def home(m: re.Match) -> str:
        kept = m.group("base") + "[redacted]"
        out.append(("a home path", kept, "…" + m.group("name")[-4:]))
        return kept

    def email(m: re.Match) -> str:
        at = m.group().split("@", 1)[1]
        out.append(("an email", "[redacted:email]", "…" + m.group()[0] + "@" + at))
        return "[redacted:email]"

    for rx in KEYS:
        line = rx.sub(key, line)
    line = HOME.sub(home, line)
    line = EMAIL.sub(email, line)
    return line, out


def redact_lines(text: str) -> tuple[list[str], list[tuple]]:
    """(each line redacted, [(line, kind, what it became, a stub)]). A key
    block's body lines, between a BEGIN with no END and its END, go whole."""
    kept, listed, inside = [], [], False
    for n, line in enumerate(text.splitlines(keepends=True), 1):
        if inside:
            body = line.rstrip("\r\n")
            end = PEM_END.search(body)
            cut = end.end() if end else len(body)
            inside = not end
            if body[:cut].strip():
                listed.append(
                    (n, "a key", "[redacted:key]", "…" + body[:cut].strip()[-4:])
                )
                line = "[redacted:key]" + line[cut:]
        else:
            begin = PEM_BEGIN.search(line)
            inside = bool(begin) and not PEM_END.search(line, begin.end())
        clean, got = redact(line)
        kept.append(clean)
        listed += [(n, *x) for x in got]
    return kept, listed


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--from", "--to"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--from") or not opts.get("--to") or args:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    src, to = Path(opts["--from"]), Path(opts["--to"])
    if not src.is_file():
        print(f"refused: {src} isn't a file", file=sys.stderr)
        return kernel.REFUSED
    try:
        text = src.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"refused: could not read {src}: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    kept, listed = redact_lines(text)
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as e:
        print(f"refused: could not write {to}: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write("".join(kept))
    if listed:
        wk = max(len(k) for _, k, *_ in listed)
        wb = max(len(b) for *_, b, _ in listed)
        for n, kind, became, stub in listed:
            print(f"line {n:<6} {kind:<{wk}}  {became:<{wb}}  {stub}")
    lines = len({n for n, *_ in listed})
    print(f"wrote {opts['--to']}: {len(listed)}"
          f" removal{'s' if len(listed) != 1 else ''} on {lines}"
          f" line{'s' if lines != 1 else ''}")  # fmt: skip
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
