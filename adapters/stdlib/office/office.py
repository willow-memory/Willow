"""office.py: the text inside your .docx, .odt, .pptx, .xlsx and .ods files, as
plain text beside them, so the kernel can answer from them.

    python adapters/stdlib/office/office.py mirror --from FOLDER --to MIRROR

Each office file under FOLDER becomes MIRROR/<same relative path>.txt
(`reports/q3.docx` -> `MIRROR/reports/q3.docx.txt`). Paragraphs are lines
separated by blank lines. A slide or sheet starts with a heading line,
`== slide 3` or `== sheet Budget`. A spreadsheet row is one line, its cells
joined by ` | `.

A file that will not parse (not a zip, a part missing, bad XML) is skipped and
counted, never a crash. Folders starting with "." are not walked. Files that
are not one of the five formats are not counted either way.

    wrote 3 files to MIRROR; skipped 1

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused. A
refusal names what is wrong: FOLDER not a folder, or MIRROR inside FOLDER (or
FOLDER inside MIRROR). Originals are only read, never changed.
"""

from __future__ import annotations

import os
import sys
import zipfile
import zlib
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: office.py mirror --from FOLDER --to MIRROR"

FORMATS = (".docx", ".odt", ".pptx", ".xlsx", ".ods")

# A zip bomb is bounded here: a part is read at most this far, then refused.
MAX_PART = 64 * 1024 * 1024

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
SS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG = "{http://schemas.openxmlformats.org/package/2006/relationships}"
OFF = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"
TXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
TBL = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"


class Corrupt(Exception):
    """A file that cannot be read as the format its name says."""


# ── reading a part out of the zip ───────────────────────────────────────────


def _part(zf: zipfile.ZipFile, name: str) -> ET.Element:
    try:
        with zf.open(name) as f:
            data = f.read(MAX_PART + 1)
    except KeyError:
        raise Corrupt(f"no {name} inside") from None
    if len(data) > MAX_PART:
        raise Corrupt(f"{name} is larger than {MAX_PART} bytes")
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise Corrupt(f"{name} is not XML: {exc}") from None


def _clean(text: str) -> str:
    """One paragraph: its non-empty lines, stripped, joined by newlines."""
    return "\n".join(s for s in (ln.strip() for ln in text.splitlines()) if s)


def _walk_paragraphs(node: ET.Element, para_tags: set[str], flat) -> list[str]:
    """Each paragraph under `node`, in document order. A paragraph is not
    descended into, so nested text (a note, a text box) stays in its parent."""
    out: list[str] = []
    for child in node:
        if child.tag in para_tags:
            text = _clean(flat(child))
            if text:
                out.append(text)
        else:
            out.extend(_walk_paragraphs(child, para_tags, flat))
    return out


def _flat_ooxml(node: ET.Element) -> str:
    """Text of an OOXML paragraph: runs' text, a tab as a tab, a break as a
    newline. Looks through hyperlinks, fields and text boxes."""
    parts: list[str] = []
    for el in node.iter():
        if el.tag in (W + "t", A + "t"):
            parts.append(el.text or "")
        elif el.tag in (W + "tab", A + "tab"):
            parts.append("\t")
        elif el.tag in (W + "br", A + "br"):
            parts.append("\n")
    return "".join(parts)


def _flat_odf(node: ET.Element) -> str:
    """Text of an ODF paragraph, spaces and tabs and breaks as they are shown."""
    parts: list[str] = [node.text or ""]
    for child in node:
        if child.tag == TXT + "s":
            parts.append(" " * int(child.get(TXT + "c") or "1"))
        elif child.tag == TXT + "tab":
            parts.append("\t")
        elif child.tag == TXT + "line-break":
            parts.append("\n")
        else:
            parts.append(_flat_odf(child))
        parts.append(child.tail or "")
    return "".join(parts)


# ── the five formats ────────────────────────────────────────────────────────


def read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        root = _part(zf, "word/document.xml")
    return _blocks(_walk_paragraphs(root, {W + "p"}, _flat_ooxml))


