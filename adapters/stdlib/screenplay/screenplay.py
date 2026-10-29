r"""screenplay.py: Fountain and Final Draft scripts: scenes, characters and lines. Python 3.9+.

    python adapters/stdlib/screenplay/screenplay.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .fountain and .fdx files (hidden folders and files skipped)
and writes each script as its scenes, so a line can be cited by scene:

    title: Garden Party
    author: Ana Example

    scene 1: INT. KITCHEN - DAY
    Ana waters the tomatoes.
    ANA: Six hours of sun.
    BEN (V.O.): Or so she says.

    scene 2: EXT. GARDEN - NIGHT

A scene is a heading (INT., EXT., EST., INT./EXT., I/E, or one forced with a
leading dot) with its scene number if the script gives one (`#12#`), else counted
from one. Action is kept as written. A character's cue and dialogue are joined
as "NAME: line", the extension (V.O.) kept; parentheticals, transitions, page
breaks, notes ([[...]]), boneyard (/* ... */), sections and synopses are left out.
A Fountain title page gives the title and author lines; a Final Draft file's
paragraphs are read by type (Scene Heading, Action, Character, Dialogue).
A file that declares entities is not read.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file with no scene or dialogue is skipped and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

HEADING = re.compile(r"^(?:\.(?!\.)|(?:INT|EXT|EST|INT\./EXT|INT/EXT|I/E)[. ])", re.I)
NUMBER = re.compile(r"\s*#([^#]+)#\s*$")
TITLE_KEY = re.compile(
    r"^(title|credit|author|authors|source|draft date|contact|copyright)\s*:\s*(.*)$",
    re.I,
)
CUE = re.compile(r"^[^a-z]*[A-Z][^a-z]*$")
LOWER = re.compile(r"\([^)]*[a-z][^)]*\)")


def fountain(text: str) -> list[tuple[str, str]]:
    """The script as (kind, text) events: title, heading, action, cue, dialogue."""
    text = re.sub(
        r"/\*.*?\*/", "", text.replace("\r\n", "\n").replace("\r", "\n"), flags=re.S
    )
    text = re.sub(r"\[\[.*?\]\]", "", text, flags=re.S)
    paragraphs = [p for p in re.split(r"\n[ \t]*\n", text.strip("\n"))]
    out: list[tuple[str, str]] = []
    start = 0
    first = paragraphs[0].split("\n")
    if (
        first
        and all(TITLE_KEY.match(x) or x.startswith((" ", "\t")) for x in first)
        and TITLE_KEY.match(first[0])
    ):
        key = ""
        for line in first:
            m = TITLE_KEY.match(line)
            if m:
                key = m.group(1).lower()
                out.append(("title", f"{key}: {m.group(2).strip()}".rstrip(": ")))
            elif key and line.strip():
                kind, prev = out[-1]
                out[-1] = (
                    kind,
                    prev + (" " if not prev.endswith(": ") else "") + line.strip(),
                )
        start = 1
    for para in paragraphs[start:]:
        lines = [x.rstrip() for x in para.split("\n") if x.strip()]
        if not lines:
            continue
        head = lines[0].strip()
        if HEADING.match(head) and len(lines) == 1:
            out.append(("heading", NUMBER.sub("", head.lstrip(".")).strip()))
        elif (
            head.startswith(("===", "="))
            or head.startswith("#")
            and not head.startswith("#[")
        ):
            if head.startswith("#"):
                out.append(("section", head.lstrip("# ").strip()))
        elif (
            head.startswith(">")
            and not head.endswith("<")
            or head.upper().endswith(" TO:")
            and len(lines) == 1
        ):
            continue
        elif (
            (
                head.startswith("@")
                or (CUE.match(head.rstrip("^ ")) and not LOWER.search(head))
            )
            and len(lines) > 1
            and not head.startswith("!")
        ):
            name = head.lstrip("@").rstrip("^ ").strip()
            spoken = [
                x.strip()
                for x in lines[1:]
                if not (x.strip().startswith("(") and x.strip().endswith(")"))
            ]
            out.append(("cue", name))
            out.append(("dialogue", " ".join(spoken)))
        else:
            body = " ".join(
                x.strip().lstrip("!").strip("> <").strip()
                if x.strip().startswith((">", "!"))
                else x.strip()
                for x in lines
            )
            out.append(("action", " ".join(body.split())))
    return out


def final_draft(data: bytes) -> list[tuple[str, str]]:
    root = ET.fromstring(data)
    kinds = {
        "Scene Heading": "heading",
        "Action": "action",
        "Character": "cue",
        "Dialogue": "dialogue",
    }
    out = []
    for para in root.iter("Paragraph"):
        kind = kinds.get(para.get("Type", ""))
        text = " ".join(
            "".join(t.itertext()).strip() for t in para.findall("Text")
        ).strip()
        if kind and text:
            out.append((kind, NUMBER.sub("", text)))
    return out


def render(events: list[tuple[str, str]]) -> str | None:
    if not any(k in ("heading", "dialogue") for k, _ in events):
        return None
    lines, scene, cue = [], 0, ""
    for kind, text in events:
        if kind == "title":
            lines.append(text)
        elif kind == "heading":
            scene += 1
            lines += ["", f"scene {scene}: {text}"]
        elif kind == "section":
            lines += ["", f"section: {text}"]
        elif kind == "action":
            lines.append(text)
        elif kind == "cue":
            cue = text
        elif kind == "dialogue" and cue:
            lines.append(f"{cue}: {text}")
    return "\n".join(lines).strip("\n") + "\n"


def convert(data: bytes) -> str | None:
    if b"<!ENTITY" in data:
        return None
    text = data.decode("utf-8-sig", errors="strict")
    if text.lstrip().startswith("<"):
        return render(final_draft(data)) if "<FinalDraft" in text[:2000] else None
    return render(fountain(text))


EXTS = (".fountain", ".fdx")
ERRORS = (OSError, UnicodeDecodeError, ValueError, ET.ParseError)

USAGE = "usage: screenplay.py mirror --from FOLDER --to MIRROR"


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
