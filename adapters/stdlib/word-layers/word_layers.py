"""word_layers.py: one words list made from several, so a box's list is a
master list and the layers that box needs. Python 3.9+.

    python adapters/stdlib/word-layers/word_layers.py make --from LIST [--from LIST ...] --to MADE
    python adapters/stdlib/word-layers/word_layers.py check --from LIST [--from LIST ...] --to MADE

A box takes one words list, named when the box is made. One list for
everything goes wrong quickly: "step" is an instruction in one pile and a
stack's step in the next, so a line that helps one box misleads another. A
list for each box goes wrong the other way: the words that are true
everywhere are written out in each, and corrected in one.

So the lists are kept in layers, each a words list of its own: a master of
what is true in every box, and a layer for each matter or project. `make`
writes MADE as those lists one after another, in the order given, each under
a line saying which file it is and the SHA-256 of what it held. The kernel
already reads a word that is on two lines as both lines together, so a word
in the master and again in a layer means all of what each says. MADE is the
file the box names; it is made, never edited.

`make` writes only when something changed, and says which: `made` (it
wasn't there), `remade` with the layers that changed, or `current`. Words
that more than one layer gives are listed, since those are where two lists
meet. A layer that isn't a words list is refused, naming it and its line. A
MADE that is there and was not made by this is refused and left as it was:
it is someone's own list. MADE is readable only by its owner, as the kernel
asks of a words list.

`check` writes nothing: it says whether MADE is what `make` would write now.

Exit codes, the kernel's: `make` 0 made, remade or current; `check` 0
current, 42 stale or not made yet; 2 refused (a bad command line, a layer
that is missing or not a words list, a MADE that isn't one of these, a MADE
whose folder isn't there).
"""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

#: The first line of a made list. A file that doesn't open with it is not
#: one of these, and is never written over.
MARK = "# made by word-layers: edit the layers below, never this file."


def layer(path: Path) -> tuple[str, dict]:
    """A layer's text and the words it gives, or ValueError saying why not."""
    try:
        text = path.read_bytes().decode("utf-8")
    except (OSError, ValueError) as e:
        raise ValueError(f"{path} could not be read: {type(e).__name__}") from None
    alias, why = kernel.parse_words(text)
    if why:
        raise ValueError(f"{path}: {why}")
    return text, alias


def made_from(paths: list[Path]) -> tuple[str, dict[str, list[str]]]:
    """What MADE should hold for these layers, and for each word more than one
    layer gives, the layers that give it."""
    parts, gives = [MARK, ""], {}
    for p in paths:
        text, alias = layer(p)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        parts += [f"# layer {p.resolve()} sha256 {digest}", text.rstrip("\n"), ""]
        for word in alias:
            gives.setdefault(word, []).append(p.name)
    whole = "\n".join(parts)
    _, why = kernel.parse_words(whole)
    if why:  # each layer parsed alone, so this is this add-on's own fault
        raise ValueError(f"the made list would not be a words list: {why}")
    return whole, {w: ls for w, ls in sorted(gives.items()) if len(ls) > 1}


def layers_in(text: str) -> dict[str, str]:
    """{layer path: sha256} a made list says it was made from."""
    out = {}
    for line in text.splitlines():
        f = line.split()
        if line.startswith("# layer ") and len(f) == 5 and f[3] == "sha256":
            out[f[2]] = f[4]
    return out


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("make", "check"):
        return usage()
    froms, to, it = [], None, iter(argv[1:])
    for a in it:
        value = next(it, "")
        if a == "--from" and value:
            froms.append(Path(value))
        elif a == "--to" and value and to is None:
            to = Path(value)
        else:
            return usage()
    if not froms or to is None:
        return usage()
    try:
        whole, shared = made_from(froms)
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    old = None
    if to.is_dir() or not to.parent.is_dir():
        print(f"refused: --to {to}: a file, in a folder that is there", file=sys.stderr)
        return kernel.REFUSED
    if to.exists():
        try:
            old = to.read_bytes().decode("utf-8")
        except (OSError, ValueError):
            old = ""
        if not old.startswith(MARK):
            print(f"refused: {to} is there and was not made by word-layers; "
                  "it is left as it is", file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
    was, now = layers_in(old or ""), layers_in(whole)
    moved = [Path(p).name for p in now if was.get(p) != now[p]]
    moved += [f"{Path(p).name} (taken out)" for p in was if p not in now]
    if old == whole:
        state = "current"
    elif argv[0] == "check":
        state = "stale" if old is not None else "not made yet"
    else:
        fd, tmp = tempfile.mkstemp(dir=to.parent, prefix=".word-layers-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(whole)
            os.chmod(tmp, 0o600)
            os.replace(tmp, to)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
        state = "remade" if old is not None else "made"
    words = len(kernel.parse_words(whole)[0])
    print(f"{state}: {to}, {words} words from {len(froms)} layers"
          + (f"; changed: {', '.join(moved)}" if moved and state != "current" else ""))  # fmt: skip
    for word, names in shared.items():
        print(f"  in more than one layer, read together: {word} ({', '.join(names)})")
    return kernel.ESCALATE if state in ("stale", "not made yet") else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
