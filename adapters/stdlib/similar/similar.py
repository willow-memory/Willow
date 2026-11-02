"""similar.py: what's already on the list, before you build or add something.

    python adapters/stdlib/similar/similar.py near "your idea in a sentence"
    python adapters/stdlib/similar/similar.py check
    python adapters/stdlib/similar/similar.py new --base REF
    python adapters/stdlib/similar/similar.py tags [NAME...]

The list is every add-on in this repo, built and planned: each one's line,
and the one tag a person chose for it, if any. Nothing outside this repo is
read.

`near` asks the kernel's own search (`kernel.rank`, the same as a `bite`)
which entries hold your words: up to three, each with the words it shares.
A built one is something to connect to instead of building again; an idea is
something already on the list, to pick up rather than add twice.

`check` refuses two entries that are the same idea: the same words in the
same order, whatever the case or punctuation (the kernel's `bite_key`). CI
runs it; a near idea is shown, never refused, since only a person can say
two ideas are one.

`tags` prints each entry's tags and the three entries nearest it, as the
add-on list shows them. None of it is stored: it is worked out from the cards
every time, so it can't go stale when a card changes. Five tags at most:

    install   no-install or needs-install, from the card's kind
    network   offline, this-machine or online, from its network line
    two topics
              words the entry shares with its nearest entries, which say what
              it is about: the entries are ranked against the whole card by
              pile-rank's BM25, and a topic is a word from their names and
              one-line descriptions that also appears in this card, used by
              a handful of entries and not by most
    its own   the one tag the card's author chose, if any: the open slot

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
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pile-rank"))
import kernel  # noqa: E402
import pile_rank  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "willow_readme", ROOT / "adapters" / "stdlib" / "readme" / "readme.py"
)
readme = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(readme)

USAGE = """usage: similar.py near "your idea in a sentence"
       similar.py check
       similar.py new --base REF
       similar.py tags [NAME...]"""


def entries() -> list[dict]:
    """Every add-on, built and planned, as readme.py reads and checks them."""
    return readme.addons()


def text_of(a: dict) -> str:
    """What `near` searches for an entry: its line, and the tag a person
    chose. Not the card's whole text: its common words (answers, reads, only)
    made unrelated add-ons near each other."""
    own = readme.split_tags(a.get("tags", ""))
    return a["line"] + ("\n" + " ".join(own) if own else "")


# ── tags, worked out ─────────────────────────────────────────────────────────
#: words that say how a card is written, not what its add-on is about; the one
#: list to tune when a topic reads as noise
HOW = set("""
about across add added adds after again against all almost also always another answer answered
answering answers any are ask asked asking asks back before being big both built came can card
cards change changed changes check checked checks cited come comes could day does done downloaded
each else even every exact exist exists few find finds first folder folders from gets give given
gives going gone hand hands has hasn have here hold holds input into its just keep keeping keeps
kept kind last later leave leaves less like line lines list machine made make makes many may more
most much must name named names need needs never new next none not nothing now off often old once
one ones only other others out over own part per picked place plain put read reading reads ready
right run runs said same say says see seen set shows side since some something still such take
takes tell than that the them then there these they thing things this those through time times too
turn two type under until use used uses using very want way ways well what when where which while
who whole why will willow with without word words write writes writing written wrote yes yet you
your yours kernel record records box boxes pile passage passages file files question questions
idea ideas com www http https org toward nearly three four five ons guess
""".split())
#: a topic is used by at least this many entries' names and lines, and at most
#: the other: it groups a handful, never most of the list
TOPIC_USE = (2, 25)
NEIGHBOURS = 6
#: what the install and network tags can be; the card's own tag is never one
FACT_TAGS = {"no-install", "needs-install", "offline", "this-machine", "online"}


def card_text(a: dict, root: Path = ROOT) -> str:
    """An entry's name, its line and, for a built one, the first two
    paragraphs of its card: what it is, in the words its author chose."""
    out = a["name"].replace("-", " ") + ". " + a["line"]
    if a["built"]:
        body = (root / a["path"] / "README.md").read_text(encoding="utf-8")
        body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
        paras = [p for p in body.split("\n\n") if p.strip()
                 and not p.lstrip().startswith(("#", "```", "|", "    "))]  # fmt: skip
        out += " " + " ".join(paras[:2])
    return out


def topic_words(text: str) -> list[tuple[str, str]]:
    """(plain form, word as written) for each word that could be a topic."""
    out = []
    for w in kernel.words(text):
        lw = w.lower()
        if lw in kernel.FUNCTION or lw in HOW or len(lw) < 3:
            continue
        if any(c.isdigit() for c in lw):
            continue
        out.append((kernel.stem(lw), lw))
    return out


def facts_tags(a: dict) -> list[str]:
    net = {"none": "offline", "loopback": "this-machine"}.get(a["network"], "online")
    return ["no-install" if a["kind"] == "stdlib" else "needs-install", net]


def worked_out(every: list[dict], root: Path = ROOT) -> dict[str, dict]:
    """{name: {"tags": [...], "near": [three names]}} for every entry, the
    same for the same cards on any machine."""
    text = {a["name"]: card_text(a, root) for a in every}
    whole = {n: {s for s, _ in topic_words(t)} for n, t in text.items()}
    form: dict[str, Counter] = defaultdict(Counter)
    short, use = {}, Counter()
    for a in every:
        got = topic_words(a["name"].replace("-", " ") + ". " + a["line"])
        for s, w in got:
            form[s][w] += 1
        short[a["name"]] = {s for s, _ in got}
        use.update(short[a["name"]])
    ranker = pile_rank.Ranker(
        [{"path": n, "line": 1, "text": t, "id": kernel.h256(t)} for n, t in text.items()]
    )
    out = {}
    for a in every:
        n = a["name"]
        nb = [c["path"] for c, _, _ in ranker.rank(text[n], NEIGHBOURS + 1)
              if c["path"] != n][:NEIGHBOURS]  # fmt: skip
        shared = Counter(
            s for m in nb for s in whole[n] & short[m]
            if TOPIC_USE[0] <= use[s] <= TOPIC_USE[1]
        )  # fmt: skip
        own = readme.split_tags(a.get("tags", ""))
        topics = []
        for s in sorted(
            (s for s in shared if shared[s] >= 2 or s in short[n]),
            key=lambda s: (-shared[s] - (s in short[n]), use[s], s),
        ):
            word = sorted(form[s].items(), key=lambda x: (-x[1], x[0]))[0][0]
            taken = {kernel.stem(w) for t in topics + own for w in t.split("-")}
            if s not in taken and word not in FACT_TAGS:  # "hook" beside "hooks" says it twice
                topics.append(word)
            if len(topics) == 2:
                break
        out[n] = {"tags": facts_tags(a) + topics + own, "near": nb[:3]}
    return out


def pile(every: list[dict], leave_out: str | None = None) -> list[dict]:
    """The kernel's chunks: one per entry, its path the entry's name, so a
    name's words count too."""
    return [
        {
            "path": a["name"],
            "line": 1,
            "text": text_of(a),
            "id": kernel.h256(text_of(a)),
        }
        for a in every
        if a["name"] != leave_out
    ]


