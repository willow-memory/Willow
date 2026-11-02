"""ris.py: RIS citation exports, each reference as a passage. Python 3.9+.

    python adapters/stdlib/ris/ris.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .ris and .enw files (hidden folders and files skipped): the
citation export of EndNote, Zotero, Mendeley, Web of Science, Scopus and
Google Scholar. Each reference becomes one paragraph that opens with its
citation, so a question about a paper finds who wrote it, when and where:

    Example, Ada; Sample, Cy (2020). Tides of the Estuary. Journal of Made-Up Studies 12(3), 45–67.
    JOUR
    2020-03-15
    10.1000/xyz123
    tides; estuaries
    We measure the tide at six harbours.
    Read for chapter 2.

Then each value the reference holds, on its own line and with no label of
this reader's ("doi:", "keywords:"): a word written into every passage would
let a question about something the folder doesn't hold be answered by any of
them. The type is the code as the file writes it (JOUR, BOOK). A .enw file is
read by what it holds: RIS lines (`TY  - JOUR`), or EndNote's own tagged lines
(`%A`, `%T`, `%0 Journal Article`). The year is taken only from the date tags
(PY, Y1, DA; %D); with none, the citation has no year. A reference that is
broken (a TY with no ER before the next, or the file ending inside one) is
skipped and counted in the file's closing passage:

    2 references; 1 malformed

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file with no reference, or that cannot be read, is
skipped and counted:

    wrote 2 files to MIRROR; skipped 1

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import html
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

TAG = re.compile(r"([A-Z][A-Z0-9])  -(?: (.*))?$")
REFER = re.compile(r"%([0-9A-Z@!#$&()*+^>~\]])(?: (.*))?$")
# EndNote's own letters, as the RIS tag each one means here
REFER_TAGS = {"0": "TY", "A": "AU", "E": "A2", "T": "TI", "J": "T2", "B": "BT", "D": "PY", "8": "DA",
              "V": "VL", "N": "IS", "P": "SP", "R": "DO", "K": "KW", "X": "AB", "Z": "N1", "U": "UR",
              "I": "PB", "C": "CY", "@": "SN", "F": "ID"}  # fmt: skip
MARKUP = re.compile(r"</?(p|div|br|span|b|i|em|strong|sub|sup|a|ul|ol|li|h[1-6])\b[^>]*>", re.I)  # fmt: skip
INLINE = ("span", "b", "i", "em", "strong", "sub", "sup", "a")
YEAR = re.compile(r"\s*(\d{4})(?!\d)")
FULL_DATE = re.compile(r"\s*(\d{4})/(\d{2})/(\d{2})(?:/.*)?\s*$")


def records(text: str) -> tuple[list[dict[str, list[str]]], int]:
    """RIS text as ([{tag: [values]}], broken), a record running from TY to ER.
    A line with no tag continues the tag before it."""
    out, broken, rec, last = [], 0, None, None
    for line in text.splitlines():
        m = TAG.match(line.rstrip())
        if m:
            tag, val = m.group(1), (m.group(2) or "").strip()
            if tag == "TY":
                broken += rec is not None
                rec, last = {"TY": [val]}, "TY"
            elif rec is None:
                continue
            elif tag == "ER":
                out.append(rec)
                rec = None
            else:
                rec.setdefault(tag, []).append(val)
                last = tag
        elif rec is not None and line.strip():
            vals = rec[last]
            vals[-1] = (vals[-1] + " " + line.strip()).strip()
    return out, broken + (rec is not None)


def refer_records(text: str) -> tuple[list[dict[str, list[str]]], int]:
    """EndNote's tagged text (%A, %T...) as RIS records: one per run of lines
    between blank lines. A run whose first line has no % tag is broken."""
    out, broken = [], 0
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n").replace("\r", "\n")):
        lines = [x for x in block.split("\n") if x.strip()]
        if not lines:
            continue
        if not REFER.match(lines[0].rstrip()):
            broken += 1
            continue
        rec, last = {}, None
        for line in lines:
            m = REFER.match(line.rstrip())
            if m:
                last = REFER_TAGS.get(m.group(1), "")
                rec.setdefault(last, []).append((m.group(2) or "").strip())
            elif last == "KW":
                rec[last].append(line.strip())
            else:
                rec[last][-1] = (rec[last][-1] + " " + line.strip()).strip()
        rec.pop("", None)
        out.append(rec)
    return out, broken


def plain(val: str) -> str:
    """A value as text: a note's HTML (Zotero writes them so) read as words."""
    if MARKUP.search(val):
        val = html.unescape(
            MARKUP.sub(lambda m: "" if m.group(1).lower() in INLINE else " ", val)
        )
    return " ".join(val.split())


