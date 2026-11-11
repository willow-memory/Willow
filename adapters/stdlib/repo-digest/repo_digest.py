"""repo_digest.py: one page of what this repo needs from you, and the order its add-ons build in. Python 3.9+.

    python adapters/stdlib/repo-digest/repo_digest.py page [--json] [--root DIR]

Every tool here can say "I don't know": a file nothing declares, an idea
not built, an add-on that needs one that isn't there. Each says it in its
own place. This is the one page of them, for the repo itself, as the
digest add-on is for a person's folder, with where each goes.

What waits, and where it goes:

    a ring in what uses what    two add-ons that each need the other beside
                                them: one of the two `uses` lines is wrong
    uses one that isn't here    a card's `uses` names no built add-on: build
                                it, or take the name off
    nothing declares            a file with no kind (the kinds add-on's
                                count): a declaration, where its subject is
    ideas waiting               on the ideas list, by section: to build or
                                to leave
    entries waiting             changelog entries not yet in a release

And how the add-ons bridge. A card's `uses` line names the add-ons it
needs beside it. An add-on with none rests on the kernel alone; one that
uses those is one step up; and so on. The page says how many are at each
step, which rest on the most, the longest way down from any one, and the
add-ons most built on. That order is the order they have to be there in:
nothing runs before what it uses.

It reads the cards' headers, the ideas list, towncrier.toml and the names
of the files git knows. It writes nothing. Exit codes, the kernel's: 0
nothing waits that is wrong (ideas and entries waiting are how a repo
stands, not a fault); 42 a ring, a `uses` that leads nowhere or a file
nothing declares, or git couldn't list the files; 2 refused.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE.parent / "kinds"))
import kernel  # noqa: E402
import kinds  # noqa: E402

NAME = "repo-digest"
USAGE = "usage: repo_digest.py page [--json] [--root DIR]"
SHOWN = 8  # names listed in a row before "and N more"


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


def uses_of(root: Path, files: list[str]) -> dict[str, list[str]]:
    """{add-on: the add-ons its card's `uses` line names}, for each card."""
    out = {}
    for f in files:
        if (
            f.count("/") != 3
            or not f.startswith("adapters/")
            or not f.endswith("/README.md")
        ):
            continue
        text = kinds.text_of(root / f)
        if not text.startswith(kinds.CARD_OPENS):
            continue
        line = re.search(r"^uses: (.+)$", text.split("-->", 1)[0], flags=re.M)
        named = [u.strip() for u in line.group(1).split(",")] if line else []
        out[f.split("/")[2]] = [u for u in named if u]
    return out


def rings(uses: dict[str, list[str]]) -> list[tuple[str, ...]]:
    """Each ring in what uses what, once, from its first name A to Z."""
    found: set[tuple[str, ...]] = set()

    def walk(a: str, path: tuple[str, ...]) -> None:
        if a in path:
            ring = path[path.index(a) :]
            i = ring.index(min(ring))
            found.add(ring[i:] + ring[:i])
            return
        for u in uses.get(a, ()):
            if u in uses:
                walk(u, path + (a,))

    for a in sorted(uses):
        walk(a, ())
    return sorted(found)


def steps_up(uses: dict[str, list[str]]) -> dict[str, int | None]:
    """{add-on: how many steps above the kernel it rests}: 0 with no `uses`,
    else one more than the highest it uses. None for one in a ring, or
    resting on one: it has no place in the order."""
    done: dict[str, int | None] = {}

    def of(a: str, path: tuple[str, ...]) -> int | None:
        if a in done:
            return done[a]
        if a in path:
            return None
        below = [of(u, path + (a,)) for u in uses[a] if u in uses]
        got = None if None in below else 1 + max(below) if below else 0
        if not path or got is not None:
            done[a] = got
        return got

    for a in sorted(uses):
        done[a] = of(a, ())
    return done


def way_down(
    uses: dict[str, list[str]], steps: dict[str, int | None], a: str
) -> list[str]:
    """The longest way from a down to an add-on that rests on the kernel."""
    out = [a]
    while True:
        below = [u for u in uses[out[-1]] if steps.get(u) is not None]
        if not below:
            return out
        out.append(max(sorted(below), key=lambda u: steps[u]))


def names(found: list[str]) -> str:
    more = len(found) - SHOWN
    return ", ".join(found[:SHOWN]) + (f", and {more} more" if more > 0 else "")


def count(n: int, one: str, many: str | None = None) -> str:
    return f"{n} {one if n == 1 else many or one + 's'}"


def ideas(root: Path) -> list[tuple[str, str]]:
    try:
        entries = json.loads(kinds.text_of(root / kinds.IDEAS) or "[]")
    except ValueError:
        return [(kinds.IDEAS, "the ideas list can't be read")]
    by: dict[str, list[str]] = {}
    for e in entries if isinstance(entries, list) else ():
        if isinstance(e, dict) and e.get("name"):
            by.setdefault(str(e.get("section") or "(no section)"), []).append(
                str(e["name"])
            )
    return [
        (section, f"{count(len(found), 'idea')}, such as {sorted(found)[0]}")
        for section, found in sorted(by.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    ]


def page(root: Path, files: list[str]) -> tuple[dict, bool]:
    """(the report, whether anything that is wrong waits)."""
    uses = uses_of(root, files)
    known, _ = kinds.census(root, files)
    steps = steps_up(uses)
    ring_rows = []
    in_ring = {a for ring in rings(uses) for a in ring}
    for ring in rings(uses):
        rest = sorted(a for a, s in steps.items() if s is None and a not in in_ring)
        on = (
            f"; {count(len(rest), 'add-on rests', 'add-ons rest')} on it: {names(rest)}"
            if rest
            else ""
        )
        ring_rows.append(
            (" → ".join(ring + ring[:1]), f"each needs the other beside it{on}")
        )
    nowhere = [
        (a, f"uses {u}, and no add-on here is called that")
        for a in sorted(uses)
        for u in uses[a]
        if u not in uses
    ]
    lost: dict[str, list[str]] = {}
    for f in files:
        if f not in known:
            lost.setdefault(kinds.folder_of(f), []).append(f)
    undeclared = [
        (where, f"{count(len(fs), 'file')}, such as {fs[0]}")
        for where, fs in sorted(lost.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    ]
    idea_rows = ideas(root)
    fragments = sum(1 for kind, _ in known.values() if kind == "account") - 1
    entries = [("the changelog", f"{count(fragments, 'entry', 'entries')} not yet in a release")] if fragments > 0 else []  # fmt: skip

    placed = sorted((s, a) for a, s in steps.items() if s is not None)
    top = placed[-1][0] if placed else 0
    order = []
    for step in range(top + 1):
        at = [a for s, a in placed if s == step]
        label = "on the kernel alone" if step == 0 else count(step, "step") + " up"
        order.append(
            (label, count(len(at), "add-on") + ("" if step == 0 else f": {names(at)}"))
        )
    if top:
        deepest = max(
            sorted(a for s, a in placed if s == top),
            key=lambda a: len(way_down(uses, steps, a)),
        )
        order.append(
            ("the longest way down", " → ".join(way_down(uses, steps, deepest)))
        )
    used: dict[str, int] = {}
    for a in uses:
        for u in set(uses[a]):
            if u in uses:
                used[u] = used.get(u, 0) + 1
    most = [
        (u, f"{count(n, 'add-on uses', 'add-ons use')} it")
        for u, n in sorted(used.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    ]
    if not uses and not files:
        return report(NAME, "empty", "no file is tracked here", []), False
    n_undeclared = sum(len(fs) for fs in lost.values())
    n_ideas = sum(int(what.split()[0]) for _, what in idea_rows if what[0].isdigit())
    said = (
        f"{count(n_undeclared, 'file')} nothing declares, {count(len(ring_rows), 'ring')} "
        f"in what uses what, {count(n_ideas, 'idea')} waiting; "
        f"{count(len(uses), 'add-on')} build {count(top, 'step')} deep"
    )
    doc = report(NAME, "populated", said, [
        ("a ring in what uses what: one of the two uses lines is wrong", ring_rows),
        ("uses one that isn't here: build it, or take the name off", nowhere),
        ("nothing declares: a declaration, where its subject lives", undeclared),
        ("ideas waiting: to build, or to leave", idea_rows),
        ("entries waiting: for the next release", entries),
        ("the order they build in", order),
        ("most built on", most),
    ])  # fmt: skip
    return doc, bool(ring_rows or nowhere or undeclared)


def args_of(argv: list[str]) -> tuple[bool, Path]:
    if not argv or argv[0] != "page":
        raise ValueError(USAGE)
    as_json, root, it = False, ROOT, iter(argv[1:])
    for a in it:
        if a == "--json":
            as_json = True
        elif a == "--root":
            given = next(it, "")
            root = Path(given)
            if not given or not root.is_dir():
                raise ValueError(
                    f"refused: --root {given or 'with no folder'} is not a folder"
                )
        else:
            raise ValueError(USAGE)
    return as_json, root


def main(argv: list[str]) -> int:
    try:
        as_json, root = args_of(argv)
    except ValueError as why:
        print(why, file=sys.stderr)
        return kernel.REFUSED
    files = kinds.tracked(root)
    if files is None:
        say(report(NAME, "unreachable", f"git couldn't list the files of {root}", []), as_json)  # fmt: skip
        return kernel.ESCALATE
    doc, waits = page(root, files)
    say(doc, as_json)
    return kernel.ESCALATE if waits else kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
