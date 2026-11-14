"""new_kinds.py: kinds of file in your folders that no step of your stack reads yet, each with the readers that took some of them when tried on a few. Python 3.9+.

    python adapters/stdlib/new-kinds/new_kinds.py --from FOLDER [--from FOLDER]... [--stack STACKFILE] [--leave .EXT[,.EXT]]... [--json]

    new-kinds: populated, 2 kinds no step reads, of 6 in 1 folder: .gpx, .pdf
    ## a reader knows their shape
      .gpx  12 files; places took 4 of 4, strava took 1 of 4
    ## the kernel can't read them
      .pdf  3 files; pdf took 3 of 3

A stack is set up for the files its folders held then. When a new kind of
file arrives (a GPX from a watch, an export from an app), nothing says so:
the kernel reads it as plain text or skips it, and the reader that would
read it well isn't in the stack. Run as a step of the stack, this says so
on every run, until a step reads the kind or you leave it.

It counts the files in each FOLDER by kind (extension, lowercased; hidden
files and folders skipped, as the kernel skips them). A kind is left out
when a step in STACKFILE is a reader whose card says it reads it, or when
`--leave` names it. For each kind left, the readers whose cards say they
read it are tried: each runs its own `mirror --from --to` on copies of up
to four of its files, spread over them in name order, beside a file of the
kind with nothing in it, in scratch removed after. A reader that took some
of yours and not the nonsense knows their shape. One that took the
nonsense too reads any file of the kind (json-paths takes any .json), and
is named only beside the rest. A kind the kernel reads as text, that no
reader knows the shape of, is fine as it is and isn't a row.

The readers are the ones beside this add-on (its own adapters folder), and
only those whose card says `network: none`. Only kinds and counts are said,
never a file's name or a line of it.

Exit codes: 0 `empty` (every kind is read by a step, read as text, or left);
42 `populated` (a kind waits on you: add its reader, or leave it); 2
refused (a FOLDER that isn't one, a stack file that names no step, or a bad
command line).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

NAME = "new-kinds"
USAGE = (
    "usage: new_kinds.py --from FOLDER [--from FOLDER]... [--stack STACKFILE]"
    " [--leave .EXT[,.EXT]]... [--json]"
)
ADAPTERS = Path(__file__).resolve().parents[2]
#: files of a kind a reader is tried on, and how long it is given for them
SAMPLE = 4
TRY_SECONDS = 30
NO_KIND = "(no extension)"


# ── the report: the shape every report add-on prints (ci/README.md) ─────────
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


# ── the readers, from their cards ───────────────────────────────────────────
def card(folder: Path) -> dict:
    """A card's header fields, as `key: value` lines in its README's
    willow-addon comment; {} for a folder with none."""
    try:
        text = (folder / "README.md").read_text(encoding="utf-8")
    except OSError:
        return {}
    if not text.startswith("<!-- willow-addon"):
        return {}
    head = text.split("-->", 1)[0].splitlines()[1:]
    return {k.strip(): v.strip() for k, _, v in (ln.partition(":") for ln in head) if k.strip()}  # fmt: skip


def kinds_read(said: str) -> list[str]:
    """A card's `reads`: kinds by extension and files by name, lowercased;
    `none` reads no kind."""
    got = [k.strip().lower() for k in said.split(",") if k.strip()]
    return [] if got == ["none"] else got


def main_of(folder: Path) -> Path | None:
    """A reader's one script: the .py in its folder that runs as a program."""
    mains = [p for p in sorted(folder.glob("*.py"))
             if not p.name.startswith("test_") and "__main__" in p.read_text(encoding="utf-8")]  # fmt: skip
    return mains[0] if len(mains) == 1 else None


def readers(adapters: Path = ADAPTERS) -> dict:
    """Every built reader beside this add-on, by name: what it reads, and
    its script when it can be tried here (it reads no network)."""
    out = {}
    for kind in ("stdlib", "deps"):
        base = adapters / kind
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            c = card(d) if d.is_dir() else {}
            if c.get("role") != "reads":
                continue
            script = main_of(d) if c.get("network") == "none" else None
            out[d.name] = {"reads": kinds_read(c.get("reads", "")), "script": script,
                           "needs": bool(c.get("needs"))}  # fmt: skip
    return out


