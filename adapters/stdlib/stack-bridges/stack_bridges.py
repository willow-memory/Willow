"""stack_bridges.py: which steps of a stack take what an earlier step made, and the order that leaves them in. Python 3.9+.

    python adapters/stdlib/stack-bridges/stack_bridges.py --stack FILE [--json]

A stack file lists its steps top to bottom, and stack runs them that way.
But the steps are not a row: some take what an earlier one made, and the
rest could run in any order, or at once. That is decided when the stack is
written, and nothing says it. This reads the file and says it.

A bridge is a step taking what another made. Two kinds are in the file:

    its output    the step names an earlier step's kept output, `{06}`
    what it wrote the step names a place an earlier step was told to
                  write to with `--to`: the place itself, a file under it,
                  or the folder it sits in

From the bridges comes the order. A step that takes nothing rests on no
other and could run first. A step is one deeper than the deepest it takes
from, and steps at the same depth don't need one another.

A third kind comes from the cards, not the file:

    the record    the step names a record after a step whose add-on's
                  card says it writes the record, and both name the same
                  one: `{box}`, or the folder given to `--box`

A stack file names the record the same way for a step that adds a row and
one that only reads, so the card's `writes` line is what tells them apart.
A record named by its folder is tied only to steps naming that folder:
whether `{box}` is one of those folders is decided when the stack is run,
and the file doesn't say.
A step naming an add-on that isn't here has no card to read, and is said.

And two bridges that can't hold, each said with its step:

    takes {NN}, and no step before it has that number
    takes a place a later step writes: it would read it before it is there

Two steps told to write to one place are said too, and not as a fault: for
a folder that is how it is used, for a file one of the two is lost, and the
stack file doesn't say which the place is.

It reads the file and writes nothing; it runs no step and opens no folder
the stack names. Exit codes, the kernel's: 0 the bridges hold (a stack with
none is `empty`); 42 one can't; 2 refused (a bad command line, no such
file, a file that isn't a stack).
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

NAME = "stack-bridges"
USAGE = "usage: stack_bridges.py --stack FILE [--json]"
TAKEN = re.compile(r"\{(\d\d)(?:\.json)?\}")


def stack_module():
    spec = importlib.util.spec_from_file_location(
        "stack", HERE.parent / "stack" / "stack.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def written(args: list[str]) -> list[str]:
    """The places a step is told to write to: each word after a `--to`."""
    return [
        args[i + 1].rstrip("/")
        for i, a in enumerate(args[:-1])
        if a == "--to" and args[i + 1]
    ]


def read(args: list[str]) -> list[str]:
    """Every word of a step that could name a place it reads: each argument
    but the ones after `--to`, and what follows a `kind:` before a path."""
    out = []
    for i, a in enumerate(args):
        if a == "--to" or (i and args[i - 1] == "--to"):
            continue
        out.append(a.rstrip("/"))
        head, sep, rest = a.partition(":")
        if sep and rest and "/" not in head and "{" not in head and "<" not in head:
            out.append(rest.rstrip("/"))
    return out


def reaches(word: str, place: str) -> bool:
    """Whether a word a step reads names a place another wrote: the place
    itself, something under it, or the folder it is in."""
    return word == place or word.startswith(place + "/") or place.startswith(word + "/")


def short(place: str) -> str:
    return place.rsplit("/", 1)[-1] or place


def bridges(
    steps: list[tuple[str, list[str]]],
) -> tuple[
    dict[int, list[tuple[int, str]]], list[tuple[int, str]], list[tuple[int, str]]
]:
    """({a step's place: [(the place it takes from, how)]}, [(a step's
    place, a bridge that can't hold)], [(a step's place, the place it
    writes to as an earlier step does)]), places counted from 1."""
    wrote = {n: written(args) for n, (_, args) in enumerate(steps, 1)}
    takes: dict[int, list[tuple[int, str]]] = {}
    broken: list[tuple[int, str]] = []
    shared: list[tuple[int, str]] = []
    for n, (_, args) in enumerate(steps, 1):
        found: list[tuple[int, str]] = []
        for m in TAKEN.finditer(" ".join(args)):
            src = int(m.group(1))
            if 1 <= src < n:
                found.append((src, "its output"))
            else:
                broken.append(
                    (n, f"takes {m.group(0)}, and no step before it has that number")
                )
        for word in read(args):
            for src, places in wrote.items():
                for place in places:
                    if src == n or not reaches(word, place):
                        continue
                    if src < n:
                        found.append((src, f"what it wrote, {short(place)}"))
                    else:
                        broken.append(
                            (
                                n,
                                f"takes {short(place)}, which step {src:02d} writes later",
                            )
                        )
        for place in wrote[n]:
            for src in range(1, n):
                if place in wrote[src]:
                    shared.append(
                        (n, f"writes to {short(place)}, as step {src:02d} does")
                    )
        if found:
            takes[n] = sorted(set(found))
    return takes, sorted(set(broken)), sorted(set(shared))


def writes_record(name: str) -> bool | None:
    """Whether the add-on's card promises to write the record: its `writes`
    line names it. None when no add-on here is called that."""
    for kind in ("stdlib", "deps"):
        card = HERE.parents[1] / kind / name / "README.md"
        if card.is_file():
            head = card.read_text(encoding="utf-8").partition("-->")[0]
            line = re.search(r"^writes: (.+)$", head, flags=re.M)
            return bool(line) and "record" in [
                w.strip() for w in line.group(1).split(",")
            ]
    return None


def record_of(args: list[str]) -> str | None:
    """The record a step names: the folder given to `--box`, as written
    less a `./` before it and a `/` after; else `{box}` when the step names
    that anywhere; else None."""
    for flag, value in zip(args, args[1:]):
        if flag == "--box" and value != "{box}":
            folder = value.rstrip("/")
            while folder.startswith("./"):
                folder = folder[2:]
            return folder or value
    return "{box}" if "{box}" in args else None


def record_bridges(
    steps: list[tuple[str, list[str]]], writes=writes_record
) -> dict[int, int]:
    """{a step's place: the place of the last step before it that writes the
    same record}, for each step that names a record after one that writes
    it."""
    out: dict[int, int] = {}
    last: dict[str, int] = {}
    for n, (name, args) in enumerate(steps, 1):
        record = record_of(args)
        if record is None:
            continue
        if record in last:
            out[n] = last[record]
        if writes(name):
            last[record] = n
    return out


def depths(count: int, takes: dict[int, list[tuple[int, str]]]) -> dict[int, int]:
    """{a step's place: how many steps deep it rests}: 0 taking nothing,
    else one more than the deepest it takes from. Sources come first, so
    one pass top to bottom is enough."""
    deep: dict[int, int] = {}
    for n in range(1, count + 1):
        deep[n] = 1 + max((deep[src] for src, _ in takes.get(n, ())), default=-1)
    return deep


def way_down(n: int, takes: dict, deep: dict[int, int]) -> list[int]:
    out = [n]
    while takes.get(out[-1]):
        out.append(
            max(sorted({src for src, _ in takes[out[-1]]}), key=lambda s: deep[s])
        )
    return out


def page(text: str) -> tuple[dict | None, str | None, bool]:
    """(the report, why the file isn't a stack, whether a bridge can't hold)."""
    pools, err = stack_module().parse_stack(text)
    if err:
        return None, err, False
    steps = [step for _, rows in pools for step in rows]
    label = {n: f"{n:02d} {name}" for n, (name, _) in enumerate(steps, 1)}
    takes, broken, shared = bridges(steps)
    for n, src in record_bridges(steps).items():
        takes[n] = sorted(set(takes.get(n, [])) | {(src, "the record as it left it")})
    deep = depths(len(steps), takes)
    count = sum(len({src for src, _ in found}) for found in takes.values())
    cant = [(label[n], why) for n, why in broken]
    both = [(label[n], why) for n, why in shared]
    rows = []
    for n in sorted(takes):
        by: dict[int, list[str]] = {}
        for src, how in takes[n]:
            by.setdefault(src, []).append(how)
        rows.append(
            (
                label[n],
                "; ".join(
                    f"{label[src]}: {', '.join(hows)}"
                    for src, hows in sorted(by.items())
                ),
            )
        )
    top = max(deep.values())
    order = []
    for d in range(top + 1):
        at = [label[n] for n in sorted(deep) if deep[n] == d]
        where = (
            "rest on no other" if d == 0 else f"{d} step{'' if d == 1 else 's'} deep"
        )
        order.append((where, f"{len(at)}: {', '.join(at)}"))
    if top:
        deepest = min(n for n in deep if deep[n] == top)
        order.append(
            (
                "the longest way down",
                " → ".join(label[n] for n in way_down(deepest, takes, deep)),
            )
        )
    named = [
        (n, writes_record(name))
        for n, (name, args) in enumerate(steps, 1)
        if record_of(args) is not None
    ]
    writers = [label[n] for n, w in named if w]
    if writers:
        order.append((
            "write the record",
            f"{len(writers)}: {', '.join(writers)}; a step that names the record after "
            "one of these takes the record as it left it",
        ))  # fmt: skip
    unknown = [label[n] for n, w in named if w is None]
    if unknown:
        order.append((
            "no card here",
            f"{len(unknown)}: {', '.join(unknown)}; whether these write the record isn't known",
        ))  # fmt: skip
    plural = "" if len(steps) == 1 else "s"
    if not count and not cant and not both:
        said = f"{len(steps)} step{plural}, and none takes what another made"
        return report(NAME, "empty", said, []), None, False
    said = (
        f"{len(steps)} step{plural}, {count} bridge{'' if count == 1 else 's'}, "
        f"{top} deep; {sum(1 for d in deep.values() if d == 0)} rest on no other"
    )
    doc = report(NAME, "populated", said, [
        ("a bridge that can't hold", cant),
        ("two steps write to one place: fine for a folder, a loss for a file", both),
        ("what each step takes, and from which", rows),
        ("the order that leaves them in", order),
    ])  # fmt: skip
    return doc, None, bool(cant)


def args_of(argv: list[str]) -> tuple[Path, bool]:
    as_json, file, it = False, None, iter(argv)
    for a in it:
        if a == "--json":
            as_json = True
        elif a == "--stack" and file is None:
            file = next(it, "")
        else:
            raise ValueError(USAGE)
    if not file:
        raise ValueError(USAGE)
    if not Path(file).is_file():
        raise ValueError(f"refused: no stack file {file}")
    return Path(file), as_json


def main(argv: list[str]) -> int:
    try:
        file, as_json = args_of(argv)
        doc, err, cant = page(file.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError) as why:
        print(why, file=sys.stderr)
        return kernel.REFUSED
    if err:
        print(f"refused: {file} is not a stack: {err}", file=sys.stderr)
        return kernel.REFUSED
    say(doc, as_json)
    return kernel.ESCALATE if cant else kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
