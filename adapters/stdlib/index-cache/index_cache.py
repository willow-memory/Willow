"""index_cache.py: keep a folder's scan index between runs, rebuilt only when
the folder changed. Python 3.9+.

    python adapters/stdlib/index-cache/index_cache.py --from FOLDER --to INDEX
    python adapters/stdlib/index-cache/index_cache.py --from @LIST --to INDEX
    python adapters/stdlib/index-cache/index_cache.py --box BOX --to INDEX

`scan index` reads the whole folder to build an index; on a big folder that is
the slow step. But a folder usually hasn't changed since last time, and then
the index already on disk is still the right one. This keeps a small manifest
beside the index -- each read file's path and the SHA-256 of its text -- and on
each run hashes the folder's files and compares:

- **unchanged** -- every file the index was built from is still there with the
  same hash, and no new file was added: the index is current, so nothing is
  rebuilt and no passage is re-read. Ask it with `scan`.
- **changed** -- a file was added, edited or removed: it rebuilds the index
  (through `scan`), writes the new manifest, and says what moved.

So the index is kept between runs and a question doesn't re-read the folder
unless the folder changed. The files it hashes are exactly the ones the kernel
would read into the index (text, UTF-8, not hidden, under the size cap); a
binary or a dotfile changing never forces a rebuild.

`--from @LIST` keeps the index of a list's files where they are kept, as a
box laid with `kernel.py init --from NAME=@LIST` reads them (CONST-VI-9):
one path a line, each named by its path from the folder the files share,
the kernel's own `list_chunks`. A listed file that is gone is read as
nothing, as a deleted one is, and counts as removed.

`--box BOX` keeps the index of everything the box reads: its pile folder and
each of its sources, folder or list, named as the kernel's `pile_of_box`
names them (NAME/ and the path). So a box laid from several places is asked
from one index with the same passages its bite reads. For a box with only a
pile, it is the pile folder's index, manifest and all. It reads the box's
kernel.json and nothing else of the box: never its record or its key.

It reads the folder and writes only under `--to` (the index and its manifest);
it writes no box, reads no key, and reaches no network. An index made by
another kernel.py is rebuilt, since its passages were the other kernel's. Exit
codes, the kernel's: 0 the index is current or was rebuilt; 42 the folder has
nothing to read; 2 refused (a bad command line, or a `--from` that is not a
folder, a `--from @LIST` that is not a list of files, or a `--box` that is
not a box).
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "batch-ask"))
import kernel  # noqa: E402
import scan  # noqa: E402

FORMAT = "willow-index-cache/1"
CACHE = "cache.json"  # the manifest, beside scan's own index files


#: a file's details on disk, kept beside its hash: when all four are as they
#: were, its text is the text that was hashed, and it isn't read again
Stat = list  # [size, mtime_ns, ctime_ns, inode]
#: a file changed this close to when the last check began may have changed
#: again inside the clock's tick with the same details: it is read again
RACY_NS = 2_000_000_000


def stat_of(p) -> Stat | None:
    try:
        st = os.stat(p)
    except OSError:
        return None
    return [st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_ino]


def hidden(rel: str) -> bool:
    return any(part.startswith(".") for part in rel.split(os.sep))


def folder_files(folder: Path) -> list[tuple[str, str]]:
    """(name, file) for the files under `folder` the kernel reads, by name:
    kernel.chunks's walk, hidden folders and files left out. Walked as
    strings (os.walk), never a Path a file: on thousands of files the Path
    objects were most of a check's time."""
    top, out = str(folder), []
    for here, dirs, files in os.walk(top):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in files:
            if not name.startswith("."):
                full = os.path.join(here, name)
                if os.path.isfile(full):
                    out.append((os.path.relpath(full, top), full))
    return sorted(out)


def listed_paths(lst: Path) -> list[str]:
    """`listed`, as strings: each folder's real path found once, and a file's
    own only when it is a link, which is the real path of each."""
    out: list[str] = []
    seen: set[str] = set()
    base = str(lst.parent)
    real: dict[str, str] = {}
    for line in lst.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        full = os.path.join(base, line)  # an absolute line stays as it is
        if ".." in full.split(os.sep) or os.path.basename(full) in ("", "."):
            f = os.path.realpath(full)
        else:
            d, name = os.path.split(full)
            if d not in real:
                real[d] = os.path.realpath(d)
            f = os.path.join(real[d], name)
            if os.path.islink(f):
                f = os.path.realpath(f)
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def listed(lst: Path) -> list[Path]:
    """The files a list names, as the kernel's `listed` reads them (in its
    order, each once, a relative path from the list's folder), each once by a
    set: the kernel's looks back along the list for each line, which on a
    list of thousands is most of a check's time. The kernel's stays its own."""
    return [Path(f) for f in listed_paths(lst)]