def near(every: list[dict], words: str, leave_out: str | None = None) -> list[tuple]:
    """(entry, the words it shares) for each entry the kernel's search
    serves for `words`, best first, each entry once; then, up to `TOP` in
    all, each entry whose own words `words` holds by the same rule, counted
    against the entry. The kernel counts against the question, so a long,
    careful line reads as far from a short entry it contains."""
    by_name = {a["name"]: a for a in every}
    want = set(kernel.words(words)) - kernel.FUNCTION
    mine = kernel.forms(w.lower() for w in kernel.words(words))
    out, seen = [], set()
    for c in kernel.rank(pile(every, leave_out), words):
        if c["path"] in seen:
            continue
        seen.add(c["path"])
        shared = sorted(w for w in want if kernel.held_by(w, kernel.toks(c), {}))
        out.append((by_name[c["path"]], shared))
    back = []
    for c in pile(every, leave_out):
        theirs = set(kernel.words(c["text"])) - kernel.FUNCTION
        shared = sorted(w for w in theirs if kernel.holds(w, mine))
        if c["path"] not in seen and len(shared) >= max(2, kernel.HOLD * len(theirs)):
            back.append((-len(shared) / len(theirs), c["path"], shared))
    for _, name, shared in sorted(back)[: max(0, kernel.TOP - len(out))]:
        out.append((by_name[name], shared))
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
    if argv[:1] == ["tags"]:
        got = worked_out(every)
        names = argv[1:] or sorted(got)
        unknown = [n for n in names if n not in got]
        if unknown:
            print(f"refused: no add-on or idea named {unknown[0]!r}", file=sys.stderr)
            return kernel.REFUSED
        for n in names:
            print(f"{n}: {', '.join(got[n]['tags'])} · near: {', '.join(got[n]['near'])}")
        return kernel.ALIVE
    if len(argv) == 3 and argv[:2] == ["new", "--base"]:
        print(report(every, at(argv[2])), end="")
        return kernel.ALIVE
    print(USAGE, file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