def read_odt(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        root = _part(zf, "content.xml")
    return _blocks(_walk_paragraphs(root, {TXT + "p", TXT + "h"}, _flat_odf))


def read_pptx(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if _slide_number(n) is not None]
        names.sort(key=_slide_number)
        blocks = []
        for name in names:
            root = _part(zf, name)
            paras = _walk_paragraphs(root, {A + "p"}, _flat_ooxml)
            blocks.append(_blocks([f"== slide {_slide_number(name)}", *paras]))
    if not blocks:
        raise Corrupt("no slides inside")
    return "\n\n".join(blocks)


def _slide_number(name: str) -> int | None:
    base = name.rsplit("/", 1)
    if len(base) != 2 or base[0] != "ppt/slides":
        return None
    stem = base[1]
    if not (stem.startswith("slide") and stem.endswith(".xml")):
        return None
    digits = stem[len("slide") : -len(".xml")]
    return int(digits) if digits.isdigit() else None


def read_xlsx(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        strings = _shared_strings(zf)
        wb = _part(zf, "xl/workbook.xml")
        rels = _part(zf, "xl/_rels/workbook.xml.rels")
        targets = {
            rel.get("Id"): _xl_target(rel.get("Target", ""))
            for rel in rels.iter(PKG + "Relationship")
        }
        blocks = []
        for sheet in wb.iter(SS + "sheet"):
            name = sheet.get("name") or ""
            target = targets.get(sheet.get(R + "id"))
            if target is None:
                raise Corrupt(f"sheet {name!r} has no part")
            root = _part(zf, target)
            rows = [_row_text(row, strings) for row in root.iter(SS + "row")]
            blocks.append(_sheet(name, rows))
    if not blocks:
        raise Corrupt("no sheets inside")
    return "\n\n".join(blocks)


def _xl_target(target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return os.path.normpath(os.path.join("xl", target)).replace(os.sep, "/")


def _shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []  # a workbook with no shared strings may leave the part out
    root = _part(zf, "xl/sharedStrings.xml")  # present but broken: refused
    return [
        "".join(t.text or "" for t in si.iter(SS + "t")) for si in root.iter(SS + "si")
    ]


def _row_text(row: ET.Element, strings: list[str]) -> str:
    """One sheet row as one line; blank rows give ''."""
    cells: dict[int, str] = {}
    for c in row.iter(SS + "c"):
        col = _col_index(c.get("r") or "")
        cells[col] = _cell_value(c, strings)
    filled = [col for col, v in cells.items() if v]
    if not filled:
        return ""
    last = max(filled)
    line = " | ".join(cells.get(col, "") for col in range(1, last + 1))
    return " ".join(line.split("\n"))


def _cell_value(c: ET.Element, strings: list[str]) -> str:
    kind = c.get("t")
    if kind == "inlineStr":
        v = "".join(t.text or "" for t in c.iter(SS + "t"))
    else:
        el = c.find(SS + "v")
        v = (el.text or "") if el is not None else ""
        if kind == "s" and v:
            idx = int(v)
            if not 0 <= idx < len(strings):
                raise Corrupt(f"shared string {idx} is not in the table")
            v = strings[idx]
    return v.strip()


def _col_index(ref: str) -> int:
    n = 0
    for ch in ref:
        if not ch.isalpha():
            break
        n = n * 26 + (ord(ch.upper()) - ord("A") + 1)
    return n or 1


def read_ods(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        root = _part(zf, "content.xml")
    blocks = []
    for table in root.iter(TBL + "table"):
        rows = [_ods_row(r) for r in _ods_rows(table)]
        blocks.append(_sheet(table.get(TBL + "name") or "", rows))
    if not blocks:
        raise Corrupt("no sheets inside")
    return "\n\n".join(blocks)


def _ods_rows(node: ET.Element):
    """The rows of one table, looking through row groups but not into cells,
    so a nested table is not read as this sheet's rows."""
    for child in node:
        if child.tag == TBL + "table-row":
            yield child
        elif child.tag in (
            TBL + "table-header-rows",
            TBL + "table-rows",
            TBL + "table-row-group",
        ):
            yield from _ods_rows(child)


def _ods_row(row: ET.Element) -> str:
    """One row as one line. A run of identical empty rows, or empty columns,
    stored once with a repeat count, is not expanded past the last filled cell."""
    cells: list[str] = []
    for cell in row:
        if cell.tag not in (TBL + "table-cell", TBL + "covered-table-cell"):
            continue
        repeat = int(cell.get(TBL + "number-columns-repeated") or "1")
        text = _ods_cell(cell)
        if text:
            cells.extend([text] * min(repeat, 1024))  # a 16384-wide fill stays bounded
        else:
            cells.extend([""] * min(repeat, 1024))
    while cells and not cells[-1]:
        cells.pop()
    return " | ".join(cells)


def _ods_cell(cell: ET.Element) -> str:
    paras = [_clean(_flat_odf(p)) for p in cell.iter(TXT + "p")]
    text = "\n".join(p for p in paras if p)
    if not text:
        text = cell.get(OFF + "value") or ""
    return " ".join(text.split("\n"))


# ── blocks, the mirror, the command line ───────────────────────────────────


def _blocks(lines: list[str]) -> str:
    """Each paragraph or heading is a block of its own, blank-line separated."""
    return "\n\n".join(lines)


def _sheet(name: str, rows: list[str]) -> str:
    """A sheet: its heading, a blank line, then its rows, one line each. The
    rows stay together (no blank line between them) so a passage is a run of
    rows, not one row. Blank rows are dropped."""
    body = "\n".join(r for r in rows if r)
    head = f"== sheet {name}"
    return f"{head}\n\n{body}" if body else head


READERS = {
    ".docx": read_docx,
    ".odt": read_odt,
    ".pptx": read_pptx,
    ".xlsx": read_xlsx,
    ".ods": read_ods,
}


def _candidates(folder: Path):
    """Every file under FOLDER, sorted by relative path; any path part starting
    with '.' is skipped (its folder and the file alike)."""
    found: list[tuple[tuple[str, ...], Path]] = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        base = Path(dirpath)
        for name in filenames:
            if name.startswith("."):
                continue
            path = base / name
            rel = path.relative_to(folder).parts
            if path.is_file():
                found.append((rel, path))
    found.sort()
    return [path for _, path in found]


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

    wrote = skipped = 0
    for path in _candidates(folder):
        if path.suffix.lower() not in FORMATS:
            continue
        rel = path.relative_to(folder).as_posix()
        try:
            data = (READERS[path.suffix.lower()](path) + "\n").encode("utf-8")
        except (
            Corrupt,
            zipfile.BadZipFile,
            zlib.error,
            OSError,
            ValueError,
            RuntimeError,
            NotImplementedError,
            EOFError,
            KeyError,
            UnicodeError,
        ):
            skipped += 1  # a file that will not parse is counted, never a crash
            continue
        target = mirror_dir / (rel + ".txt")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
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