def list_files(lst: Path) -> list[tuple[str, str]]:
    """(name, file) for a list's files, named as the kernel's `list_chunks`
    names them: by path from the folder the listed files share."""
    files = listed_paths(lst)
    if not files:
        return []
    root = os.path.commonpath([os.path.dirname(f) for f in files])
    cut = len(root) + (0 if root.endswith(os.sep) else 1)
    return [(f[cut:], f) for f in files if not hidden(f[cut:])]


def box_files(cfg: dict) -> list[tuple[str, str]]:
    """(name, file) for everything a box reads, named as the kernel's
    `pile_of_box` names its passages: the pile folder's paths as they are,
    then each source's as its name, a slash, and its path."""
    out = folder_files(Path(cfg["pile"])) if "pile" in cfg else []
    for name, at in sorted(kernel.sources(cfg).items()):
        is_list = cfg["sources"][name].startswith("@")
        part = list_files(at) if is_list else folder_files(at)
        out += [(f"{name}/{rel}", p) for rel, p in part]
    return out


def within(p: str, folder: str) -> bool:
    return p == folder or p.startswith(folder.rstrip(os.sep) + os.sep)


def hashed(
    files: list[tuple[str, str]], known: dict | None = None
) -> tuple[dict[str, str], dict[str, list]]:
    """({name: SHA-256 of its text}, {name: [stat, hash or None]}) for the
    files the kernel reads into an index: UTF-8 text with no NUL in its first
    bytes and under the size cap, the same filter as kernel.chunks, hashing
    the text so a rebuild follows exactly the changes the index would see. A
    file whose details are as `known` holds them is not read: its hash, or
    that it was no text, is taken from there."""
    known = known or {}
    out: dict[str, str] = {}
    seen: dict[str, list] = {}
    for rel, p in files:
        st = stat_of(p)
        if st is None:
            continue
        was = known.get(rel)
        if was is not None and was[0] == st:
            h = was[1]
        else:
            try:
                with open(p, "rb") as fh:
                    raw = fh.read()
                if len(raw) > kernel.MAX_FILE or b"\0" in raw[: kernel.SNIFF]:
                    h = None
                else:
                    h = kernel.h256(raw.decode("utf-8"))
            except UnicodeDecodeError:
                h = None
            except OSError:
                continue
        seen[rel] = [st, h]
        if h is not None:
            out[rel] = h
    return out, seen


def manifest(folder: Path, known: dict | None = None) -> dict[str, str]:
    """{relative path: SHA-256 of its text} for the files of `folder` the
    kernel reads into an index (see `hashed`)."""
    return hashed(folder_files(folder), known)[0]


def listed_manifest(lst: Path, known: dict | None = None) -> dict[str, str]:
    """`manifest` for a list's files, named as `list_files` names them."""
    return hashed(list_files(lst), known)[0]


def box_manifest(cfg: dict, known: dict | None = None) -> dict[str, str]:
    """`manifest` for everything a box reads, named as `box_files` names it.
    A box with only a pile has the pile folder's manifest, so an index made
    with --from PILE stays current."""
    return hashed(box_files(cfg), known)[0]


