"""notes.py: an Obsidian or Logseq vault, as plain text the kernel can search.

    python adapters/stdlib/notes/notes.py mirror --from FOLDER --to MIRROR

Each .md note under FOLDER becomes MIRROR/<same relative path>.txt
(`daily/2024-03-03.md` -> `MIRROR/daily/2024-03-03.md.txt`). Originals are only
read, never changed.

What changes, and what does not:

- `[[Note]]`, `[[Note|shown]]` and `[[Note#Heading]]` become the shown text if
  given, else the note's name, so a question finds the words a reader sees.
- `#tags`, front-matter `tags:` (a YAML list or a comma list) and Logseq
  `tags::` are collected into a line `tags: a, b, c` at the top of the note.
- Front matter is removed, except its tags and a `date:` (or `created:`) that
  is an ISO date, written as `date: YYYY-MM-DD`.
- Logseq's leading `- ` bullets and `id::` lines are dropped; the indentation
  in front of a bullet goes with it.
- At the end, `linked from: A, B` lists the notes that link here, and
  `links to: X, Y` the notes this one links to. Either says `none` when
  there are none: absence is recorded, not left out. Names match without regard to
  case, and a note's name is its file name without .md.
- Every other line is kept as written, and lines inside a code fence are not
  touched at all.

A file that is not UTF-8 text, or holds a NUL byte, is skipped and counted.
Folders whose name starts with "." are not walked, so `.obsidian` and `.trash`
are skipped.

    wrote 12 files to MIRROR; skipped 1

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused. A
refusal names what is wrong: FOLDER not a folder, or MIRROR inside FOLDER (or
FOLDER inside MIRROR).
"""

from __future__ import annotations

import datetime
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: notes.py mirror --from FOLDER --to MIRROR"

BULLET = re.compile(r"^\s*- ")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
ID_LINE = re.compile(r"^\s*id::")
TAGS_LINE = re.compile(r"^\s*tags::(.*)$")
LINK = re.compile(r"!?\[\[([^\[\]\n|]*)(?:\|([^\[\]\n]*))?\]\]")
PAGE_LINK = re.compile(r"\[\[([^\[\]]+)\]\]")
TAG = re.compile(r"(?:^|(?<=\s))#([\w/-]*[^\W\d][\w/-]*)")
FRONT_KEY = re.compile(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$")
ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})(?!\d)")


@dataclass
class Note:
    rel: str  # path inside FOLDER, posix: "daily/2024-03-03.md"
    stem: str  # the file name without .md: "2024-03-03"
    date: str | None
    tags: list[str]
    body: list[str]  # the lines after the header, as they will be written
    links: list[tuple[str, str]]  # (match key, name) in order of appearance

    @property
    def key(self) -> str:
        return self.stem.casefold()


def _iso_date(value: str) -> str | None:
    m = ISO.match(value.strip().strip("\"'[]"))
    if not m:
        return None
    try:
        datetime.date(*map(int, m.groups()))
    except ValueError:
        return None
    return m.group(0)


def _split_tags(value: str) -> list[str]:
    """Tag names from a YAML list, a comma list, or Logseq's [[page]] and #tag."""
    names = PAGE_LINK.findall(value)
    rest = PAGE_LINK.sub(" ", value).strip()
    if rest.startswith("[") and rest.endswith("]"):
        rest = rest[1:-1]
    names += re.split(r"[\s,]+", rest)
    out = []
    for name in names:
        name = name.strip().strip("\"'").lstrip("#").strip()
        if name:
            out.append(name)
    return out


def _front_matter(lines: list[str]) -> tuple[str | None, list[str], list[str]]:
    """(date, tags, lines after the header). No header, or one that does not
    close, or holds a line that is not YAML, is no front matter at all."""
    if not lines or lines[0].strip() != "---":
        return None, [], lines
    end = None
    for i in range(1, len(lines)):
        s = lines[i].strip()
        if s in ("---", "..."):
            end = i
            break
        if not (not s or lines[i][:1].isspace() or s.startswith("-")):
            if not FRONT_KEY.match(lines[i]):
                return None, [], lines
    if end is None:
        return None, [], lines
    fields: dict[str, str] = {}
    key = ""
    for line in lines[1:end]:
        if m := FRONT_KEY.match(line):
            key = m.group(1).lower()
            fields[key] = m.group(2)
        elif key and (m := re.match(r"^\s*-\s*(.*)$", line)):
            fields[key] = fields.get(key, "") + " " + m.group(1)
    date = None
    for k in ("date", "created"):
        date = _iso_date(fields.get(k, ""))
        if date:
            break
    return date, _split_tags(fields.get("tags", "")), lines[end + 1 :]


def _link(m: re.Match, links: list[tuple[str, str]]) -> str:
    """One [[wikilink]] as the words a reader sees; its note is recorded."""
    target, alias = m.group(1), (m.group(2) or "").strip()
    parts = re.split(r"[#^]", target, maxsplit=1)
    name = parts[0].strip().rsplit("/", 1)[-1].strip()
    if name.lower().endswith(".md"):
        name = name[:-3].strip()
    if name:
        links.append((name.casefold(), name))
        return alias or name
    heading = parts[1].strip() if len(parts) > 1 else ""  # [[#Heading]]
    return alias or heading or m.group(0)


