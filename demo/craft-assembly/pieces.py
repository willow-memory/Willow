"""pieces.py: sources taken apart into one store of pieces, and rebuilt from it.

    python demo/craft-assembly/pieces.py apart   --from SOURCES --to STORE
    python demo/craft-assembly/pieces.py rebuild --store STORE --to OUT [--only NAME]
    python demo/craft-assembly/pieces.py check   --store STORE --built OUT

SOURCES holds one folder per source, as sources.py fetched them (each a git
checkout; its .git is never a piece). `apart` writes

    STORE/objects/<ab>/<sha256>   each distinct file once, by the SHA-256 of
                                  its bytes (a symlink: of its target)
    STORE/recipes/<name>.json     the source's files: path, git mode, SHA-256,
                                  and the git tree hash they make

and says how many pieces there were and how many two or more sources share.
`rebuild` writes each source back from its recipe and the store alone, and
`check` hashes each rebuilt folder the way git hashes a tree, against the
tree its recipe recorded. Same store, same bytes: recipes are sorted JSON,
and nothing records a time or a machine path.

Exit codes: 0 done, or every tree held; 42 a tree that doesn't hold; 2 refused.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "php2shell"))
import make_trees  # noqa: E402  the repo's own git-tree hasher, held by its tests

MODES = {"100644", "100755", "120000"}


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return 2


def files_of(folder: Path) -> list[tuple[str, str, bytes]]:
    """(path, git mode, bytes) for every file under `folder` but .git, in
    path order; a symlink's bytes are its target, as git stores it."""
    out = []
    for root, dirs, names in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if not (root == str(folder) and d == ".git"))
        for n in sorted(names) + [d for d in dirs if Path(root, d).is_symlink()]:
            p = Path(root) / n
            st = p.lstat()
            if stat.S_ISLNK(st.st_mode):
                mode, data = "120000", os.readlink(p).encode()
            elif stat.S_ISREG(st.st_mode):
                mode = "100755" if st.st_mode & stat.S_IXUSR else "100644"
                data = p.read_bytes()
            else:
                continue
            out.append((p.relative_to(folder).as_posix(), mode, data))
    return sorted(out)


def tree(folder: Path) -> str:
    """The git tree hash of `folder`, leaving out a top-level .git."""
    keep = [e for e in folder.iterdir() if e.name != ".git"]
    if len(keep) == len(list(folder.iterdir())):
        return make_trees.git_tree(folder)
    entries = []
    for p in keep:
        st = p.lstat()
        if stat.S_ISLNK(st.st_mode):
            mode, sha = b"120000", make_trees.obj(b"blob", os.readlink(p).encode())
        elif stat.S_ISDIR(st.st_mode):
            sha = make_trees.git_tree(p)
            if sha == make_trees.EMPTY:
                continue
            mode = b"40000"
        else:
            mode = b"100755" if st.st_mode & stat.S_IXUSR else b"100644"
            sha = make_trees.blob(p.read_bytes())
        key = p.name.encode() + (b"/" if mode == b"40000" else b"")
        entries.append(
            (key, mode + b" " + p.name.encode() + b"\0" + bytes.fromhex(sha))
        )
    return make_trees.obj(b"tree", b"".join(e for _, e in sorted(entries)))


def put(store: Path, data: bytes) -> str:
    sha = hashlib.sha256(data).hexdigest()
    p = store / "objects" / sha[:2] / sha
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".part")
        tmp.write_bytes(data)
        tmp.rename(p)
    return sha


def get(store: Path, sha: str) -> bytes:
    data = (store / "objects" / sha[:2] / sha).read_bytes()
    if hashlib.sha256(data).hexdigest() != sha:
        raise ValueError(f"piece {sha} doesn't hash to its name")
    return data


