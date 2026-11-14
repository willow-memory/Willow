"""reach.py: what an add-on's tests can read of this repo, drawn wide. Python 3.9+.

A gate's verdict is a function of the bytes its tests can read. For an
add-on whose files reach nothing of the repo but its own folder, the kernel,
the add-ons its card names (`uses`, `looks-for`, and theirs in turn) and
CI's own runner, that is its reach: those folders and files. ci-memo keys
the add-on test gates on it, so a gate whose add-ons' reach didn't change
can stand on its last verdict; and the guard holds every test to it, so a
read outside is a breach, as a write outside the card's `writes` is.

An add-on is drawn narrow when a scan of its files finds nothing that
reaches further: no other top-level name of the repo in quotes or a path
(`"docs"`, `/README.md"`...), no other add-on's folder that its card doesn't
name, no listing of the add-ons' folder. Anything else is drawn wide, the
whole tree. A repo tool (ci, readme, similar, github) is always wide, and so
is one in WIDE. The scan only spares the guard false alarms: what holds the
reach is the guard, which fails any run whose tests read outside it, so a
run that ci-memo pins never read past what its keys hold.

    reach(root, "stdlib/debts")  -> ["adapters/stdlib/debts/", "kernel.py", ...]
    reach(root, "stdlib/readme") -> None   (the whole tree)

Prefixes end in `/` for a folder; anything else is one file.
"""

from __future__ import annotations

import os
import re

#: the repo's own tools: their tests read the whole tree (cards, docs, lists)
REPO_TOOLS = {"ci", "readme", "similar", "github"}
#: what every add-on's tests run under: the runner, the guard, the cut into
#: chunks, and the kernel
RUNNER = ("kernel.py", "adapters/stdlib/ci/", "adapters/stdlib/test-shards/")
#: add-ons whose tests read past their reach in a way the scan can't see (a
#: path built from parts): found by the guard, which fails a run that reads
#: outside, and listed here, so each is drawn wide
WIDE = {
    "live",  # runs each way in through config(), naming their folders as words
}
LISTS = re.compile(
    r"(STDLIB|HERE\.parent|\"stdlib\"|\"deps\")\)?\s*\.\s*(iterdir|glob|rglob)\("
)
ADDON_REF = re.compile(
    r"(?:stdlib|deps|STDLIB|HERE\.parent)\W{1,6}([a-z0-9][a-z0-9-]+)"
)

_cache: dict = {}


def card_leans(root: str, addon: str) -> set[str]:
    """The add-ons a card names in `uses` and `looks-for`, as "kind/name"."""
    try:
        with open(
            os.path.join(root, "adapters", addon, "README.md"), encoding="utf-8"
        ) as f:
            head = f.read().split("-->")[0]
    except OSError:
        return set()
    out = set()
    for line in head.splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip() in ("uses", "looks-for"):
            for n in value.split(","):
                n = n.strip()
                for kind in ("stdlib", "deps"):
                    if n and os.path.isdir(os.path.join(root, "adapters", kind, n)):
                        out.add(f"{kind}/{n}")
    return out


def leans(root: str, addon: str) -> set[str]:
    """`addon` and every add-on it leans on, in turn."""
    seen, todo = set(), [addon]
    while todo:
        a = todo.pop()
        if a not in seen:
            seen.add(a)
            todo += sorted(card_leans(root, a) - seen)
    return seen


def tops(root: str) -> set[str]:
    return {n for n in os.listdir(root) if not n.startswith(".")} - {
        "kernel.py",
        "adapters",
    }


def wide_because(root: str, addon: str) -> str | None:
    """Why `addon` is drawn wide, or None when it is narrow."""
    kind, name = addon.split("/")
    if name in REPO_TOOLS:
        return "a repo tool"
    if name in WIDE:
        return "listed wide: its tests read past what the scan sees"
    named = {a.split("/")[1] for a in leans(root, addon)} | {"ci", "test-shards"}
    every = set()
    for k in ("stdlib", "deps"):
        if os.path.isdir(os.path.join(root, "adapters", k)):
            every |= set(os.listdir(os.path.join(root, "adapters", k)))
    top = tops(root)
    folder = os.path.join(root, "adapters", kind, name)
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            with open(
                os.path.join(dirpath, fn), encoding="utf-8", errors="ignore"
            ) as f:
                text = f.read()
            for t in top:
                if re.search(r"[\"'/]" + re.escape(t) + r"[\"'/]", text):
                    return f"{fn} names {t}"
            if LISTS.search(text):
                return f"{fn} lists the add-ons"
            for m in ADDON_REF.finditer(text):
                if (
                    m.group(1) in every
                    and m.group(1) not in named
                    and m.group(1) != name
                ):
                    return f"{fn} reaches {m.group(1)}, which its card doesn't name"
    return None


def reach(root: str, addon: str) -> list[str] | None:
    """The prefixes `addon` ("stdlib/NAME") can read, or None: the whole tree."""
    root = os.path.realpath(root)
    key = (root, addon)
    if key not in _cache:
        if wide_because(root, addon):
            _cache[key] = None
        else:
            _cache[key] = sorted(
                {f"adapters/{a}/" for a in leans(root, addon)} | set(RUNNER)
            )
    return _cache[key]


def within(rel: str, prefixes: list[str]) -> bool:
    """Whether a repo-relative path is one of the prefixes or under one."""
    return any(rel == p or (p.endswith("/") and rel.startswith(p)) for p in prefixes)
