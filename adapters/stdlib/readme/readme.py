"""readme.py: README.md's generated sections, built from the add-ons themselves.

    python adapters/stdlib/readme/readme.py write [--week YYYY-Www]
    python adapters/stdlib/readme/readme.py check

Each generated section sits between two markers in README.md,
`<!-- willow:NAME -->` and `<!-- /willow:NAME -->`; everything outside them is
written by hand and never touched. `write` rebuilds every section in place.
`check` rebuilds them in memory and exits 2 if README.md differs, so a section
can't go stale: the add-on's tests run it on every push.

The sections, in this order:

    pools    how the add-ons spread: by section, built and planned, 🐍 and 📦
    newest   the five most recently added add-ons that are built
    pick     the add-on of the week, drawn from the built ones by a hash of
             the week, so anyone can recompute the draw
    list     every add-on, built and planned, by section, A to Z

What it reads:

- each built add-on's card (`README.md` in its folder under `adapters/stdlib/`
  or `adapters/deps/`), which opens with a header:

      <!-- willow-addon
      section: Keeping track
      line: Numbers over time and a date gone by, beside an answer.
      source: box
      added: 2026-10-22
      -->

  plus `needs:` and `network:` for one in `adapters/deps/`;
- `adapters/planned.json`, the add-ons not built yet, with the same fields
  and a `kind` (stdlib or deps).

A name is built when its folder exists, and then it must not also be planned.
Nothing is decided by hand in the list: building an add-on is what turns its
🛠 into ✅.

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
FIELDS = {"section", "line", "source"}
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


def addons() -> list[dict]:
    """Every add-on, built and planned, each checked; refused on the first
    that doesn't hold together."""
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
        if not FIELDS <= a.keys():
            raise Refused(f"{where}: needs {', '.join(sorted(FIELDS - a.keys()))}")
        if a["section"] not in NAMES:
            raise Refused(f"{where}: no section {a['section']!r}")
        if a["source"] not in SOURCES:
            raise Refused(f"{where}: source is bot, box or new")
        if a["kind"] == "deps" and not a.get("needs"):
            raise Refused(f"{where}: a deps add-on says what it needs")
        if a["kind"] == "stdlib" and a.get("needs"):
            raise Refused(f"{where}: a stdlib add-on needs nothing")
        if a["built"] and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.get("added", "")):
            raise Refused(f"{where}: added is the date it was built, YYYY-MM-DD")
    return out


# ── the sections ─────────────────────────────────────────────────────────────
def mark(a: dict) -> str:
    out = "🐍" if a["kind"] == "stdlib" else f"📦 [{a['needs']}]"
    if a.get("network"):
        out += f" 🌐 {a['network']}"
    return out


def entry(a: dict) -> str:
    name = f"[**{a['name']}**]({a['path']})" if a["built"] else f"**{a['name']}**"
    return f"- {'✅' if a['built'] else '🛠'} {name} {mark(a)} — {a['line']} *{a['source']}*"


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
        f" · {sum(a['kind'] == 'stdlib' for a in every)} 🐍"
        f" · {sum(a['kind'] == 'deps' for a in every)} 📦",
        "",
        "| Section | Built | Planned | 🐍 | 📦 |",
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


def this_week() -> str:
    y, w, _ = date.today().isocalendar()
    return f"{y}-W{w:02d}"


def rebuild(text: str, week: str | None) -> str:
    every = addons()
    found = [m.group(1) for m in BLOCK.finditer(text)]
    if sorted(found) != sorted(ORDER):
        raise Refused(
            f"README.md's sections are {found}; it needs one each of {list(ORDER)}"
        )

    def fill(m: re.Match) -> str:
        name, attrs = m.group(1), dict(a.split("=") for a in m.group(2).split())
        if name == "pick":
            attrs["week"] = week or attrs.get("week") or this_week()
            if not re.fullmatch(r"\d{4}-W\d{2}", attrs["week"]):
                raise Refused(f"week {attrs['week']!r} is YYYY-Www")
            body = section_pick(every, attrs["week"])
        else:
            body = {
                "pools": section_pools,
                "newest": section_newest,
                "list": section_list,
            }[name](every)
        head = "".join(f" {k}={v}" for k, v in sorted(attrs.items()))
        return f"<!-- willow:{name}{head} -->\n{body}\n<!-- /willow:{name} -->"

    return BLOCK.sub(fill, text)


def main(argv: list[str]) -> int:
    verb, rest = (argv[0], argv[1:]) if argv else ("", [])
    week = None
    if rest[:1] == ["--week"] and len(rest) == 2:
        week, rest = rest[1], []
    if rest or verb not in ("write", "check") or (week and verb == "check"):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    text = README.read_text(encoding="utf-8")
    try:
        new = rebuild(text, this_week() if verb == "write" and not week else week)
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    if verb == "write":
        README.write_text(new, encoding="utf-8")
        print("README.md: generated sections written")
        return kernel.ALIVE
    if new != text:
        print(
            "README.md isn't current: run python adapters/stdlib/readme/readme.py write"
        )
        return kernel.REFUSED
    print("README.md is current")
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