# ── trying a reader on a few files ──────────────────────────────────────────
def sample(files: list[Path]) -> list[Path]:
    """Up to SAMPLE of a kind's files, spread over them in name order, so
    the same folder is always tried on the same ones."""
    files = sorted(files)
    if len(files) <= SAMPLE:
        return files
    step = (len(files) - 1) / (SAMPLE - 1)
    return [files[round(i * step)] for i in range(SAMPLE)]


def nonsense(ext: str) -> bytes:
    """A file of the kind with no shape in it: the control a reader is tried
    on beside your files. One that takes it reads any file of the kind."""
    return b'{"willow": 1}\n' if ext in (".json", ".jsonl", ".ndjson") else b"willow\n"


def took_by(script: Path, src: Path, dst: Path) -> set:
    """Which of the tried folders a reader wrote text for: src holds each
    file in a folder of its own, so what it wrote says which it took. A
    reader that refuses, fails or runs past TRY_SECONDS took none."""
    try:
        r = subprocess.run([sys.executable, str(script), "mirror", "--from", str(src),
                            "--to", str(dst)], capture_output=True, cwd=src.parent,
                           timeout=TRY_SECONDS)  # fmt: skip
    except (OSError, subprocess.TimeoutExpired):
        return set()
    if r.returncode != 0 or not dst.is_dir():
        return set()
    wrote = {f.relative_to(dst).parts[0] for f in dst.rglob("*") if f.is_file()}
    return {w for w in wrote if (src / w).is_dir()}


def trial(ext: str, files: list[Path], scripts: dict) -> dict:
    """The readers in `scripts` (name: script), each tried on copies of up
    to SAMPLE of `files` beside a file of the kind with nothing in it, in
    scratch removed after. `fits`: the ones that took some of yours and not
    the nonsense; `any`: the ones that took the nonsense too. Each is
    {name, took}, most taken first, then by name; `tried` is how many."""
    out: dict = {"tried": 0, "fits": [], "any": []}
    if not scripts or not files:
        return out
    some = sample(files)
    out["tried"] = len(some)
    with tempfile.TemporaryDirectory(prefix="willow-new-kinds-") as tmp:
        src = Path(tmp) / "from"
        for i, f in enumerate(some):
            (src / str(i)).mkdir(parents=True)
            shutil.copyfile(f, src / str(i) / f.name)
        (src / "control").mkdir()
        (src / "control" / ("willow" + ext)).write_bytes(nonsense(ext))
        with ThreadPoolExecutor(max_workers=os.cpu_count() or 2) as pool:
            runs = {n: pool.submit(took_by, s, src, Path(tmp) / ("to-" + n))
                    for n, s in sorted(scripts.items())}  # fmt: skip
            took = {n: r.result() for n, r in runs.items()}
    for n, t in took.items():
        mine = len(t - {"control"})
        if mine:
            out["any" if "control" in t else "fits"].append({"name": n, "took": mine})
    for k in ("fits", "any"):
        out[k].sort(key=lambda r: (-r["took"], r["name"]))
    return out


# ── the folders, by kind ────────────────────────────────────────────────────
def kinds_in(folders: list[Path]) -> dict:
    """Each kind's files, and whether the kernel reads any of them as they
    are (UTF-8 text, not over its size): {ext: {"files": [...], "text": n}}.
    Hidden files and folders are skipped, as the kernel skips them."""
    out: dict = {}
    for root in folders:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
            for fn in sorted(filenames):
                if fn.startswith("."):
                    continue
                p = Path(dirpath) / fn
                if not p.is_file():
                    continue
                ext = p.suffix.lower() or NO_KIND
                k = out.setdefault(ext, {"files": [], "text": 0})
                k["files"].append(p)
                k["text"] += as_text(p)
    return out


def as_text(p: Path) -> bool:
    """Whether the kernel reads a file as it is: UTF-8, no NUL in its
    first bytes, not over its size."""
    try:
        if p.stat().st_size > kernel.MAX_FILE:
            return False
        raw = p.read_bytes()
        if b"\0" in raw[: kernel.SNIFF]:
            return False
        raw.decode("utf-8")
        return True
    except (OSError, UnicodeDecodeError):
        return False


