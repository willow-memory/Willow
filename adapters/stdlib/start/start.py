"""start.py: willow set up in one step. Python 3.9+.

    python adapters/stdlib/start/start.py --pile FOLDER --to DIR
    python adapters/stdlib/start/start.py            (asks, in a terminal)

FOLDER is your files, which willow only ever reads. DIR is where willow
keeps its own things, ~/willow if you're asked and just press Enter. In it:

    DIR/box           the record, made by the kernel's own init
    DIR/key           your key, readable only by you; it approves answers
    DIR/my-words.txt  the starter words list, yours to edit (starter-words)

Then it prints how to open your folder in your browser and a file to
double-click next time (browse's launcher), and how to back up (backup).
A DIR inside your files is refused, or willow would read its own record
as one of them; a DIR that already holds a box is left alone.

Everything it writes is under DIR. The box and the key are written by the
kernel's init, as if you'd typed it.

Exit codes, the kernel's: 0 set up; 2 refused, or a bad command line.
"""

from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import types
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

DEFAULT = "~/willow"


def sibling(folder: str, module: str):
    """Another add-on's module from its source, or None when it was deleted."""
    path = STDLIB / folder / f"{module}.py"
    if not path.is_file():
        return None
    mod = types.ModuleType(f"start_{module}")
    mod.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
    return mod


def quiet(fn, *args) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = fn(*args)
    return code, out.getvalue().strip()


def start(pile: Path, home: Path) -> tuple[int, str]:
    """(exit code, what to tell the person)."""
    pile, home = pile.expanduser().resolve(), home.expanduser().resolve()
    if not pile.is_dir():
        return kernel.REFUSED, f"{pile} isn't a folder"
    if home == pile or pile in home.parents:
        return kernel.REFUSED, (f"{home} is inside your files; willow would read its "
                                "own record as one of them. Choose a folder outside.")  # fmt: skip
    box, key, words = home / "box", home / "key", home / "my-words.txt"
    if (box / "kernel.json").exists():
        browse = STDLIB / "browse" / "browse.py"
        return kernel.REFUSED, (f"{box} is already set up. Open it with:\n\n"
                                f"    python {browse} --box {box}")  # fmt: skip
    home.mkdir(parents=True, exist_ok=True)
    told = []
    starter = sibling("starter-words", "starter")
    init = ["init", "--box", str(box), "--pile", str(pile), "--key", str(key)]
    if starter is None:
        told.append(
            "The starter-words add-on isn't here, so there's no words list yet."
        )
    elif words.exists():
        init += ["--words", str(words)]
        told.append(f"Your words list was already at {words}; it's used as it is.")
    else:
        code, said = quiet(starter.copy, words)
        if code != kernel.ALIVE:
            return code, said
        init += ["--words", str(words)]
        told.append(f"Your words list: {words}. Edit it to teach willow your words.")
    code, said = quiet(kernel.main, init)
    if code != kernel.ALIVE:
        return code, said
    told.insert(0, f"Set up. Your files: {pile}\nWillow's record: {box}\n"
                   f"Your key: {key} (it approves answers; keep a copy somewhere safe)")  # fmt: skip
    browse = sibling("browse", "browse")
    if browse is not None:
        told.append(
            f"Open your folder in your browser:\n\n    python {browse.HERE} --box {box}\n"
        )
        told.append(
            "Or start it with a double-click next time:\n\n" + browse.launcher(box)
        )
    if (STDLIB / "backup" / "backup.py").is_file():
        told.append(
            f"Back it up:\n\n    python {STDLIB / 'backup' / 'backup.py'} --box {box} --to FOLDER\n"
        )
    return kernel.ALIVE, "\n\n".join(t.rstrip("\n") for t in told) + "\n"


def ask() -> tuple[Path, Path] | None:
    """Both folders, asked for in a terminal; None if no folder was given."""
    try:
        pile = input("Where are your files? (a folder) ").strip()
        home = input(f"Where should willow keep its things? [{DEFAULT}] ").strip()
    except EOFError:
        return None
    return (Path(pile), Path(home or DEFAULT)) if pile else None


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--pile", "--to"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not argv and sys.stdin.isatty():
        got = ask()
        if got is None:
            print(__doc__.split("\n\n")[1], file=sys.stderr)
            return kernel.REFUSED
        # the same command line, typed for them: what it may write is under --to
        pile, home = got
        argv = ["--pile", str(pile.expanduser()), "--to", str(home.expanduser())]
        return subprocess.call([sys.executable, str(Path(__file__).resolve()), *argv])
    elif opts.get("--pile") and opts.get("--to") and not args:
        pile, home = Path(opts["--pile"]), Path(opts["--to"])
    else:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    code, said = start(pile, home)
    if code == kernel.REFUSED:
        print(f"refused: {said}", file=sys.stderr)
    else:
        print(said, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
