"""thesis.py: a document's claims, each against your sources, and the ones
no passage holds.

    python adapters/stdlib/thesis/thesis.py --box DIR FILE [--top N]

Every sentence of FILE is a claim. Each is put to claim-check, part by part,
against the folder the box points at:

    line 4    held   policy.txt:12 (+1)   Google scans Gmail for ads.
    line 9    short  policy.txt:203 lacks scans   Gmail is read by people.
    3 claims; 1 held, 1 short; 1 skipped

and the ones with no passage holding every part are listed last, with the
parts no file has:

    without a passage holding every part:
      line 9   no file has: scans, people

**Held is where to read, not a verdict.** A passage holding every part may
deny the claim; one holding only some may back it in other words. Only
"no file has" is a hard fact: nothing in your folder names that part.

A sentence with fewer than two parts (its words less the common ones) is not
put to the sources, only counted as skipped. Headings and code fences are
not claims. Lines are the document's own.

It only reads. Exit codes, the kernel's: 0 every claim has a passage holding
all its parts; 42 some has none; 2 refused.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

CHECK = Path(__file__).resolve().parents[1] / "claim-check" / "claim_check.py"
spec = importlib.util.spec_from_file_location("willow_claim_check_for_thesis", CHECK)
claim_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(claim_check)

TOP = 1
SHOWN = 70  # characters of a claim shown
END = re.compile(r"(?<=[.!?])\s+")
LEAD = re.compile(r"^\s*(?:[-*+>]\s+|\d+[.)]\s+)+")


def claims(text: str) -> list[tuple[int, str]]:
    """(line, sentence) for each sentence outside headings and code fences. A
    sentence runs across the lines of a paragraph and is placed at the line
    it starts on."""
    out, para, fenced = [], [], False

    def flush() -> None:
        if not para:
            return
        flat, at = "", []  # the paragraph as one string, and each char's line
        for n, line in para:
            piece = line + " "
            flat += piece
            at += [n] * len(piece)
        pos = 0
        for s in END.split(flat):
            i = flat.index(s, pos)
            pos = i + len(s)
            if s.strip():
                out.append((at[i], " ".join(s.split())))
        para.clear()

    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            flush()
            fenced = not fenced
        elif fenced or not line.strip() or line.lstrip().startswith("#"):
            flush()
        else:
            bullet = LEAD.match(line)
            if bullet:
                flush()
            para.append((n, LEAD.sub("", line)))
    flush()
    return out


def short(s: str) -> str:
    return s if len(s) <= SHOWN else s[: SHOWN - 1].rstrip() + "…"


def main(argv: list[str]) -> int:
    top = TOP
    if len(argv) == 5 and argv[3] == "--top" and argv[4].isdigit() and int(argv[4]) > 0:
        top, argv = int(argv[4]), argv[:3]
    if len(argv) != 3 or argv[0] != "--box":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box, doc = Path(argv[1]), Path(argv[2])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    if not doc.is_file():
        print(f"refused: {doc} is not a file", file=sys.stderr)
        return kernel.REFUSED
    if doc.stat().st_size > kernel.MAX_FILE:
        print(f"refused: {doc} is over {kernel.MAX_FILE} bytes", file=sys.stderr)
        return kernel.REFUSED
    try:
        text = doc.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        print(f"refused: {doc} is not UTF-8 text", file=sys.stderr)
        return kernel.REFUSED
    cfg, alias = kernel.config(box), {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            print(f"refused: {why}", file=sys.stderr)
            return kernel.REFUSED
    pile = kernel.chunks(Path(cfg["pile"]))
    held, unheld, skipped = 0, [], 0
    for line, sentence in claims(text):
        want = claim_check.parts(sentence)
        if len(want) < 2:
            skipped += 1
            continue
        got = claim_check.check(pile, want, alias, top)
        if got["all"]:
            held += 1
            c = got["all"][0][0]
            more = f" (+{len(got['all']) - 1})" if len(got["all"]) > 1 else ""
            print(
                f"line {line:<4} held   {c['path']}:{c['line']}{more}   {short(sentence)}"
            )
        else:
            near = "; ".join(
                f"{c['path']}:{c['line']} lacks "
                + ", ".join(w for w in want if w not in h)
                for c, h in got["some"]
            )
            print(f"line {line:<4} short  {near or 'no part held'}   {short(sentence)}")
            unheld.append((line, got["absent"]))
    total = held + len(unheld)
    print(
        f"{total} claims; {held} held, {len(unheld)} short; {skipped} skipped"
        if total
        else f"No claims to check; {skipped} skipped."
    )
    if unheld:
        print("without a passage holding every part:")
        for line, absent in unheld:
            print(f"  line {line:<4} " + (f"no file has: {', '.join(absent)}"
                  if absent else "every part is somewhere, none in one place"))  # fmt: skip
    return kernel.ESCALATE if unheld else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