def stack_readers(text: str, known: dict) -> tuple[list[str], str | None]:
    """The readers a stack file runs as steps: its `- NAME -- ...` lines,
    as the stack add-on reads them, kept when NAME is a reader here."""
    steps = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("- "):
            name = line[2:].partition(" -- ")[0].strip()
            if name and "/" not in name:
                steps.append(name)
    if not steps:
        return [], "the stack file names no steps"
    return sorted({s for s in steps if s in known}), None


def plural(n: int, word: str) -> str:
    return f"{n:,} {word}" + ("" if n == 1 else "s")


def look(folders: list[Path], stacked: list[str], leave: set, known: dict) -> dict:
    """The report: each kind no step reads and not left, with the readers
    that took some of it."""
    kinds = kinds_in(folders)
    read = {k for n in stacked for k in known[n]["reads"]}
    fits, cant, none_yet, waiting = [], [], [], []
    for ext in sorted(kinds, key=lambda e: (-len(kinds[e]["files"]), e)):
        k = kinds[ext]
        if ext in read or ext in leave:
            continue
        files = [p for p in k["files"] if p.name.lower() not in read]
        if not files:
            continue
        cards = {n: r for n, r in known.items() if ext in r["reads"]}
        scripts = {n: r["script"] for n, r in cards.items() if r["script"]}
        t = trial(ext, files, scripts) if ext != NO_KIND else {"tried": 0, "fits": [], "any": []}  # fmt: skip
        took = [f"{r['name']} took {r['took']} of {t['tried']}" for r in t["fits"]]
        loose = [r["name"] for r in t["any"]]
        tail = f"; any {ext} is taken by {', '.join(loose)}" if loose else ""
        n = plural(len(files), "file")
        if k["text"]:
            if took:
                fits.append((ext, f"{n}; {', '.join(took)}{tail}"))
                waiting.append(ext)
            continue
        if took:
            cant.append((ext, f"{n}; {', '.join(took)}"))
        elif cards:
            by = [
                c + (" (needs its install)" if cards[c]["needs"] else "")
                for c in sorted(cards)
            ]
            cant.append(
                (ext, f"{n}; none of {t['tried']} tried taken by {', '.join(by)}")
            )
        else:
            none_yet.append((ext, f"{n}; no reader here says it reads them"))
        waiting.append(ext)
    where = plural(len(folders), "folder")
    if not waiting:
        return report(NAME, "empty", f"every kind of {len(kinds)} in {where} is read by a step, read as text, or left", [])  # fmt: skip
    named = ", ".join(waiting[:8]) + (
        f" and {len(waiting) - 8} more" if len(waiting) > 8 else ""
    )
    said = f"{plural(len(waiting), 'kind')} no step reads, of {len(kinds)} in {where}: {named}"
    return report(NAME, "populated", said, [
        ("a reader knows their shape", fits),
        ("the kernel can't read them", cant),
        ("no reader for them yet", none_yet),
    ])  # fmt: skip


# ── the command line ────────────────────────────────────────────────────────
def refuse(why: str) -> int:
    print(f"refused: {why}\n{USAGE}", file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    folders, stack, leave, as_json = [], None, set(), False
    it = iter(argv)
    for a in it:
        if a == "--json":
            as_json = True
        elif a in ("--from", "--stack", "--leave"):
            v = next(it, None)
            if v is None or v.startswith("--"):
                return refuse(f"{a} needs a value")
            if a == "--from":
                folders.append(Path(v).expanduser())
            elif a == "--stack":
                stack = Path(v).expanduser()
            else:
                for e in v.split(","):
                    e = e.strip().lower()
                    if e and not e.startswith("."):
                        return refuse(f"--leave takes kinds as .ext, not {e!r}")
                    if e:
                        leave.add(e)
        else:
            return refuse(f"unknown option {a!r}")
    if not folders:
        return refuse("no --from FOLDER")
    for f in folders:
        if not f.is_dir():
            return refuse(f"{f} is not a folder")
    known = readers()
    stacked: list[str] = []
    if stack is not None:
        try:
            text = stack.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            return refuse(f"can't read the stack file: {e}")
        stacked, why = stack_readers(text, known)
        if why:
            return refuse(why)
    doc = look(folders, stacked, leave, known)
    say(doc, as_json)
    return kernel.ALIVE if doc["state"] == "empty" else kernel.ESCALATE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
