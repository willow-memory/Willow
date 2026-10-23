"""similar.py: what's already on the list, before you build or add something.

    python adapters/stdlib/similar/similar.py near "your idea in a sentence"
    python adapters/stdlib/similar/similar.py check
    python adapters/stdlib/similar/similar.py new --base REF

The list is every add-on in this repo: each built one's card, and each idea
in adapters/planned.json. Nothing outside this repo is read.

`near` asks the kernel's own search (`kernel.rank`, the same as a `bite`)
which entries hold your words: up to three, each with the words it shares.
A built one is something to connect to instead of building again; an idea is
something already on the list, to pick up rather than add twice.

`check` refuses two entries that are the same idea: the same words in the
same order, whatever the case or punctuation (the kernel's `bite_key`). CI
runs it; a near idea is shown, never refused, since only a person can say
two ideas are one.

`new` writes Markdown for a pull request: each entry added, or whose line
changed, since REF (a git commit or branch), and what on the list is close
to it. willow-bot posts it on the pull request. Nothing close is said, not
left out.

It only reads, and writes to standard output. Exit codes, the kernel's: 0
done; 2 refused (a duplicate, or a list that doesn't hold together).
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "willow_readme", ROOT / "adapters" / "stdlib" / "readme" / "readme.py"
)
readme = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(readme)

USAGE = """usage: similar.py near "your idea in a sentence"
       similar.py check
       similar.py new --base REF"""


def entries() -> list[dict]:
    """Every add-on, built and planned, as readme.py reads and checks them."""
    return readme.addons()


def text_of(a: dict) -> str:
    """What is searched for an entry: its line, and a built one's card."""
    out = a["line"] + "\n" + a["tags"].replace(",", " ")
    if a["built"]:
        card = (ROOT / a["path"] / "README.md").read_text(encoding="utf-8")
        out += "\n\n" + card.split("-->", 1)[1]
    return out


def pile(every: list[dict], leave_out: str | None = None) -> list[dict]:
    """The kernel's chunks: one per paragraph of each entry's text, its path
    the entry's name, so a name's words count too."""
    out = []
    for a in every:
        if a["name"] == leave_out:
            continue
        para, start = [], 1
        for i, line in enumerate(text_of(a).splitlines() + [""], 1):
            if not line.strip():
                if para:
                    body = "\n".join(para)
                    out.append({"path": a["name"], "line": start, "text": body,
                                "id": kernel.h256(body)})  # fmt: skip
                para = []
            else:
                if not para:
                    start = i
                para.append(line)
    return out


def near(every: list[dict], words: str, leave_out: str | None = None) -> list[tuple]:
    """(entry, the words it shares) for each entry the kernel's search
    serves for `words`, best first, each entry once."""
    by_name = {a["name"]: a for a in every}
    want = set(kernel.words(words)) - kernel.FUNCTION
    out, seen = [], set()
    for c in kernel.rank(pile(every, leave_out), words):
        if c["path"] in seen:
            continue
        seen.add(c["path"])
        shared = sorted(w for w in want if kernel.held_by(w, kernel.toks(c), {}))
        out.append((by_name[c["path"]], shared))
    return out


def line_of(a: dict, shared: list[str]) -> str:
    what = "built: connect to it" if a["built"] else "an idea already on the list"
    name = f"[**{a['name']}**]({a['path']})" if a["built"] else f"**{a['name']}**"
    return f"- {name}, {what}. {a['line']} (shares: {', '.join(shared)})"


def duplicates(every: list[dict]) -> list[tuple[str, str]]:
    first: dict[str, str] = {}
    out = []
    for a in every:
        key = kernel.bite_key(a["line"])
        if key is None:
            continue
        if key in first:
            out.append((first[key], a["name"]))
        else:
            first[key] = a["name"]
    return out


def at(ref: str) -> dict[str, str]:
    """{name: line} for every entry at a git ref, read from git itself."""

    def show(path: str) -> str | None:
        got = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=ROOT,
                             capture_output=True, text=True)  # fmt: skip
        return got.stdout if got.returncode == 0 else None

    out = {}
    planned = show("adapters/planned.json")
    for e in json.loads(planned) if planned else []:
        out[e["name"]] = e["line"]
    listed = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", ref, "adapters/"],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout.split()  # fmt: skip
    for path in listed:
        parts = path.split("/")
        if len(parts) == 4 and parts[3] == "README.md":
            card = show(path) or ""
            for line in card.split("-->")[0].splitlines():
                if line.startswith("line:"):
                    out[parts[2]] = line.split(":", 1)[1].strip()
    return out


def report(every: list[dict], before: dict[str, str]) -> str:
    changed = [a for a in every if before.get(a["name"]) != a["line"]]
    if not changed:
        return "### Similar\n\nThis pull request adds no add-on and no idea.\n"
    out = ["### Similar", "",
           "What's already on the list near each add-on or idea this pull "
           "request adds, by the kernel's own search over this repo's cards "
           "and ideas. A suggestion: only a person decides."]  # fmt: skip
    for a in changed:
        kind = "built" if a["built"] else "idea"
        out += ["", f"**{a['name']}** ({kind}): {a['line']}", ""]
        found = near(every, a["line"], leave_out=a["name"])
        out += [line_of(b, shared) for b, shared in found] or [
            "- Nothing on the list is close."
        ]
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    try:
        every = entries()
    except readme.Refused as why:
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    if len(argv) == 2 and argv[0] == "near":
        found = near(every, argv[1])
        print(
            "\n".join(line_of(a, s) for a, s in found)
            or "Nothing on the list is close."
        )
        return kernel.ALIVE
    if argv == ["check"]:
        dups = duplicates(every)
        for a, b in dups:
            print(f"refused: {a} and {b} have the same line", file=sys.stderr)
        if dups:
            return kernel.REFUSED
        print(f"{len(every)} add-ons and ideas, no two the same")
        return kernel.ALIVE
    if len(argv) == 3 and argv[:2] == ["new", "--base"]:
        print(report(every, at(argv[2])), end="")
        return kernel.ALIVE
    print(USAGE, file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