def head_of(index: Path) -> dict | None:
    """The manifest file a past run wrote for `index`, when it is this kind
    and this kernel.py's; else None."""
    try:
        head = json.loads((index / CACHE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if head.get("format") != FORMAT or head.get("kernel") != kernel.VERSION:
        return None
    return head


def built(index: Path) -> dict[str, Stat | None]:
    """scan's own files of `index` by their details on disk."""
    return {f: stat_of(index / f) for f in scan.FILES}


def cached(index: Path) -> dict[str, str] | None:
    """The manifest a past run wrote for `index`, or None when there is none,
    it is of another kind, it was made by another kernel.py, or the index it
    describes is not whole. Then the index is treated as stale. An index whose
    files are as they were when it was written is whole without reading it
    again; one that isn't, or a manifest that kept no details, is read."""
    head = head_of(index)
    if head is None:
        return None
    if not all((index / f).is_file() for f in scan.FILES):
        return None  # made before scan wrote all it writes now: made again once
    if head.get("built") is None or head["built"] != built(index):
        try:
            scan.passages(index)  # the scan index is present and this kernel's
        except (ValueError, OSError):
            return None
    return head.get("files", {})


def known(index: Path) -> dict[str, list]:
    """{name: [stat, hash]} from the last run's manifest, for `hashed`: only
    files whose details were last seen changed before that run began, less
    the racy window, since a file changed while it was being read could look
    the same again. Nothing, when there is no manifest of this kind."""
    head = head_of(index)
    if head is None or not isinstance(head.get("since"), int):
        return {}
    edge = head["since"] - RACY_NS
    return {
        rel: was
        for rel, was in head.get("stats", {}).items()
        if was[0][1] < edge and was[0][2] < edge
    }


def moved(old: dict[str, str], new: dict[str, str]) -> str:
    """How the folder changed, oldest manifest to newest, in one line."""
    added = len(set(new) - set(old))
    removed = len(set(old) - set(new))
    changed = sum(1 for p in set(old) & set(new) if old[p] != new[p])
    return f"+{added} new, ~{changed} changed, -{removed} removed"


def write_head(index: Path, now: dict, seen: dict, since: int) -> None:
    """The manifest beside the index: each file's hash, and its details on
    disk with the time this run began, so the next run reads only what
    moved; and scan's own files' details, so the next run knows the index is
    whole without reading it."""
    head = {"format": FORMAT, "kernel": kernel.VERSION, "files": now,
            "stats": seen, "since": since, "built": built(index)}  # fmt: skip
    (index / CACHE).write_text(kernel.canon(head) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    it = iter(argv)
    for a in it:
        if a in ("--from", "--to", "--box"):
            opts[a] = next(it, "")
        else:
            opts["bad"] = a
    if opts.get("bad") or ("--from" in opts) == ("--box" in opts) or "--to" not in opts:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    given, index = opts.get("--from", ""), Path(opts["--to"]).resolve()
    lst = Path(given[1:]).resolve() if given.startswith("@") else None
    cfg = None
    if "--box" in opts:
        box = Path(opts["--box"]).resolve()
        try:
            cfg = kernel.config(box)
            folders = [str(Path(cfg["pile"]).resolve())] if "pile" in cfg else []
            files: list[str] = []
            for name, at in kernel.sources(cfg).items():
                if cfg["sources"][name].startswith("@"):
                    files += [str(at.resolve()), *listed_paths(at)]
                else:
                    folders.append(str(at.resolve()))
        except (OSError, ValueError, KeyError) as e:
            print(f"refused: {opts['--box']} is not a box ({e})", file=sys.stderr)
            return kernel.REFUSED
        ix = str(index)
        held = (
            within(ix, str(box))
            or any(within(ix, d) or within(d, ix) for d in folders)
            or any(within(f, ix) for f in files)
        )
    elif lst is not None:
        if not lst.is_file():
            print(f"refused: {given[1:]} is not a list of files", file=sys.stderr)
            return kernel.REFUSED
        # only the listed files are read, so an index beside them is fine;
        # one that would hold the list, or a listed file, is not
        held = any(within(f, str(index)) for f in [str(lst), *listed_paths(lst)])
    else:
        folder = Path(given).resolve()
        if not folder.is_dir():
            print(f"refused: {given} is not a folder", file=sys.stderr)
            return kernel.REFUSED
        held = index.is_relative_to(folder) or folder.is_relative_to(index)
    if held:
        print("refused: the index and what it reads can't hold each other",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    if not index.parent.is_dir():
        print(f"refused: {index.parent} is not a folder; make it first",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED

    since = time.time_ns()
    if cfg is not None:
        files = box_files(cfg)
    else:
        files = folder_files(folder) if lst is None else list_files(lst)
    now, seen = hashed(files, known(index))
    before = cached(index)
    if before is not None and before == now:
        print(f"current: {len(now)} files unchanged; the index at {opts['--to']} "
              f"still answers. Ask it with scan.")  # fmt: skip
        head = head_of(index) or {}
        if head.get("stats") != seen:  # details moved, text the same: keep them
            write_head(index, now, seen, since)
        return kernel.ALIVE

    if cfg is not None:
        n = scan.build_from(kernel.pile_of_box(cfg), index)
    elif lst is None:
        n = scan.build(folder, index)
    else:
        n = scan.build_from(kernel.list_chunks(lst), index)
    write_head(index, now, seen, since)
    how = moved(before, now) if before is not None else f"+{len(now)} new"
    print(f"rebuilt {n} passage{'' if n == 1 else 's'} to {opts['--to']} ({how})")
    return kernel.ALIVE if n else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