def dump(obj) -> str:
    return json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def apart(sources: Path, store: Path) -> dict:
    """Every source folder into the store; returns the counts."""
    (store / "recipes").mkdir(parents=True, exist_ok=True)
    owners: dict[str, set[str]] = {}
    sizes: dict[str, int] = {}
    total = 0
    for src in sorted(p for p in sources.iterdir() if p.is_dir()):
        rows = []
        for path, mode, data in files_of(src):
            sha = put(store, data)
            rows.append([path, mode, sha])
            owners.setdefault(sha, set()).add(src.name)
            sizes[sha] = len(data)
            total += 1
        recipe = {"source": src.name, "tree": tree(src), "files": rows}
        (store / "recipes" / f"{src.name}.json").write_text(
            dump(recipe), encoding="utf-8"
        )
    shared = [s for s, who in owners.items() if len(who) > 1]
    return {
        "sources": len({w for who in owners.values() for w in who}),
        "files": total,
        "pieces": len(owners),
        "shared_pieces": len(shared),
        "shared_bytes": sum(sizes[s] for s in shared),
        "piece_bytes": sum(sizes.values()),
    }


def recipe(store: Path, name: str) -> dict:
    return json.loads((store / "recipes" / f"{name}.json").read_text(encoding="utf-8"))


def write(store: Path, rows: list, to: Path) -> None:
    """Files from the store, by recipe rows, into `to`."""
    for path, mode, sha in rows:
        if mode not in MODES or ".." in Path(path).parts or Path(path).is_absolute():
            raise ValueError(f"a recipe row that can't be written: {path}")
        p = to / path
        p.parent.mkdir(parents=True, exist_ok=True)
        data = get(store, sha)
        if mode == "120000":
            os.symlink(data.decode(), p)
        else:
            p.write_bytes(data)
            os.chmod(p, 0o755 if mode == "100755" else 0o644)


def rebuild(store: Path, to: Path, only: str | None = None) -> list[str]:
    names = sorted(p.stem for p in (store / "recipes").glob("*.json"))
    names = [n for n in names if only in (None, n)]
    for name in names:
        write(store, recipe(store, name)["files"], to / name)
    return names


def check(store: Path, built: Path) -> dict[str, bool]:
    return {
        p.stem: (built / p.stem).is_dir()
        and tree(built / p.stem) == recipe(store, p.stem)["tree"]
        for p in sorted((store / "recipes").glob("*.json"))
    }


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("apart", "rebuild", "check"):
        return usage()
    takes = {"apart": {"--from", "--to"}, "rebuild": {"--store", "--to", "--only"},
             "check": {"--store", "--built"}}[argv[0]]  # fmt: skip
    opts, it = {}, iter(argv[1:])
    for a in it:
        v = next(it, "")
        if a not in takes or not v or a in opts:
            return usage()
        opts[a] = v
    if not (takes - {"--only"}) <= opts.keys():
        return usage()
    if argv[0] == "apart":
        src, store = Path(opts["--from"]), Path(opts["--to"])
        if not src.is_dir() or store.resolve().is_relative_to(src.resolve()):
            print(
                "refused: --from must be a folder, and the store outside it",
                file=sys.stderr,
            )
            return 2
        print(dump(apart(src, store)), end="")
        return 0
    store = Path(opts["--store"])
    if not (store / "recipes").is_dir():
        print(f"refused: {store} holds no recipes", file=sys.stderr)
        return 2
    if argv[0] == "rebuild":
        out = Path(opts["--to"])
        if out.exists() and any(out.iterdir()):
            print(
                f"refused: {out} isn't empty; rebuild into a new folder",
                file=sys.stderr,
            )
            return 2
        names = rebuild(store, out, opts.get("--only"))
        print(f"rebuilt {len(names)} sources")
        return 0 if names else 42
    held = check(store, Path(opts["--built"]))
    for name, ok in held.items():
        print(f"{'holds' if ok else 'BROKEN'}  {name}")
    return 0 if all(held.values()) else 42


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
