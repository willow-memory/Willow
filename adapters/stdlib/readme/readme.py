"""readme.py: the add-on list and the front page's feature, built from the
add-ons themselves.

    python adapters/stdlib/readme/readme.py write [--week YYYY-Www]
    python adapters/stdlib/readme/readme.py check
    python adapters/stdlib/readme/readme.py tags

Each generated section sits between two markers, `<!-- willow:NAME -->` and
`<!-- /willow:NAME -->`; everything outside them is written by hand and never
touched. `write` rebuilds every section in place. `check` rebuilds them in
memory and exits 2 if a page differs, so a section can't go stale: the
add-on's tests run it on every push.

ADDONS.md holds these sections, in this order:

    pools    how the add-ons spread: by section, built and ideas, and how
             many need an install
    newest   the five most recently added add-ons that are built
    pick     the add-on of the week, drawn from the built ones by a hash of
             the week, so anyone can recompute the draw
    list     every add-on, built and planned, by section, A to Z

README.md holds one, `front`: one of pools, newest or pick, as its `show=`
says (`<!-- willow:front show=pick week=2026-W43 -->`), and a link to the
rest. To switch the front page's feature, change `show=` and run `write`.

What it reads:

- each built add-on's card (`README.md` in its folder under `adapters/stdlib/`
  or `adapters/deps/`), which opens with a header:

      <!-- willow-addon
      section: Keeping track
      line: Numbers over time and a date gone by, beside an answer.
      source: box
      added: 2026-10-22
      writes: nothing
      network: none
      tags: no-install, offline, read-only, tracking
      -->

  plus `needs:` and `floor:` for one in `adapters/deps/`;
- `adapters/planned.json`, the add-ons not built yet, with the same fields
  and a `kind` (stdlib or deps).

A name is built when its folder exists, and then it must not also be planned.
Nothing is decided by hand in the list: building an add-on is what turns its
an idea into a built one.

Tags: every add-on and idea carries `tags:`, up to five, lowercase words
joined by -. `tags` fills them in for any entry that has none, from what its
card already says (an install or none, where it goes online, what it writes,
its section), leaving the fifth for a person, and never touches tags that are
there: once written, they are the card's to edit. `check` refuses an entry with
no tags, more than five, or one that isn't a tag.

The week of `pick` is part of the section (`<!-- willow:pick week=2026-W43
-->`). `write` sets it to this week, or to `--week`; `check` rebuilds with the
week already there, so the same repo always gives the same README.

Exit codes, the kernel's: 0 done or current; 2 refused, or README.md not
current.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

README = ROOT / "README.md"
ADDONS_MD = ROOT / "ADDONS.md"
ADAPTERS = ROOT / "adapters"
PLANNED = ADAPTERS / "planned.json"
KINDS = ("stdlib", "deps")

#: the list's sections, in order, each with the line under its heading
SECTIONS = [
    ("Reading more kinds of files", "Each writes plain text into a mirror folder"
     " the kernel searches, so your originals are never touched."),
    ("Finding things", ""),
    ("Your own words", "The blind tests' biggest gap: on day one, a person's"
     " words aren't their files' words."),
    ("Keeping track", ""),
    ("Trust and proof", ""),
    ("Privacy and safety", ""),
    ("Assistants", "Each hands in suggestions through propose. None can"
     " approve: every suggestion waits for your seal."),
    ("Ways to use it", ""),
    ("Play", ""),
    ("For maintainers", ""),
]  # fmt: skip
NAMES = [s for s, _ in SECTIONS]
FIELDS = {"section", "line", "source", "writes", "network", "tags"}
#: at most this many tags an add-on carries
MAX_TAGS = 5
#: the tag each section gives an entry that has none yet
SECTION_TAG = {
    "Reading more kinds of files": "file-reader", "Finding things": "search",
    "Your own words": "words", "Keeping track": "tracking",
    "Trust and proof": "trust", "Privacy and safety": "privacy",
    "Assistants": "assistant", "Ways to use it": "interface", "Play": "play",
    "For maintainers": "maintainers",
}  # fmt: skip
#: what an add-on may write: the guard in adapters/stdlib/ci/guard holds it
#: to this while its tests run; a file of the repo may also be named
WRITES = {"nothing", "record", "to"}
SOURCES = {"bot", "box", "new"}
HEADER = re.compile(r"\A<!-- willow-addon\n(.*?)\n-->\n", re.S)
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class Refused(Exception):
    pass


# ── the add-ons ──────────────────────────────────────────────────────────────
def card(folder: Path) -> dict:
    """A built add-on's header, from the top of its card."""
    readme = folder / "README.md"
    if not readme.is_file():
        raise Refused(f"{folder.relative_to(ROOT)} has no README.md card")
    m = HEADER.match(readme.read_text(encoding="utf-8"))
    if m is None:
        raise Refused(
            f"{readme.relative_to(ROOT)} doesn't open with a willow-addon header"
        )
    fields = {}
    for line in m.group(1).splitlines():
        key, sep, value = line.partition(":")
        if not sep or not value.strip():
            raise Refused(f"{readme.relative_to(ROOT)}: header line {line!r}")
        fields[key.strip()] = value.strip()
    return fields


