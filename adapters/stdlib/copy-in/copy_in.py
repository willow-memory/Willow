"""copy_in.py: new files from another folder or device copied into yours,
each logged with its SHA-256; nothing deleted, a changed file a second copy.
Python 3.9+.

    python adapters/stdlib/copy-in/copy_in.py --from FOLDER --to DIR [--skip PREFIX ...]
        [--dry-run] [--json]

FOLDER is what came from the other device, however it came: a phone's
Download pulled over a cable, a mounted card, a synced folder. DIR is yours,
the folder your stacks read. Each file in FOLDER whose bytes DIR hasn't had
before is copied to DIR/<its path> and logged in DIR/copied-in.jsonl, one
line a copy: its path in FOLDER, where it went in DIR, its size and its
sha256. The copy is read back and must hash the same, or it is said.

**The log is the memory.** A file whose sha256 is in the log is "already
in" and not copied again, wherever it sits in FOLDER and whether or not its
copy is still in DIR: what you deleted from DIR stays deleted. Files with
the same bytes twice in FOLDER are copied once.

**Nothing is deleted, nothing replaced.** A file gone from FOLDER is left
in DIR. A file with new bytes at a path DIR already holds (it changed on the
other device, or another file had the name) goes beside it as
`name (2).ext`, then (3), so the first copy stays. A file in DIR with the
same bytes at the same path, never logged, is logged as "already there".

A path under a --skip PREFIX is passed over and counted. A link is never
followed, and a file that can't be read is said. --dry-run says the same
and writes nothing.

It prints a report (the shape every report add-on shares), and --json the
same report as one JSON object.

Exit codes, the kernel's: 0 every new file copied and checked (populated),
or nothing in FOLDER (empty); 42 something wasn't done (a file that couldn't
be read, a copy that didn't hash the same, a link passed over); 2 refused (a
bad command line, FOLDER not a folder that's there, DIR a file or its parent
missing, one inside the other, a log line that isn't one this wrote).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = (
    "usage: copy_in.py --from FOLDER --to DIR [--skip PREFIX ...] [--dry-run] [--json]"
)
LOG = "copied-in.jsonl"


def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report: its state, one line said, and each group's rows (where,
    what); a group named None comes first and has no heading."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups if rows]}  # fmt: skip


def report_text(doc: dict) -> str:
    """A report as every report add-on prints it: the same twenty lines each
    keeps, held to this one by test_contract.py."""
    rows = [r for g in doc["groups"] for r in g["rows"]]
    w = min(max((len(r["where"]) for r in rows), default=0), 60)
    out = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    for g in doc["groups"]:
        if g["name"] is not None:
            out.append(f"## {g['name']}")
        out += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(out)


def say(doc: dict, as_json: bool) -> None:
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def skipped_by(path: str, skip: list[str]) -> bool:
    """Whether a path is under one of the --skip prefixes."""
    return any(
        path == s.rstrip("/") or path.startswith(s.rstrip("/") + "/") for s in skip
    )


def logged(dst: Path) -> dict[str, str] | None:
    """{sha256: where it went} from DIR's log; None when a line isn't one
    this wrote."""
    log = dst / LOG
    if not log.is_file():
        return {}
    out: dict[str, str] = {}
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            return None
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("sha256"), str)
            or not isinstance(row.get("to"), str)
        ):
            return None
        out.setdefault(row["sha256"], row["to"])
    return out


def files(src: Path) -> tuple[list[str], list[str]]:
    """(each file's path in FOLDER, each link's), sorted; a link is never
    followed, into a folder or to a file."""
    found: list[str] = []
    links: list[str] = []

    def walk(folder: Path) -> None:
        for p in sorted(folder.iterdir()):
            rel = p.relative_to(src).as_posix()
            if p.is_symlink():
                links.append(rel)
            elif p.is_dir():
                walk(p)
            elif p.is_file():
                found.append(rel)

    walk(src)
    return found, links


def free(dst: Path, rel: str, taken: set[str]) -> str:
    """Where a new file at `rel` goes in DIR: its own path while nothing is
    there, else `name (2).ext`, (3), and on, beside it."""
    if not (dst / rel).exists() and rel not in taken:
        return rel
    p = PurePosixPath(rel)
    stem, ext = (p.stem, p.suffix) if p.stem else (p.name, "")
    n = 2
    while True:
        cand = str(p.with_name(f"{stem} ({n}){ext}"))
        if not (dst / cand).exists() and cand not in taken:
            return cand
        n += 1


def copy_in(src: Path, dst: Path, skip: list[str], dry: bool, known: dict) -> dict:
    found, links = files(src)
    copied: list = []
    there: list = []
    beside: list = []
    unread: list = []
    unchecked: list = []
    already = skipped = 0
    seen: dict[str, str] = {}  # sha256 -> path in FOLDER, this run
    taken: set[str] = set()  # DIR paths a dry run would have used
    lines: list = []
    for rel in found:
        if skipped_by(rel, skip):
            skipped += 1
            continue
        source = src / rel
        try:
            digest = sha(source)
        except OSError as e:
            unread.append((rel, f"couldn't be read: {type(e).__name__}"))
            continue
        if digest in known:
            already += 1
            continue
        if digest in seen:
            there.append((rel, f"the same bytes as {seen[digest]}, copied once"))
            continue
        seen[digest] = rel
        target = dst / rel
        if target.is_file() and sha(target) == digest:
            there.append((rel, "already there, now logged"))
            lines.append({"from": rel, "to": rel, "sha256": digest,
                          "size": source.stat().st_size})  # fmt: skip
            continue
        to = free(dst, rel, taken)
        taken.add(to)
        verb = "would copy" if dry else "copied"
        if to == rel:
            copied.append((rel, verb))
        else:
            beside.append((rel, f"{verb} beside it, as {to}: different bytes"))
        if dry:
            continue
        (dst / to).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dst / to)
        if sha(dst / to) != digest:
            unchecked.append((rel, f"the copy at {to} doesn't hash the same"))
            continue
        lines.append({"from": rel, "to": to, "sha256": digest,
                      "size": source.stat().st_size})  # fmt: skip
    if lines and not dry:
        with open(dst / LOG, "a", encoding="utf-8") as f:
            for line in lines:
                f.write(json.dumps(line, ensure_ascii=False, sort_keys=True) + "\n")
    not_done = unread + unchecked + [(r, "a link, not followed") for r in links]
    verb = "would copy" if dry else "copied"
    said = (
        f"{verb} {len(copied) + len(beside)} new files, {already} already in, "
        f"{len(there)} there already, {len(not_done)} not done, {skipped} skipped"
    )
    groups = [
        (verb, copied),
        ("beside an earlier copy", beside),
        ("there already", there),
        ("not done", not_done),
    ]
    state = "populated" if found or links else "empty"
    return report("copy-in", state, said, groups)


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    dry = "--dry-run" in argv
    argv = [a for a in argv if a not in ("--json", "--dry-run")]
    if len(argv) % 2:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    pairs = list(zip(argv[::2], argv[1::2]))
    opts = {k: v for k, v in pairs if k != "--skip"}
    skip = [v for k, v in pairs if k == "--skip"]
    if sorted(opts) != ["--from", "--to"] or len(opts) + len(skip) != len(pairs):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    src, dst = Path(opts["--from"]), Path(opts["--to"])
    if not src.is_dir():
        print(f"refused: not a folder that's there: {src}", file=sys.stderr)
        return kernel.REFUSED
    if dst.exists() and not dst.is_dir():
        print(f"refused: not a folder: {dst}", file=sys.stderr)
        return kernel.REFUSED
    if not dst.resolve().parent.is_dir():
        print(f"refused: the folder {dst} would go in isn't there", file=sys.stderr)
        return kernel.REFUSED
    if within(dst.resolve(), src.resolve()) or within(src.resolve(), dst.resolve()):
        print("refused: FOLDER and DIR must not be inside one another", file=sys.stderr)
        return kernel.REFUSED
    known = logged(dst)
    if known is None:
        print(f"refused: {dst / LOG} has a line this didn't write", file=sys.stderr)
        return kernel.REFUSED
    out = copy_in(src, dst, skip, dry, known)
    say(out, as_json)
    waits = any(g["name"] == "not done" for g in out["groups"])
    return kernel.ESCALATE if waits else kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