def year_and_date(r: dict[str, list[str]]) -> tuple[str, str]:
    """(year, date) from the date tags only, PY then Y1 then DA. The year is
    the four digits a date opens with; the date is said when it holds more
    than the year: YYYY/MM/DD as 2020-03-15, anything else as written."""
    year = date = ""
    for tag in ("PY", "Y1", "DA"):
        for val in r.get(tag, []):
            m = YEAR.match(val)
            if m and not year:
                year = m.group(1)
            full = FULL_DATE.match(val)
            rest = val.strip().strip("/")
            if not date and full:
                date = "-".join(full.groups())
            elif not date and rest and rest != (m.group(1) if m else None):
                date = rest
    return year, date


def first(r: dict[str, list[str]], *tags: str) -> str:
    for tag in tags:
        for val in r.get(tag, []):
            if plain(val):
                return plain(val)
    return ""


def every(r: dict[str, list[str]], *tags: str) -> list[str]:
    return [plain(v) for tag in tags for v in r.get(tag, []) if plain(v)]


def ended(text: str) -> str:
    return text if text.endswith((".", "?", "!")) else text + "."


def passage(r: dict[str, list[str]]) -> str:
    """One reference: its citation, then each value on its own line with no
    label of this reader's, so no word here repeats in every passage."""
    year, date = year_and_date(r)
    who = "; ".join(every(r, "AU", "A1")) + (f" ({year})" if year else "")
    vol = first(r, "VL") + (f"({first(r, 'IS')})" if first(r, "IS") else "")
    sp, ep = first(r, "SP"), first(r, "EP")
    where = " ".join(x for x in (first(r, "T2", "JF", "JO", "JA", "BT"), vol) if x)
    tail = ", ".join(x for x in (where, f"{sp}–{ep}" if sp and ep else sp or ep) if x)
    title = first(r, "TI", "T1", "CT")
    cite = " ".join(ended(x.strip()) for x in (who, title, tail) if x.strip())
    lines = [
        cite,
        first(r, "TY"),
        date,
        "; ".join(every(r, "A2", "ED")),
        "; ".join(every(r, "A3", "A4")),
        ", ".join(x for x in (first(r, "PB"), first(r, "CY")) if x),
        first(r, "DO"),
        "; ".join(every(r, "UR")),
        first(r, "SN"),
        first(r, "ID"),
        "; ".join(every(r, "KW")),
        first(r, "AB", "N2"),
        "; ".join(every(r, "N1")),
    ]
    return "\n".join(x for x in lines if x)


def convert(data: bytes) -> str | None:
    text = data.decode("utf-8-sig")
    head = next((x.strip() for x in text.splitlines() if x.strip()), "")
    found, broken = (refer_records if head.startswith("%") else records)(text)
    if not found:
        return None
    close = f"{len(found)} references" + (f"; {broken} malformed" if broken else "")
    return "".join(passage(r) + "\n\n" for r in found) + close + "\n"


EXTS = (".ris", ".enw")
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: ris.py mirror --from FOLDER --to MIRROR"


def _sources(folder: Path) -> list[Path]:
    """Files under `folder` this reads, sorted by relative path. Hidden folders
    and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if not name.startswith(".") and name.lower().endswith(EXTS) and p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            text = convert(path.read_bytes())
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except ERRORS:
            skipped += 1
            continue
        wrote += 1
    return wrote, skipped


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2])) if argv[:1] == ["mirror"] else {}
    if len(argv) != 5 or sorted(opts) != ["--from", "--to"]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    if not Path(opts["--from"]).is_dir():
        print(f"refused: not a folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    src = Path(opts["--from"]).resolve()
    dst = Path(opts["--to"]).resolve()
    if _within(dst, src) or _within(src, dst):
        print(
            "refused: MIRROR and FOLDER must not be inside one another", file=sys.stderr
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