def addons(tagged: bool = True) -> list[dict]:
    """Every add-on, built and planned, each checked; refused on the first
    that doesn't hold together. `tagged=False` is for `tags`, which fills
    them in."""
    out = []
    for kind in KINDS:
        for folder in sorted(p for p in (ADAPTERS / kind).glob("*") if p.is_dir()):
            if folder.name.startswith(("_", ".")):
                continue
            entry = {**card(folder), "name": folder.name, "kind": kind}
            entry["built"] = True
            entry["path"] = f"adapters/{kind}/{folder.name}/"
            out.append(entry)
    built = {a["name"] for a in out}
    for entry in json.loads(PLANNED.read_text(encoding="utf-8")):
        if entry.get("name") in built:
            raise Refused(f"{entry['name']} is built, and still in planned.json")
        out.append({**entry, "built": False})
    seen = set()
    for a in out:
        where = a.get("path") or f"planned.json: {a.get('name')}"
        if not NAME.fullmatch(str(a.get("name", ""))):
            raise Refused(f"{where}: a name is lowercase words joined by -")
        if a["name"] in seen:
            raise Refused(f"{a['name']} is listed twice")
        seen.add(a["name"])
        if a.get("kind") not in KINDS:
            raise Refused(f"{where}: kind is stdlib or deps")
        if "tags" not in a and not tagged:
            a["tags"] = ""
        if not FIELDS <= a.keys():
            missing = ", ".join(sorted(FIELDS - a.keys()))
            hint = "; run readme.py tags" if missing == "tags" else ""
            raise Refused(f"{where}: needs {missing}{hint}")
        tags = split_tags(a["tags"])
        bad = [t for t in tags if not NAME.fullmatch(t)]
        if bad or len(tags) > MAX_TAGS or len(set(tags)) < len(tags):
            raise Refused(f"{where}: tags are up to {MAX_TAGS} distinct lowercase words joined by -: {a['tags']!r}")  # fmt: skip
        if tagged and not tags:
            raise Refused(f"{where}: no tags; run readme.py tags")
        if a["section"] not in NAMES:
            raise Refused(f"{where}: no section {a['section']!r}")
        if a["source"] not in SOURCES:
            raise Refused(f"{where}: source is bot, box or new")
        writes = [w.strip() for w in a["writes"].split(",")]
        bad = [w for w in writes if w not in WRITES and not any(ROOT.glob(w))]
        if bad or ("nothing" in writes and len(writes) > 1):
            raise Refused(f"{where}: writes is nothing, or any of record, to, or a file of the repo: {a['writes']!r}")  # fmt: skip
        if not a["network"].strip():
            raise Refused(f"{where}: network is none, loopback, or what it reaches and why")  # fmt: skip
        if a["kind"] == "deps" and not a.get("needs"):
            raise Refused(f"{where}: a deps add-on says what it needs")
        if a["kind"] == "stdlib" and a.get("needs"):
            raise Refused(f"{where}: a stdlib add-on needs nothing")
        if a["built"] and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.get("added", "")):
            raise Refused(f"{where}: added is the date it was built, YYYY-MM-DD")
    return out


# ── the sections ─────────────────────────────────────────────────────────────
def split_tags(text: str) -> list[str]:
    return [t.strip() for t in str(text).split(",") if t.strip()]