def _parse(rel: str, text: str) -> Note:
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    date, tags, lines = _front_matter(lines)
    body: list[str] = []
    links: list[tuple[str, str]] = []
    fence = ""  # the opening fence while inside a code block, else ""
    for raw in lines:
        if fence:
            body.append(raw)
            s = raw.strip()
            if s.startswith(fence) and set(s) <= {fence[0]}:
                fence = ""
            continue
        line = BULLET.sub("", raw, count=1)
        if m := FENCE.match(line):
            fence = m.group(1)
            body.append(line)
        elif ID_LINE.match(line):
            continue
        elif m := TAGS_LINE.match(line):
            tags.extend(_split_tags(m.group(1)))
        else:
            tags.extend(TAG.findall(line))
            body.append(LINK.sub(lambda m: _link(m, links), line))
    return Note(rel, Path(rel).name[:-3], date, tags, body, links)


def _read(folder: Path) -> tuple[list[Note], int]:
    """Every readable .md note under FOLDER, sorted by path, and how many were
    skipped. Any path part starting with "." is not walked."""
    found: list[tuple[tuple[str, ...], Path]] = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            path = Path(dirpath) / name
            if name.startswith(".") or not name.lower().endswith(".md"):
                continue
            if path.is_file():
                found.append((path.relative_to(folder).parts, path))
    notes: list[Note] = []
    skipped = 0
    for parts, path in sorted(found, key=lambda pair: pair[0]):
        try:
            raw = path.read_bytes()
            if b"\0" in raw:
                raise ValueError("binary")
            text = raw.decode("utf-8")
        except (OSError, ValueError):  # UnicodeDecodeError is a ValueError
            skipped += 1
            continue
        if text.startswith("﻿"):
            text = text[1:]
        notes.append(_parse("/".join(parts), text))
    return notes, skipped


def _links(notes: list[Note]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """(linked from, links to), each by note path: the names, sorted by key,
    each listed once. A note's link to its own name is not counted."""
    by_key: dict[str, list[Note]] = {}
    for n in notes:
        by_key.setdefault(n.key, []).append(n)
    from_: dict[str, dict[str, str]] = {n.rel: {} for n in notes}
    to: dict[str, list[str]] = {}
    for src in notes:
        outgoing: dict[str, str] = {}
        for key, name in src.links:
            if key == src.key:
                continue
            # a link to a note in the vault is listed by that note's file name
            outgoing.setdefault(key, by_key[key][0].stem if key in by_key else name)
            for tgt in by_key.get(key, []):
                from_[tgt.rel].setdefault(src.key, src.stem)
        to[src.rel] = [outgoing[k] for k in sorted(outgoing)]
    back = {rel: [names[k] for k in sorted(names)] for rel, names in from_.items()}
    return back, to


def _render(note: Note, back: list[str], links: list[str]) -> str:
    blocks: list[str] = []
    head: list[str] = []
    if note.date:
        head.append(f"date: {note.date}")
    if note.tags:
        unique: dict[str, str] = {}
        for t in note.tags:
            unique.setdefault(t.casefold(), t)
        head.append("tags: " + ", ".join(unique[k] for k in sorted(unique)))
    if head:
        blocks.append("\n".join(head))
    body = list(note.body)
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    if body:
        blocks.append("\n".join(body))
    # absence is said, not left out: "no note links here" is a fact
    blocks.append("linked from: " + (", ".join(back) or "none"))
    blocks.append("links to: " + (", ".join(links) or "none"))
    return "\n\n".join(blocks) + "\n"


def mirror(folder: Path, mirror_dir: Path) -> int:
    folder, mirror_dir = folder.resolve(), mirror_dir.resolve()
    if not folder.is_dir():
        print(f"refused: {folder} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    if mirror_dir.is_relative_to(folder):
        print("refused: MIRROR is inside FOLDER", file=sys.stderr)
        return kernel.REFUSED
    if folder.is_relative_to(mirror_dir):
        print("refused: FOLDER is inside MIRROR", file=sys.stderr)
        return kernel.REFUSED

    notes, skipped = _read(folder)
    back, to = _links(notes)
    wrote = 0
    for note in notes:
        target = mirror_dir / (note.rel + ".txt")
        text = _render(note, back[note.rel], to[note.rel])
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except OSError as exc:
            print(f"refused: cannot write {target}: {exc}", file=sys.stderr)
            return kernel.REFUSED
        wrote += 1

    print(f"wrote {wrote} files to {mirror_dir}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


def main(argv: list[str]) -> int:
    if (
        len(argv) != 5
        or argv[0] != "mirror"
        or argv[1] != "--from"
        or argv[3] != "--to"
    ):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    return mirror(Path(argv[2]), Path(argv[4]))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
