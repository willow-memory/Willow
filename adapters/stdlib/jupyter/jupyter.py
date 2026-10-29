r"""jupyter.py: Jupyter notebooks: Markdown, code and text outputs as passages. Python 3.9+.

    python adapters/stdlib/jupyter/jupyter.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .ipynb files (hidden folders and files, and the
.ipynb_checkpoints folders Jupyter keeps, skipped) and writes each notebook as
text, one block for each cell, so a passage can be cited by its cell:

    notebook: Tide analysis (python3, python)

    cell 1 (markdown)
    # Tides at the estuary

    cell 2 (code)
    df = load("harbours.csv")
    output:
    6 rows

A cell's source is written as it is. For a code cell, its text outputs follow
under "output:" (printed text, a result's plain-text form, an error's name and
message), the first 20 lines of each. Pictures and other binary outputs are
left out, not guessed at. Raw cells are written as "raw". Notebooks in the older
nbformat 3 are read too.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file that is not a notebook is skipped and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

LINES = 20  # lines of one output kept


def joined(value) -> str:
    return (
        "".join(value)
        if isinstance(value, list)
        else value
        if isinstance(value, str)
        else ""
    )


def output_text(out: dict) -> str:
    kind = out.get("output_type")
    if kind == "stream":
        text = joined(out.get("text"))
    elif kind in ("execute_result", "display_data", "pyout"):
        data = out.get("data") if isinstance(out.get("data"), dict) else out
        text = joined(
            data.get("text/plain") if "text/plain" in data else data.get("text")
        )
    elif kind in ("error", "pyerr"):
        text = f"{out.get('ename', 'Error')}: {out.get('evalue', '')}".strip()
    else:
        text = ""
    lines = text.rstrip().splitlines()
    return "\n".join(lines[:LINES]) + (
        f"\n... {len(lines) - LINES} more lines" if len(lines) > LINES else ""
    )


def cells_of(nb: dict) -> list[dict]:
    if isinstance(nb.get("cells"), list):
        return nb["cells"]
    sheets = nb.get("worksheets")
    return (
        sheets[0].get("cells", [])
        if isinstance(sheets, list) and sheets and isinstance(sheets[0], dict)
        else []
    )


def convert(data: bytes) -> str | None:
    nb = json.loads(data.decode("utf-8-sig"))
    if not isinstance(nb, dict) or not cells_of(nb):
        return None
    meta = nb.get("metadata") if isinstance(nb.get("metadata"), dict) else {}
    spec = meta.get("kernelspec") if isinstance(meta.get("kernelspec"), dict) else {}
    info = (
        meta.get("language_info") if isinstance(meta.get("language_info"), dict) else {}
    )
    title = (
        meta.get("title") or spec.get("display_name") or spec.get("name") or "notebook"
    )
    lang = ", ".join(
        x for x in (spec.get("name"), info.get("name") or spec.get("language")) if x
    )
    out = [f"notebook: {title}" + (f" ({lang})" if lang else "") + "\n\n"]
    for n, cell in enumerate(cells_of(nb), 1):
        if not isinstance(cell, dict):
            continue
        kind = cell.get("cell_type", "raw")
        source = joined(
            cell.get("source") if "source" in cell else cell.get("input")
        ).rstrip()
        outputs = [
            t
            for t in (
                output_text(o) for o in cell.get("outputs", []) if isinstance(o, dict)
            )
            if t
        ]
        if not source and not outputs:
            continue
        block = f"cell {n} ({kind})\n{source}\n" if source else f"cell {n} ({kind})\n"
        for text in outputs:
            block += f"output:\n{text}\n"
        out.append(block + "\n")
    return "".join(out) if len(out) > 1 else None


EXTS = (".ipynb",)
ERRORS = (
    OSError,
    UnicodeDecodeError,
    ValueError,
    KeyError,
    TypeError,
    AttributeError,
    IndexError,
)

USAGE = "usage: jupyter.py mirror --from FOLDER --to MIRROR"


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