def facts(a: dict) -> str:
    """What a card promises that a reader must see, in words, whatever its
    tags say: what it needs installed, and where it goes."""
    out = []
    if a["kind"] == "deps":
        out.append(f"Needs {a['needs']}.")
    if a["network"] == "loopback":
        out.append("Reaches this machine only.")
    elif a["network"] != "none":
        out.append(f"Goes online: {a['network']}.")
    return "".join(f" {f}" for f in out)


def entry(a: dict) -> str:
    name = (
        f"[**{a['name']}**]({a['path']})" if a["built"] else f"**{a['name']}** (idea)"
    )
    tags = " ".join(f"`{t}`" for t in split_tags(a["tags"]))
    return f"- {name} — {a['line']}{facts(a)} *{a['source']}* {tags}"


def auto_tags(a: dict) -> list[str]:
    """Four tags from what the card already says, for an entry that has none;
    the fifth is left for a person to choose."""
    writes = split_tags(a["writes"])
    out = [
        "no-install" if a["kind"] == "stdlib" else "needs-install",
        {"none": "offline", "loopback": "this-machine"}.get(a["network"], "online"),
        "read-only" if writes == ["nothing"] else "records" if "record" in writes
        else "writes-output",
        SECTION_TAG[a["section"]],
    ]  # fmt: skip
    return out


