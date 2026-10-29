"""llms_txt.py: an llms.txt for your folder, and a check of one. Python 3.9+.

    python adapters/stdlib/llms-txt/llms_txt.py write --from FOLDER --to FILE [--base URL] [--title TEXT] [--summary TEXT]
    python adapters/stdlib/llms-txt/llms_txt.py check FILE

llms.txt is a Markdown file, at the top of a site or a folder, that tells a
language model what is there and where to read it (the format llmstxt.org
describes): a title, a one-line summary, and lists of links with a note on each.

`write` makes one from what is actually in FOLDER, nothing invented:

    # notes

    > 14 files from notes: Markdown and text, listed by folder.

    ## garden

    - [Tomatoes](garden/tomatoes.md): Tomatoes want six hours of sun.

    ## Optional

    - [Archive log](archive/log.txt): older entries, 120 KB

The title is the folder's name (--title), the summary says how many files there
are (--summary), each folder at the top of FOLDER is a section, files loose at
the top are "Files", and each file is a link with its first Markdown heading
(else its file name) as the text and its first line of prose, cut at 100
characters, as the note. A file over 50 KB goes under "Optional", the section the
format sets aside for what can be skipped when there is little room. Only text
files are listed (UTF-8, no NUL byte); hidden files and folders are left out. A
link is --base URL and the path, percent-encoded, or just the path.

`check` reads an llms.txt and says where it departs from the format:

    notes/llms.txt:1  the file must begin with a "# " title
    notes/llms.txt:7  a list item should be "- [text](url)" with a note after ": "

It checks: one "# " title, first; a "> " summary after it; no heading but "##"
after the title; each section a list of "- [text](url)" items, with an optional
": note"; links with a scheme, or a path (a relative link is said); "Optional"
last; no empty section; no tabs.

`write` reads FOLDER and writes only FILE, once, readable only by you, never over
a file that exists, the same bytes for the same folder. `check` only reads.

Exit codes, the kernel's: 0 written, or checked and clean; 42 `check` found a
departure, or `write` found nothing to list (nothing written); 2 refused.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from urllib.parse import quote

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

BIG = 50_000  # bytes over which a file is "Optional"
ITEM = re.compile(r"^- \[([^\]\n]+)\]\(([^)\s]+)\)(?:: (.+))?$")
URL = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def read_text(p: Path) -> str | None:
    try:
        raw = p.read_bytes()
        if b"\0" in raw[: kernel.SNIFF]:
            return None
        return raw.decode("utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None


def describe(text: str, name: str) -> tuple[str, str]:
    """(link text, note): the first heading or the name, and the first line of prose."""
    title, note, fenced = "", "", False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            fenced = not fenced
        if fenced or not s or s.startswith("```"):
            continue
        m = re.match(r"#{1,6}\s+(.+?)\s*#*$", s)
        if m:
            title = title or m.group(1)
        elif not note and not s.startswith(("```", "---", "<", "|", "![", "[!")):
            note = s
        if title and note:
            break
    note = " ".join(note.replace("[", "").replace("]", "").split())
    return (title or name).replace("[", "(").replace("]", ")"), note if len(
        note
    ) <= 100 else note[:99] + "…"


def files(folder: Path) -> list[tuple[str, str, Path, str]]:
    """(section, link path, file, text) for each text file, in a stable order."""
    out = []
    for p in sorted(folder.rglob("*"), key=lambda q: q.relative_to(folder).as_posix()):
        rel = p.relative_to(folder)
        if not p.is_file() or any(part.startswith(".") for part in rel.parts):
            continue
        text = read_text(p)
        if text is not None:
            out.append(
                (
                    rel.parts[0] if len(rel.parts) > 1 else "Files",
                    rel.as_posix(),
                    p,
                    text,
                )
            )
    return out


def write_text(
    folder: Path, title: str, summary: str | None, base: str | None
) -> str | None:
    found = files(folder)
    if not found:
        return None
    sections: dict[str, list[str]] = {}
    optional: list[str] = []
    for section, rel, p, text in found:
        name, note = describe(text, Path(rel).name)
        url = f"{base.rstrip('/')}/{quote(rel)}" if base else quote(rel)
        big = p.stat().st_size > BIG
        parts = ([note] if note else []) + (
            [f"{p.stat().st_size // 1000} KB"] if big else []
        )
        item = f"- [{name}]({url})" + (": " + ", ".join(parts) if parts else "")
        (optional if big else sections.setdefault(section, [])).append(item)
    lead = (
        summary
        or f"{len(found)} file{'s' if len(found) != 1 else ''} from {folder.name}: text and Markdown, listed by folder."
    )
    out = [f"# {title}", "", f"> {' '.join(lead.split())}", ""]
    for section in sorted(sections, key=lambda s: (s == "Files", s.lower())):
        out += [f"## {section}", ""] + sections[section] + [""]
    if optional:
        out += ["## Optional", ""] + optional + [""]
    return "\n".join(out)


def check(text: str) -> list[tuple[int, str]]:
    """[(line, what is wrong)] against the format."""
    lines, problems = text.split("\n"), []
    titles = [n for n, x in enumerate(lines, 1) if x.startswith("# ")]
    first = next((n for n, x in enumerate(lines, 1) if x.strip()), 0)
    if not titles or titles[0] != first:
        problems.append((first or 1, 'the file must begin with a "# " title'))
    for n in titles[1:]:
        problems.append((n, 'only one "# " title is allowed'))
    sections, current, seen_h2, summary = [], None, False, False
    for n, x in enumerate(lines, 1):
        if "\t" in x:
            problems.append((n, "a tab: use spaces"))
        if x.startswith("> ") and not seen_h2:
            summary = True
        if re.match(r"#{3,6}\s", x):
            problems.append((n, 'after the title, headings must be "## " sections'))
        elif x.startswith("## "):
            seen_h2 = True
            current = (n, x[3:].strip(), [])
            sections.append(current)
        elif x.startswith("##"):
            problems.append((n, 'a section heading must be "## " and a name'))
        elif current and x.strip() and not x.startswith(">"):
            current[2].append(n)
            m = ITEM.match(x)
            if not m:
                problems.append(
                    (n, 'a list item should be "- [text](url)" with a note after ": "')
                )
            elif not URL.match(m.group(2)):
                problems.append(
                    (
                        n,
                        f"a relative link ({m.group(2)}): a scheme-less path works only beside the file",
                    )
                )
    if titles and not summary:
        problems.append((titles[0], 'a "> " summary should follow the title'))
    for i, (n, name, body) in enumerate(sections):
        if not body:
            problems.append((n, f'the section "{name}" is empty'))
        if name.lower() == "optional" and i != len(sections) - 1:
            problems.append((n, 'the "Optional" section should be last'))
    return sorted(set(problems))


def main(argv: list[str]) -> int:
    if argv[:1] == ["check"] and len(argv) == 2:
        path = Path(argv[1])
        if not path.is_file():
            print(f"refused: {path} isn't a file", file=sys.stderr)
            return kernel.REFUSED
        text = read_text(path)
        if text is None:
            print(f"refused: {path} isn't text", file=sys.stderr)
            return kernel.REFUSED
        problems = check(text)
        for n, what in problems:
            print(f"{path}:{n}  {what}")
        if not problems:
            print(f"{path} follows the format.")
        return kernel.ESCALATE if problems else kernel.ALIVE
    opts, it = {}, iter(argv[1:])
    for a in it:
        opts[a] = next(it, "")
    if (
        argv[:1] != ["write"]
        or not {"--from", "--to"} <= set(opts)
        or set(opts) - {"--from", "--to", "--base", "--title", "--summary"}
        or not all(opts.values())
        or (
            opts.get("--base")
            and not opts["--base"].startswith(("http://", "https://"))
        )
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    folder, to = Path(opts["--from"]), Path(opts["--to"])
    if not folder.is_dir():
        print(f"refused: {folder} isn't a folder", file=sys.stderr)
        return kernel.REFUSED
    text = write_text(
        folder,
        opts.get("--title") or folder.resolve().name,
        opts.get("--summary"),
        opts.get("--base"),
    )
    if text is None:
        print("Nothing to list: no text file in that folder, so nothing was written.")
        return kernel.ESCALATE
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as e:
        print(f"refused: could not write {to}: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    n = text.count("\n- ") + text.startswith("- ")
    print(f"wrote {to}: {n} file{'s' if n != 1 else ''} listed")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
