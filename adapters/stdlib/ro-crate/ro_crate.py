"""ro_crate.py: a box snapshot as an RO-Crate research object. Python 3.9+.

    python adapters/stdlib/ro-crate/ro_crate.py --box DIR --to FOLDER [--licence ID] [--now TS]

An RO-Crate is a folder of files with one description of them, written in
JSON-LD, that repositories such as Zenodo and tools that read research
objects understand. This writes FOLDER/willow-crate-YYYYMMDD-HHMMSS.zip,
holding:

    ro-crate-metadata.json   the description: every file with its SHA-256,
                             size, kind and licence
    files/...                your folder's files, as they are
    record.jsonl             the record, so the chain can be checked
    proposals/..., written/...   the suggestions and the answers you approved

and says what it wrote and where. The description names the record's tip
(its last row's hash) and the number of rows, so the crate pins the record
as it stood; `kernel.py verify` on a box restored from it is the check.

--licence ID names the licence every file is offered under, an SPDX
identifier (CC-BY-4.0, CC0-1.0) or a link; without one the crate says none
and so does the output: a repository will ask you. It is copied onto each
file and onto the crate, and is never guessed. Hidden files and folders are
left out, as the kernel leaves them out of a question.

The box's settings (which name where your key lives) and your key are not in
it, and it never reads your key. Names are written as links, a space as %20. A FOLDER inside the box or your files, or
the key's own folder, is refused. The copy is checked before it is kept:
every file's bytes and hash match the description, or it is deleted and the
run fails. The same box and --now give the same bytes.

Exit codes, the kernel's: 0 written and checked; 2 refused (a record that
doesn't verify, a FOLDER it won't use, a bad command line).
"""

from __future__ import annotations

import hashlib
import io
import json
import mimetypes
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote, unquote

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

CRATE = "https://w3id.org/ro/crate/1.1"
LICENCE = re.compile(r"^(?:[A-Za-z0-9][A-Za-z0-9.+-]*|https?://\S+)$")
KEEP = ("record.jsonl", "proposals", "written")


def licence_id(value: str) -> str:
    return (
        value
        if value.startswith(("http://", "https://"))
        else f"https://spdx.org/licenses/{value}.html"
    )


def payload(box: Path) -> list[tuple[str, Path]]:
    """(the name in the crate, the file) for everything the crate holds."""
    out: list[tuple[str, Path]] = []
    pile = Path(kernel.config(box)["pile"])
    for p in sorted(pile.rglob("*")):
        rel = p.relative_to(pile)
        if p.is_file() and not any(part.startswith(".") for part in rel.parts):
            out.append((f"files/{rel.as_posix()}", p))
    for name in KEEP:
        p = box / name
        if p.is_file():
            out.append((name, p))
        elif p.is_dir():
            out += [
                (q.relative_to(box).as_posix(), q)
                for q in sorted(p.rglob("*"))
                if q.is_file()
            ]
    return out


def describe(
    box: Path,
    rows: list[dict],
    items: list[tuple[str, Path]],
    licence: str | None,
    date: str,
) -> dict:
    lic = {"@id": licence_id(licence)} if licence else None
    files = []
    for name, p in items:
        data = p.read_bytes()
        entry = {
            "@id": quote(name, safe="/"),
            "@type": "File",
            "name": Path(name).name,
            "contentSize": str(len(data)),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        kind = mimetypes.guess_type(name)[0] or (
            "application/x-ndjson" if name.endswith(".jsonl") else None
        )
        if kind:
            entry["encodingFormat"] = kind
        if lic:
            entry["license"] = lic
        files.append(entry)
    root = {
        "@id": "./",
        "@type": "Dataset",
        "name": "A Willow box",
        "description": "A snapshot of a willow box: the files it searches, its record, the suggestions handed in and the answers approved.",
        "datePublished": date,
        "hasPart": [{"@id": f["@id"]} for f in files],
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "record rows", "value": len(rows)},
            {
                "@type": "PropertyValue",
                "name": "record tip",
                "value": rows[-1]["hash"] if rows else kernel.GENESIS,
            },
        ],
    }
    if lic:
        root["license"] = lic
    graph = [
        {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "conformsTo": {"@id": CRATE},
            "about": {"@id": "./"},
        },
        root,
        *files,
    ]
    if licence:
        graph.append({"@id": lic["@id"], "@type": "CreativeWork", "name": licence})
    return {"@context": "https://w3id.org/ro/crate/1.1/context", "@graph": graph}


def why_not(box: Path, to: Path) -> str | None:
    cfg = kernel.config(box)
    to = to.resolve()
    for inside, what in (
        (box.resolve(), "the box"),
        (Path(cfg["pile"]).resolve(), "your files"),
    ):
        if to == inside or inside in to.parents:
            return f"{to} is inside {what}; a snapshot inside what it copies isn't one"
    if to == Path(cfg["key"]).resolve().parent:
        return f"{to} is where your key is; keep the crate somewhere else"
    return None


def check(zip_path: Path, items: list[tuple[str, Path]]) -> str | None:
    """Why the crate doesn't hold, or None: every file's bytes and the hash described."""
    with zipfile.ZipFile(zip_path) as z:
        meta = json.loads(z.read("ro-crate-metadata.json"))
        got = {
            n: hashlib.sha256(z.read(n)).hexdigest()
            for n in z.namelist()
            if n != "ro-crate-metadata.json"
        }
    said = {unquote(e["@id"]): e["sha256"] for e in meta["@graph"] if "sha256" in e}
    want = {name: hashlib.sha256(p.read_bytes()).hexdigest() for name, p in items}
    if got != want or said != want:
        odd = sorted(
            {
                n
                for n in set(got) | set(want)
                if got.get(n) != want.get(n) or said.get(n) != want.get(n)
            }
        )
        return f"the crate differs from the box: {', '.join(odd[:3])}"
    return None


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--to", "--licence", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    lic = opts.get("--licence")
    if (
        not opts.get("--box")
        or not opts.get("--to")
        or args
        or ("--licence" in opts and not (lic and LICENCE.match(lic)))
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box, to = Path(opts["--box"]), Path(opts["--to"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print(
            "refused: the record doesn't verify, so it isn't copied:",
            *breaks,
            sep="\n  ",
            file=sys.stderr,
        )
        return kernel.REFUSED
    if why := why_not(box, to):
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    ts = opts.get("--now") or kernel.now()
    stamp = ts[:19].replace("-", "").replace(":", "").replace("T", "-")
    out = to / f"willow-crate-{stamp}.zip"
    if out.exists():
        print(f"refused: {out} is already there; it isn't overwritten", file=sys.stderr)
        return kernel.REFUSED
    items = payload(box)
    meta = (
        json.dumps(
            describe(box, rows, items, lic, ts[:10]),
            indent=1,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            zipfile.ZipInfo("ro-crate-metadata.json", (1980, 1, 1, 0, 0, 0)),
            meta,
            zipfile.ZIP_DEFLATED,
        )
        for name, p in items:
            z.writestr(
                zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0)),
                p.read_bytes(),
                zipfile.ZIP_DEFLATED,
            )
    to.mkdir(exist_ok=True)
    out.write_bytes(buf.getvalue())
    if why := check(out, items):
        out.unlink()
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    print(
        f"wrote {out}: {len(items)} files, {len(rows)} rows; licence: {lic or 'none given'}"
    )
    if not lic:
        print(
            "note: no --licence given, so the crate names none; a repository will ask for one",
            file=sys.stderr,
        )
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
