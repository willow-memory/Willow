"""persona_card.py: a persona card compiled to the same prompt bytes every time.

    python adapters/stdlib/persona-card/persona_card.py \\
        --box DIR --from FILE [--now TS]
    python adapters/stdlib/persona-card/persona_card.py \\
        check --box DIR --from FILE

A card is a markdown file. An optional header

    <!-- willow-persona
    name: Binder
    -->

names it; without one, the file's stem is the name. The compiled prompt is
always the same bytes for the same card: a `# name` line, a blank line, the
body, one trailing newline. Its SHA-256 goes on the record through the
kernel's own append, never the prompt itself.

    compiled  Binder  sha256=…  (row 1)

`check` holds a card to its latest row: `same` while the bytes match,
`changed` when they don't, `never compiled` when there is no row.

It never reads the key. Exit codes, the kernel's: 0 compiled, or every card
the same; 42 a card changed or was never compiled, or nothing to compile;
2 refused.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = (
    "usage: persona_card.py --box DIR --from FILE [--now TS]\n"
    "       persona_card.py check --box DIR --from FILE"
)
KIND = "persona-card"
MARKER = "<!-- willow-persona"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def card_of(raw: str, stem: str) -> tuple[str, str]:
    """(name, body) from a card's text."""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    if not text.lstrip().startswith(MARKER):
        return stem, text
    start = text.find(MARKER)
    end = text.find("-->", start)
    if end < 0:
        return stem, text
    header = text[start + len(MARKER) : end]
    name = stem
    for line in header.splitlines():
        s = line.strip()
        if s.startswith("name:"):
            got = s.split(":", 1)[1].strip()
            if got:
                name = got
    body = text[end + 3 :]
    if body.startswith("\n"):
        body = body[1:]
    return name, body


def compile_prompt(name: str, body: str) -> bytes:
    """The system-prompt bytes: same card, same bytes."""
    return f"# {name}\n\n{body.strip()}\n".encode("utf-8")


def cards_from(src: Path) -> list[Path]:
    if src.is_file():
        return [src]
    found = []
    for p in sorted(src.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(src)
        if any(part.startswith(".") for part in rel.parts):
            continue
        if p.suffix.lower() != ".md":
            continue
        found.append(p)
    return found


def latest(rows: list[dict]) -> dict[str, dict]:
    """Each path's latest persona-card row."""
    return {r["path"]: r for r in rows if r["kind"] == KIND}


def state(path: Path, digest: str, pins: dict[str, dict]) -> tuple[str, str]:
    row = pins.get(str(path.resolve()))
    if row is None:
        return "never compiled", f"never compiled  {path}"
    if row["sha256"] != digest:
        return "changed", f"changed         {path} (compiled at row {row['n']})"
    return "same", f"same            {path} (row {row['n']})"


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--from", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    verb = args[0] if args == ["check"] else ""
    if verb:
        args = args[1:]
    if not opts.get("--box") or not opts.get("--from") or args:
        print(USAGE, file=sys.stderr)
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
    src = Path(opts["--from"])
    if not src.exists():
        print(f"refused: not a file or folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    paths = cards_from(src)
    if not paths:
        print("nothing there: no persona card")
        return kernel.ESCALATE
    if verb == "check":
        pins = latest(rows)
        said = []
        for path in paths:
            name, body = card_of(path.read_text(encoding="utf-8"), path.stem)
            digest = sha256_bytes(compile_prompt(name, body))
            said.append(state(path, digest, pins))
        for _, line in said:
            print(line)
        return kernel.ALIVE if all(s == "same" for s, _ in said) else kernel.ESCALATE
    ts = opts.get("--now") or kernel.now()
    for path in paths:
        name, body = card_of(path.read_text(encoding="utf-8"), path.stem)
        prompt = compile_prompt(name, body)
        digest = sha256_bytes(prompt)
        row = kernel.append(
            box,
            ts,
            KIND,
            who="persona-card",
            name=name,
            path=str(path.resolve()),
            sha256=digest,
        )
        print(f"compiled  {name}  sha256={digest}  (row {row['n']})")
        print(prompt.decode("utf-8"), end="")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