def fill_tags() -> int:
    """Write tags into every card and idea that has none; touch no others."""
    every = addons(tagged=False)
    filled = 0
    for a in every:
        if split_tags(a["tags"]):
            continue
        line = ", ".join(auto_tags(a))
        if a["built"]:
            card_file = ROOT / a["path"] / "README.md"
            text = card_file.read_text(encoding="utf-8")
            end = text.index("\n-->\n")
            card_file.write_text(
                text[:end] + f"\ntags: {line}" + text[end:], encoding="utf-8"
            )
        else:
            a["tags"] = line
        filled += 1
    planned = json.loads(PLANNED.read_text(encoding="utf-8"))
    tags = {a["name"]: a["tags"] for a in every if not a["built"]}
    for e in planned:
        e["tags"] = e.get("tags") or tags[e["name"]]
    PLANNED.write_text(
        json.dumps(planned, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"tags filled for {filled} add-ons and ideas; the rest kept as written")
    return kernel.ALIVE


def section_list(every: list[dict]) -> str:
    lines = ["**Contents:** " + " · ".join(
        f"[{s}](#{re.sub(r'[^a-z0-9 -]', '', s.lower()).replace(' ', '-')})" for s in NAMES
    )]  # fmt: skip
    for title, intro in SECTIONS:
        lines += ["", f"### {title}", ""]
        if intro:
            lines += [intro, ""]
        lines += [
            entry(a)
            for a in sorted(every, key=lambda a: a["name"])
            if a["section"] == title
        ]
    return "\n".join(lines)


def section_pools(every: list[dict]) -> str:
    built = sum(a["built"] for a in every)
    bar = round(20 * built / len(every))
    lines = [
        f"`{'█' * bar}{'░' * (20 - bar)}` **{built} of {len(every)} built**"
        f" · {sum(a['kind'] == 'stdlib' for a in every)} need no install"
        f" · {sum(a['kind'] == 'deps' for a in every)} need one",
        "",
        "| Section | Built | Ideas | No install | Needs one |",
        "|---|---|---|---|---|",
    ]
    for title in NAMES:
        mine = [a for a in every if a["section"] == title]
        lines.append(
            f"| {title} | {sum(a['built'] for a in mine)} | {sum(not a['built'] for a in mine)}"
            f" | {sum(a['kind'] == 'stdlib' for a in mine)} | {sum(a['kind'] == 'deps' for a in mine)} |"
        )
    return "\n".join(lines)


def section_newest(every: list[dict]) -> str:
    built = sorted(
        (a for a in every if a["built"]), key=lambda a: (a["added"], a["name"])
    )
    return "\n".join(
        f"- {a['added']} · [**{a['name']}**]({a['path']}) — {a['line']}"
        for a in reversed(built[-5:])
    )


def section_pick(every: list[dict], week: str) -> str:
    """One built add-on, drawn by the SHA-256 of the week: the same week
    always draws the same one, and anyone can redo the draw."""
    built = sorted(a["name"] for a in every if a["built"])
    if not built:
        return "Nothing is built yet."
    seed = kernel.h256(f"willow add-on of the week {week}")
    a = next(x for x in every if x["name"] == built[int(seed, 16) % len(built)])
    return (
        f"**[{a['name']}]({a['path']})** — {a['line']}\n\n"
        f'*Drawn for {week}: SHA-256 of "willow add-on of the week {week}",'
        f" modulo the {len(built)} built add-ons in name order.*"
    )


# ── the README ───────────────────────────────────────────────────────────────
BLOCK = re.compile(
    r"<!-- willow:(\w+)((?: \w+=\S+)*) -->\n.*?<!-- /willow:\1 -->", re.S
)
ORDER = ("pools", "newest", "pick", "list")
#: what the front page can show, and the title it shows it under
FRONT = {
    "pick": "Add-on of the week",
    "newest": "Newest",
    "pools": "How the list stands",
}


def this_week() -> str:
    y, w, _ = date.today().isocalendar()
    return f"{y}-W{w:02d}"


def rebuild(text: str, week: str | None, needs: tuple = ORDER, page: str = "ADDONS.md") -> str:  # fmt: skip
    every = addons()
    found = [m.group(1) for m in BLOCK.finditer(text)]
    if sorted(found) != sorted(needs):
        raise Refused(
            f"{page}'s sections are {found}; it needs one each of {list(needs)}"
        )

    def drawn(attrs: dict) -> str:
        attrs["week"] = week or attrs.get("week") or this_week()
        if not re.fullmatch(r"\d{4}-W\d{2}", attrs["week"]):
            raise Refused(f"week {attrs['week']!r} is YYYY-Www")
        return section_pick(every, attrs["week"])

    def made(name: str, attrs: dict) -> str:
        if name == "pick":
            return drawn(attrs)
        return {"pools": section_pools, "newest": section_newest,
                "list": section_list}[name](every)  # fmt: skip

    def fill(m: re.Match) -> str:
        name, attrs = m.group(1), dict(a.split("=") for a in m.group(2).split())
        if name == "front":
            show = attrs.get("show", "")
            if show not in FRONT:
                raise Refused(f"front shows one of {', '.join(FRONT)}, not {show!r}")
            if show != "pick":
                attrs.pop("week", None)
            built = sum(a["built"] for a in every)
            body = (f"**{FRONT[show]}**\n\n{made(show, attrs)}\n\n"
                    f"[Every add-on, {built} built of {len(every)}, and how to add one: "
                    "ADDONS.md](ADDONS.md)")  # fmt: skip
        else:
            body = made(name, attrs)
        head = "".join(f" {k}={v}" for k, v in sorted(attrs.items()))
        return f"<!-- willow:{name}{head} -->\n{body}\n<!-- /willow:{name} -->"

    return BLOCK.sub(fill, text)


def pages() -> list[tuple[Path, tuple]]:
    """Each page readme.py writes, and the sections it holds."""
    return [(ADDONS_MD, ORDER), (README, ("front",))]


def main(argv: list[str]) -> int:
    verb, rest = (argv[0], argv[1:]) if argv else ("", [])
    week = None
    if rest[:1] == ["--week"] and len(rest) == 2:
        week, rest = rest[1], []
    if verb == "tags" and not rest:
        try:
            return fill_tags()
        except Refused as e:
            print(f"refused: {e}", file=sys.stderr)
            return kernel.REFUSED
    if rest or verb not in ("write", "check") or (week and verb == "check"):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    week = this_week() if verb == "write" and not week else week
    stale = []
    for path, needs in pages():
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        try:
            new = rebuild(text, week, needs, path.name)
        except Refused as e:
            print(f"refused: {e}", file=sys.stderr)
            return kernel.REFUSED
        if verb == "write":
            path.write_text(new, encoding="utf-8")
            print(f"{path.name}: generated sections written")
        elif new != text:
            stale.append(path.name)
    if verb == "write":
        return kernel.ALIVE
    if stale:
        print(f"{', '.join(stale)} isn't current: run python adapters/stdlib/readme/readme.py write")  # fmt: skip
        return kernel.REFUSED
    print("README.md and ADDONS.md are current")
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
