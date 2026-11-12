"""readme.py: the add-on list and the front page's feature, built from the
add-ons themselves.

    python adapters/stdlib/readme/readme.py write [--week YYYY-Www]
    python adapters/stdlib/readme/readme.py check

Each generated section sits between two markers, `<!-- willow:NAME -->` and
`<!-- /willow:NAME -->`; everything outside them is written by hand and never
touched. `write` rebuilds every section in place. `check` rebuilds them in
memory and exits 2 if a page differs, so a section can't go stale: the
add-on's tests run it on every push. A generated section is a view of the
cards, recomputed each time, never kept by hand (CONST-VI-6).

ADDONS.md holds these sections, in this order:

    pools    how the add-ons spread: by section, built and ideas, and how
             many need an install
    languages
             the language packs, `words-` and a language's code, built and
             planned, A to Z by code
    newest   the five most recently added add-ons that are built
    pick     the add-on of the week, drawn from the built ones by a hash of
             the week, so anyone can recompute the draw
    list     every add-on, built and planned, by section, then by the
             role and group groups.py gives it (the UI's own), the built
             ones first and the ideas after, A to Z; each an anchor,
             `#name`, and two lines: its line, then what it needs, where
             it goes online and its tags

README.md holds two: `summary`, one line per section saying what it's for,
with a built example or two; and `front`, one of pools, newest or
pick, as its `show=` says (`<!-- willow:front show=pick week=2026-W43 -->`),
and a link to the rest. To switch the front page's feature, change `show=`
and run `write`.

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
      role: page
      tags: health
      -->

  plus `needs:` and `floor:` for one in `adapters/deps/`;
- `adapters/planned.json`, the add-ons not built yet, with the same fields
  and a `kind` (stdlib or deps).

A name is built when its folder exists, and then it must not also be planned.
Nothing is decided by hand in the list: building an add-on is what turns its
an idea into a built one.

`role` is the part it plays in a stack, which the UI's steps are made of:

    reads     turns a kind of file into text the kernel can search
    words     a words list, a language's or your own, that changes what a
              question finds
    page      runs with nothing but your record, as a step on your page
    suggests  suggests an answer, held until you seal it, or checks a model
              that does
    ways      where you ask from: a terminal, an editor, an assistant, a page
    guards    keeps something from being shown or done: a hook, a filter
    makes     makes a file for another program, where you point it
    tools     you run it yourself, with words or options of its own
    repo      works on willow's own repository, as runs-in: repo says

A reader (`role: reads`) says what it reads, `reads: .eml, .mbox`: the
kinds of file, by extension, or a file it looks for by name
(`zotero.sqlite`), with commas between; `none` for one that reads no kind
of file (a repository, a page it fetches). The UI offers a reader by it for
the files a folder holds that the kernel can't read, and
ci/test_contract.py holds each one to the reader's own code.

What an add-on leans on is on its card, never found by reading its code:

    uses:       the add-ons it needs beside it, to run or to be tested; a
                stack that has it has these too
    looks-for:  the add-ons it uses when they're beside it; without one it
                still runs and says what's missing, and its tests hold
                either way
    runs-in:    repo, for a tool that works on willow's own repository (CI,
                the list, the branches); it isn't copied out of it
    output:     report, for one that prints a report: a line saying what it
                found, then its rows by group, each where and what, the
                same shape as every other report and the same as JSON with
                --json (adapters/stdlib/ci/README.md, the report contract);
                mirror, for a reader whose mirror says where each passage
                came from, in a hidden map beside it (the mirror
                contract); suggestions, for one that proposes a model's
                reply for your seal: its claim says who answered, where, at
                what settings and what it did, in one form (the suggestions
                contract); more than one, with commas between

Each is optional, a list of add-on names with commas between. `check`
refuses a name that isn't an add-on (built, for a built one), the add-on
itself, or a name in both lists.

Tags: each entry in the list shows up to five, worked out by the similar
add-on: whether it needs an install, whether it goes online, two topic words
it shares with its nearest entries, and the one tag its author chose, if
any. That one is a card's `tags:` line (or an idea's
`tags`), optional: a lowercase word or words joined by -, and never one of
the worked-out ones. `similar.py tags NAME` shows what an entry gets. Each
entry also names the three entries nearest it.

**The tags and the nearest entries stand for the week**, as the counts do.
They're worked out over every card's whole text, so any pull request that
adds an entry, or edits any card, would move other entries' lines too, and
each such pull request made every other one's list stale. So the first
`write` of a week works them out for every entry and keeps them in
`adapters/stdlib/readme/week.json`; for the rest of that week each entry the
file names keeps its line's tags and nearest entries, and only an entry it
doesn't name (new this week) is worked out, its own line alone, against
the week's entries and itself; the counts, too, are the week's entries, and a
new one counts from the next week. A card's
changed tags show from the next week's first write. `check` holds the file
too: a week it doesn't match is stale.

The week of `pick` is part of the section (`<!-- willow:pick week=2026-W43
-->`). `write` sets it to this week, or to `--week`; `check` rebuilds with the
week already there, so the same repo always gives the same README.

Exit codes, the kernel's: 0 done or current; 2 refused, or README.md not
current.
"""

from __future__ import annotations

import importlib.util
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
#: each entry's tags and nearest entries, as the week's first write found them
WEEK_FILE = ROOT / "adapters" / "stdlib" / "readme" / "week.json"
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
     " approve: every suggestion waits for your seal. Two ways in: MCP"
     " tools the host calls when it asks ([hosts](adapters/stdlib/hosts/),"
     " [mcp-lite](adapters/stdlib/mcp-lite/)), and a prompt hook that cites"
     " your passages at each prompt where the host allows it"
     " ([claude-code](adapters/stdlib/claude-code/);"
     " [hooks-elsewhere](adapters/stdlib/hooks-elsewhere/) for the rest)."),
    ("Ways to use it", ""),
    ("Play", ""),
    ("For maintainers", ""),
]  # fmt: skip
NAMES = [s for s, _ in SECTIONS]
#: what each section is for, in a phrase, for the README's summary
WHAT = {
    "Reading more kinds of files": "PDFs, email, chats, calendars, notes and office files, as text it can search",
    "Finding things": "more ways to look: every match, this date in past years, an exact quote, by meaning, past typos",
    "Your own words": "teaching it the words you use, so a question finds what your files call it",
    "Keeping track": "dates coming up, numbers over time, to-dos, care logs, invoices, forecasts and flashcards",
    "Trust and proof": "answers you can check later: exports, stale answers, what changed, signed and encrypted records",
    "Privacy and safety": "phone numbers, card numbers and keys hidden in answers, or found sitting in files",
    "Assistants": "AI assistants that can ask and suggest, but never approve",
    "Ways to use it": "other ways in: pipes, your shell and your editor, plain sentences, a page on this machine, answers read aloud",
    "Play": "seeded, replayable games on the record, such as dice and the Game of Life",
    "For maintainers": "the repo's own tools: CI, the list, tests that can fail",
}  # fmt: skip
#: built add-ons that show what a section is like, for the README's summary:
#: chosen by hand, and checked to be built and in that section
EXAMPLES = {
    "Reading more kinds of files": ["pdf", "mail"],
    "Finding things": ["on-this-day", "quote-check"],
    "Your own words": ["nicknames", "abbreviations"],
    "Keeping track": ["coming-up", "subscriptions"],
    "Trust and proof": ["stale", "tip-pin"],
    "Privacy and safety": ["privacy", "secrets-audit"],
    "Assistants": ["claude-code", "mcp"],
    "Ways to use it": ["browse", "print"],
    "Play": ["quiz", "life"],
    "For maintainers": ["mutants", "ci"],
}  # fmt: skip
FIELDS = {"section", "line", "source", "writes", "network", "role", "version"}
#: a version, MAJOR.MINOR.PATCH (CONTRIBUTING.md, Releases): an idea is 0.0.N
#: from 0.0.1, and its first build is 0.1.0; adapters/stdlib/ci/versions.py
#: holds each step a pull request takes
VERSION = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
#: the part an add-on plays in a stack (the docstring says each), from the
#: one grouping the UI and the lists share (groups.py, beside this)
_groups_spec = importlib.util.spec_from_file_location(
    "willow_groups_for_readme", Path(__file__).resolve().parent / "groups.py"
)
groups = importlib.util.module_from_spec(_groups_spec)
_groups_spec.loader.exec_module(groups)
ROLES = {key for key, _ in groups.ROLES}
#: what an add-on leans on, by name: optional, and checked against the list
LEANS = ("uses", "looks-for")
RUNS_IN = {"repo"}
#: what an add-on prints, when it keeps a shared shape: ci/README.md
OUTPUTS = {"report", "mirror", "suggestions"}
#: the tags the similar add-on works out, which a card's own tag is never one of
FACT_TAGS = {
    "no-install",
    "needs-install",
    "offline",
    "this-machine",
    "online",
    "to-a-model",
}
#: what an add-on may write: the guard in adapters/stdlib/ci/guard holds it
#: to this while its tests run; a file of the repo may also be named
WRITES = {"nothing", "record", "to"}
SOURCES = {"bot", "box", "new"}
#: where an add-on's idea or code was taken from, beside `source`: how it was
#: taken (its shape rebuilt, its code ported, or the project depended on), the
#: address, and that project's licence; several joined with ;
FROM_HOW = {"shape", "code", "dep"}
FROM_URL = re.compile(r"https://[^\s,;]+")
#: a licence as SPDX writes one (MIT, BSD-3-Clause, MIT OR Apache-2.0), or none
LICENCE = re.compile(r"none|[A-Za-z0-9.+-]+(?: (?:OR|AND|WITH) [A-Za-z0-9.+-]+)*")
#: a licence Apache-2.0 code can't take code from: copyleft, or source-available
COPYLEFT = re.compile(r"\b(?:A?GPL|LGPL|SSPL|BUSL|EUPL|OSL|CC-BY-(?:NC|SA|ND))", re.I)
#: the source's own notice, kept beside code taken from it
NOTICE_FILE = re.compile(r"(?:NOTICE|LICEN[CS]E|COPYING)(?:[-._].*)?", re.I)
#: every key a card's header or an idea may carry; any other is refused, so a
#: field spelt wrong is never read as one left out
KEYS = {"section", "line", "source", "writes", "network", "role", "added", "tags",
        "uses", "looks-for", "reads", "output", "needs", "floor", "programs",
        "runs-in", "from", "hands", "version"}  # fmt: skip
IDEA_KEYS = (KEYS - {"added"}) | {"name", "kind"}
HEADER = re.compile(r"\A<!-- willow-addon\n(.*?)\n-->\n", re.S)
#: a kind of file a reader reads: .ext, or a file name it looks for
KIND = re.compile(r"\.?[A-Za-z0-9][A-Za-z0-9_.+-]*")
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
#: what in an add-on's code hands text to another program that may send it
#: on: a hook's context, an MCP server's results, a sampling request. Its
#: card says so in `hands` (CONST-III-5); a plain-stdout hook can't be told
#: from its code, so this is a floor, and the hands stack the rest
HANDS_SIGNS = re.compile(
    r'additionalContext|sampling/createMessage|"jsonrpc"|mcp\.server'
)
#: an add-on whose code holds a sign and hands nothing, and why
NOT_HANDED = {
    "robinhood": "fake_robinhood.py is a stand-in for Robinhood's server in its "
    "tests; robinhood reads from that server and hands nothing to a model",
    "readme": "readme.py names the signs, to look for them",
}
#: a language pack: words- and the language's ISO 639 code
LANGUAGE = re.compile(r"words-([a-z]{2,3})")


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
            missing = ", ".join(sorted(FIELDS - a.keys()))
            raise Refused(f"{where}: needs {missing}")
        if len(a["line"]) > LINE:
            raise Refused(f"{where}: its line is {len(a['line'])} characters, and a"
                          f" line is at most {LINE}, so the list reads in one look")  # fmt: skip
        a.setdefault("tags", "")
        tags = split_tags(a["tags"])
        if len(tags) > 1 or any(not NAME.fullmatch(t) for t in tags):
            raise Refused(f"{where}: tags is your one tag, lowercase words joined by -, the rest are worked out: {a['tags']!r}")  # fmt: skip
        if set(tags) & FACT_TAGS:
            raise Refused(f"{where}: {tags[0]} is worked out from the card; tags is for a tag of your own")  # fmt: skip
        if a["section"] not in NAMES:
            raise Refused(f"{where}: no section {a['section']!r}")
        if a["source"] not in SOURCES:
            raise Refused(f"{where}: source is bot, box or new")
        unknown = sorted(
            set(a)
            - (KEYS if a["built"] else IDEA_KEYS)
            - {"name", "kind", "built", "path"}
        )
        if unknown:
            raise Refused(f"{where}: {', '.join(unknown)} is not a card's field: {', '.join(sorted(KEYS))}")  # fmt: skip
        origins(a, where)
        # CONST-II-1: what an add-on writes and where it goes online is listed
        # on its card, idea or built, never inferred from its code
        writes = [w.strip() for w in a["writes"].split(",")]
        bad = [w for w in writes if w not in WRITES and not any(ROOT.glob(w))]
        if bad or ("nothing" in writes and len(writes) > 1):
            raise Refused(f"{where}: writes is nothing, or any of record, to, or a file of the repo: {a['writes']!r}")  # fmt: skip
        if not a["network"].strip():
            raise Refused(f"{where}: network is none, loopback, or what it reaches and why")  # fmt: skip
        ver = VERSION.fullmatch(str(a["version"]))
        if not ver:
            raise Refused(f"{where}: version is MAJOR.MINOR.PATCH, such as 0.1.0: {a['version']!r}")  # fmt: skip
        if a["built"] and ver.group(1, 2) == ("0", "0"):
            raise Refused(f"{where}: a built add-on is 0.1.0 or later, its first build 0.1.0: {a['version']}")  # fmt: skip
        if not a["built"] and (ver.group(1, 2) != ("0", "0") or ver.group(3) == "0"):
            raise Refused(f"{where}: an idea is 0.0.N, from 0.0.1, until it is built: {a['version']}")  # fmt: skip
        # CONST-III-5: what leaves is stated before it leaves. network is what
        # the add-on itself connects to; hands is what it gives a program that
        # may send it on (an assistant's model), and to whom
        if "hands" in a and a["hands"].strip() in ("", "none"):
            raise Refused(f"{where}: hands is what it gives another program and to whom; leave it off when it hands nothing")  # fmt: skip
        if a["built"] and "hands" not in a and a["name"] not in NOT_HANDED:
            signs = [p.name for p in sorted((ROOT / a["path"]).iterdir())
                     if p.suffix in (".py", ".js", ".ts") and not p.name.startswith("test_")
                     and HANDS_SIGNS.search(p.read_text(encoding="utf-8", errors="replace"))]  # fmt: skip
            if signs:
                raise Refused(f"{where}: {', '.join(signs)} hands text to another program, and the card has no hands line")  # fmt: skip
        if a["kind"] == "deps" and not a.get("needs"):
            raise Refused(f"{where}: a deps add-on says what it needs")
        if a["kind"] == "stdlib" and a.get("needs"):
            raise Refused(f"{where}: a stdlib add-on needs nothing")
        # programs: what ci.py asks PATH for before a deps add-on's tests, so a
        # machine without one is unreachable there, never failing
        programs = a.get("programs", "").replace(",", " ").split()
        if programs and a["kind"] != "deps":
            raise Refused(f"{where}: only a deps add-on names programs")
        unsaid = [p for p in programs if p not in a.get("needs", "")]
        if unsaid:
            raise Refused(f"{where}: programs names {', '.join(unsaid)}, which needs doesn't")  # fmt: skip
        if a["built"] and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.get("added", "")):
            raise Refused(f"{where}: added is the date it was built, YYYY-MM-DD")
        if a.get("runs-in", "repo") not in RUNS_IN:
            raise Refused(f"{where}: runs-in is repo, or left out")
        if a["role"] not in ROLES:
            raise Refused(f"{where}: role is one of {', '.join(sorted(ROLES))}: {a['role']!r}")  # fmt: skip
        if (a["role"] == "repo") != (a.get("runs-in") == "repo"):
            raise Refused(f"{where}: role is repo exactly when runs-in is repo")
        if a.get("reads") and a["role"] != "reads":
            raise Refused(f"{where}: reads is for a card whose role is reads")
        if a["role"] == "reads" and a["built"] and not a.get("reads"):
            raise Refused(f"{where}: a reader says what it reads: reads: .ext, a file name, or none")  # fmt: skip
        if (
            a.get("reads")
            and a["reads"] != "none"
            and not all(KIND.fullmatch(k.strip()) for k in a["reads"].split(","))
        ):
            raise Refused(f"{where}: reads is .ext or a file name, with commas between, or none: {a['reads']!r}")  # fmt: skip
        said = [o.strip() for o in a.get("output", "report").split(",")]
        if not set(said) <= OUTPUTS or len(set(said)) != len(said):
            raise Refused(f"{where}: output is one of {', '.join(sorted(OUTPUTS))}, with commas between, or left out")  # fmt: skip
        if "mirror" in said and a["role"] != "reads":
            raise Refused(f"{where}: output mirror is for a card whose role is reads")
    names = {a["name"]: a["built"] for a in out}
    for a in out:
        where = a.get("path") or f"planned.json: {a['name']}"
        lists = {k: split_tags(a.get(k, "")) for k in LEANS}
        for k, got in lists.items():
            for n in got:
                if n == a["name"]:
                    raise Refused(f"{where}: {k} names the add-on itself")
                if n not in names or (a["built"] and not names[n]):
                    raise Refused(f"{where}: {k} names {n!r}, which isn't a built add-on")  # fmt: skip
        if set(lists["uses"]) & set(lists["looks-for"]):
            raise Refused(f"{where}: an add-on is in uses or looks-for, not both")
    return out


def origins(a: dict, where: str) -> list[tuple[str, str, str]]:
    """Its `from`, each part (how, address, licence), checked: refused when a
    part doesn't hold together, or takes what an Apache-2.0 add-on can't."""
    out = []
    for part in [p.strip() for p in a.get("from", "").split(";") if p.strip()]:
        bits = [b.strip() for b in part.split(",")]
        if len(bits) != 3 or bits[0] not in FROM_HOW:
            raise Refused(f"{where}: from is how (shape, code or dep), the address, and its licence, ; between each: {part!r}")  # fmt: skip
        how, url, licence = bits
        if not FROM_URL.fullmatch(url):
            raise Refused(f"{where}: from's address is an https:// link: {url!r}")
        if not LICENCE.fullmatch(licence):
            raise Refused(f"{where}: from's licence is one SPDX writes (MIT, BSD-3-Clause) or none: {licence!r}")  # fmt: skip
        if how != "shape" and licence == "none":
            raise Refused(f"{where}: from takes {how} only under a licence: a project with none gives only a shape")  # fmt: skip
        if how == "code" and COPYLEFT.search(licence):
            raise Refused(f"{where}: from takes code under {licence}, which an Apache-2.0 add-on can't: take its shape")  # fmt: skip
        if how == "dep" and a["kind"] != "deps":
            raise Refused(
                f"{where}: from dep is for a deps add-on, which says it in needs"
            )
        if how == "code" and a["built"]:
            folder = ROOT / a["path"]
            if not any(
                NOTICE_FILE.fullmatch(f.name) for f in folder.iterdir() if f.is_file()
            ):
                raise Refused(f"{where}: code taken from {url} keeps its notice: a NOTICE, LICENSE or COPYING file beside it")  # fmt: skip
        out.append((how, url, licence))
    return out


def origin_words(a: dict) -> str:
    """Its `from`, in words for the list: how, a link to where, and the licence."""
    said = []
    for how, url, licence in origins(a, ""):
        short = re.sub(r"^https://(?:www\.)?(?:github\.com/)?", "", url).rstrip("/")
        said.append(f"{how} of [{short}]({url}), {licence}")
    return f" From: {'; '.join(said)}." if said else ""


# ── the sections ─────────────────────────────────────────────────────────────
def split_tags(text: str) -> list[str]:
    return [t.strip() for t in str(text).split(",") if t.strip()]


def facts(a: dict) -> str:
    """What a card promises that a reader must see, in words, whatever its
    tags say: what it needs installed, and where it goes."""
    return "".join(f" {f}" for f in said_facts(a))


def said_facts(a: dict) -> list[str]:
    out = []
    if a["kind"] == "deps":
        out.append(f"Needs {a['needs']}.")
    if a.get("uses"):
        out.append(f"Uses {', '.join(split_tags(a['uses']))}.")
    if a["network"] == "loopback":
        out.append("Reaches this machine only.")
    elif a["network"] != "none":
        out.append(f"Goes online: {a['network']}.")
    if a.get("hands"):
        out.append(f"Hands on {a['hands']}.")
    return out


#: a card's or an idea's line at most, so with its entry's indent it reads in
#: one look (skim's width); a generated line past WIDTH is wrapped (wrap)
LINE = 140
WIDTH = 158


def words_of(text: str) -> list[str]:
    """Text cut at the spaces a line may break at: not inside a link's [text]
    or its (address), so a link and what's stuck to it stay one word. A
    plain parenthesis in prose breaks like any other words."""
    out, word, text_depth, in_address, prev = [], "", 0, False, ""
    for ch in text:
        if ch == "[":
            text_depth += 1
        elif ch == "]" and text_depth:
            text_depth -= 1
        elif ch == "(" and prev == "]" and not text_depth:
            in_address = True
        elif ch == ")" and in_address:
            in_address = False
        if ch == " " and not text_depth and not in_address:
            if word:
                out.append(word)
            word = ""
        else:
            word += ch
        prev = ch
    return out + ([word] if word else [])


def wrap(text: str, indent: str = "") -> str:
    """Text as lines of WIDTH or fewer, after `indent`, broken only between
    words and never inside a link: Markdown reads it as the same paragraph."""
    out, line = [], ""
    for word in words_of(text):
        if line and len(indent) + len(line) + 1 + len(word) > WIDTH:
            out.append(line)
            line = word
        else:
            line = f"{line} {word}" if line else word
    out.append(line)
    return "\n".join(indent + x for x in out)


def entry(a: dict, worked: dict) -> str:
    """One add-on, three short lines: its anchor and name; its line; then
    what it needs and where it goes online, in words, and its tags and
    nearest (a `\\` breaks each line, so it stays one entry). The line is
    the card's own, so a long one is the card's to shorten."""
    name = (
        f"[**{a['name']}**]({a['path']})" if a["built"] else f"**{a['name']}** (idea)"
    )
    tags = " ".join(f"`{t}`" for t in worked["tags"])
    near = f" · near: {', '.join(worked['near'])}" if worked["near"] else ""
    # what it needs, where it goes online, and where it came from (its `from`)
    said = (" ".join(said_facts(a)) + origin_words(a)).strip()
    rest = wrap(f"{said + ' ' if said else ''}*{a['source']}* {tags}{near}", "  ")
    return f'- <a id="{a["name"]}"></a>{name} \\\n  {a["line"]} \\\n{rest}'


def placed(a: dict) -> tuple[int, int, str]:
    """Where an entry goes inside its section, by groups.py, the grouping the
    UI shares: its role's place, its group's, and the heading over it (the
    group's title, or the role's when it has no groups)."""
    got = groups.role({"name": a["name"], "section": a["section"], "line": a["line"],
                       "role": a.get("role", ""), "state": "built" if a["built"] else "idea"})  # fmt: skip
    keys = [k for k, _ in groups.ROLES]
    at = keys.index(got["role"]) if got["role"] in keys else len(keys)
    return at, got["group_at"], got["group"] or dict(groups.ROLES).get(got["role"], "Other")  # fmt: skip


def similar_add_on():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "willow_similar", Path(__file__).resolve().parents[1] / "similar" / "similar.py"
    )
    similar = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(similar)
    return similar


def worked_out(every: list[dict], only: set[str] | None = None) -> dict[str, dict]:
    """Each entry's tags and nearest entries, from the similar add-on (only
    those named, when `only` is given)."""
    return similar_add_on().worked_out(every, ROOT, only)


def week_worked(listed: list[dict], week: str) -> tuple[dict[str, dict], dict]:
    """(each listed entry's tags and nearest entries, the week file as it
    should be). Only what the whole list decides is kept for the week, each
    entry's two topic words and its nearest entries; its install and online
    facts and its author's own tag are always read from its card now. A file
    for another week, or none, is made again from every entry; one for this
    week keeps each entry it names, and only an entry it doesn't name is
    worked out, its own line alone."""
    try:
        kept = json.loads(WEEK_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        kept = {}
    if (not isinstance(kept, dict) or kept.get("week") != week
            or not isinstance(kept.get("worked"), dict)):  # fmt: skip
        fresh = worked_out(listed)
        kept = {"week": week, "worked": {n: {"topics": w["topics"], "near": w["near"]}
                                         for n, w in fresh.items()}}  # fmt: skip
    frozen = kept["worked"]
    # a new entry against the week's entries and itself: what another pull
    # request adds this week never reaches its line
    base = [a for a in listed if a["name"] in frozen]
    fresh = {a["name"]: worked_out(base + [a], {a["name"]})[a["name"]]
             for a in listed if a["name"] not in frozen}  # fmt: skip
    similar = similar_add_on()
    worked = {}
    for a in listed:
        w = frozen.get(a["name"]) or fresh[a["name"]]
        tags = similar.facts_tags(a) + list(w["topics"]) + split_tags(a.get("tags", ""))
        worked[a["name"]] = {"tags": tags, "near": list(w["near"])}
    return worked, kept


def week_text(snapshot: dict) -> str:
    return json.dumps(snapshot, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def section_list(every: list[dict], worked: dict[str, dict] | None = None) -> str:
    lines = [wrap("**Contents:** " + " · ".join(
        f"[{s}](#{re.sub(r'[^a-z0-9 -]', '', s.lower()).replace(' ', '-')})" for s in NAMES
    ))]  # fmt: skip
    worked = worked if worked is not None else worked_out(every)
    for title, intro in SECTIONS:
        lines += ["", f"## {title}", ""]
        if intro:
            lines += [wrap(intro), ""]
        # by groups.py's place, the built ones first and the ideas after them
        here = sorted((placed(a), not a["built"], a["name"], a) for a in every if a["section"] == title)  # fmt: skip
        runs: dict[tuple[str, bool], list[dict]] = {}
        for (_, _, head), idea, _, a in here:
            runs.setdefault((head, idea), []).append(a)
        last = None
        for (head, idea), run in runs.items():
            if head != last:
                lines += ([""] if last is not None else []) + [f"### {head}", ""]
                last = head
            title_of = f"{head}: ideas, not built yet" if idea else head
            shown = {a["name"]: entry(a, worked[a["name"]]) for a in run}
            for i, part in enumerate(
                cut(run, lambda a: shown[a["name"]].count("\n") + 1)
            ):
                if idea or i:
                    lines += ["", f"#### {title_of}{letters(part, len(run))}", ""]
                elif len(part) < len(run):
                    lines[-2] = f"### {head}{letters(part, len(run))}"
                lines += [shown[a["name"]] for a in part]
    return "\n".join(lines)


#: the most entries under one heading: three lines each, a screen of skim's 60
RUN = 18
ROOM = 3 * RUN


def cut(run: list[dict], height=lambda a: 3) -> list[list[dict]]:
    """A heading's entries, A to Z, cut into runs as even as they go, each of
    ROOM lines or fewer (RUN entries of three), so no heading holds more than
    a screen; `height` is an entry's lines, more than three when it wraps."""
    total = sum(height(a) for a in run)
    k = -(-total // ROOM)
    out, room = [[]], 0
    for a in run:
        h = height(a)
        if out[-1] and (room + h > ROOM or (room + h > total / k and len(out) < k)):
            out.append([])
            room = 0
        out[-1].append(a)
        room += h
    return out


def letters(part: list[dict], whole: int) -> str:
    """`, a to l`: where a cut run starts and ends, by first letter; nothing
    for a heading that wasn't cut."""
    if len(part) == whole:
        return ""
    return f", {part[0]['name'][0]} to {part[-1]['name'][0]}"


def section_summary(every: list[dict]) -> str:
    """One line per section: what it's for and a built example or two, so the
    front page shows what an add-on is like; the full list is ADDONS.md."""
    built = {a["name"]: a for a in every if a["built"]}
    lines = []
    for title in NAMES:
        shown = [
            f"[{built[n]['name']}]({built[n]['path']})"
            for n in EXAMPLES.get(title, [])
            if n in built and built[n]["section"] == title
        ]
        lines.append(
            f"- **{title}:** {WHAT[title]}."
            + (f" For example {' and '.join(shown)}." if shown else "")
        )
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


def section_languages(every: list[dict]) -> str:
    """The language packs, built and planned, one row each, A to Z by code."""
    packs = sorted(
        (a for a in every if LANGUAGE.fullmatch(a["name"])), key=lambda a: a["name"]
    )
    built = sum(a["built"] for a in packs)
    lines = [
        f"**{built} built, {len(packs) - built} planned**, beside English, which the kernel has built in.",
        "",
        "| Code | Pack | What it does |",
        "|---|---|---|",
    ]  # fmt: skip
    for a in packs:
        code = LANGUAGE.fullmatch(a["name"]).group(1)
        pack = f"[{a['name']}]({a['path']})" if a["built"] else f"{a['name']} *(idea)*"
        lines.append(f"| `{code}` | {pack} | {a['line'].replace('|', chr(92) + '|')} |")
    return "\n".join(lines)


def section_newest(every: list[dict]) -> str:
    built = sorted(
        (a for a in every if a["built"]), key=lambda a: (a["added"], a["name"])
    )
    return "\n".join(
        f"- {a['added']} · [**{a['name']}**]({a['path']}) \\\n  {a['line']}"
        for a in reversed(built[-5:])
    )


def section_pick(every: list[dict], week: str) -> str:
    """One built add-on, drawn by the SHA-256 of the week: the same week
    always draws the same one, and anyone can redo the draw. Its name, then
    its line on a line of its own, as the newest are written: on one line, a
    long name and a long line together pass the width a person reads."""
    built = sorted(a["name"] for a in every if a["built"])
    if not built:
        return "Nothing is built yet."
    seed = kernel.h256(f"willow add-on of the week {week}")
    a = next(x for x in every if x["name"] == built[int(seed, 16) % len(built)])
    return (
        f"**[{a['name']}]({a['path']})** \\\n{a['line']}\n\n"
        f'*Drawn for {week}: SHA-256 of "willow add-on of the week {week}",'
        f" modulo the {len(built)} built add-ons in name order.*"
    )


# ── the README ───────────────────────────────────────────────────────────────
BLOCK = re.compile(
    r"<!-- willow:(\w+)((?: \w+=\S+)*) -->\n.*?<!-- /willow:\1 -->", re.S
)
ORDER = ("pools", "languages", "newest", "pick", "list")
#: what the front page can show, and the title it shows it under
FRONT = {
    "pick": "Add-on of the week",
    "newest": "Newest",
    "pools": "How the list stands",
}


def as_of(every: list[dict], week: str) -> list[dict]:
    """The add-ons as they stood on the week's Monday: one built after it
    counts as the idea it was. The counts, the newest and the week's draw are
    made from this, so a pull request adding an add-on changes its own line
    of the list and nothing every other one's also changes: they conflicted
    in these lines, every merge, until the counts moved only with the week."""
    y, w = (int(x) for x in week.split("-W"))
    monday = date.fromisocalendar(y, w, 1).isoformat()
    return [dict(a, built=False) if a["built"] and a.get("added", "") > monday else a
            for a in every]  # fmt: skip


def week_of(text: str, week: str | None) -> str:
    """The week the page is drawn for: given, else the one it says, else now."""
    m = re.search(r"<!-- willow:\w+[^>]*\bweek=(\d{4}-W\d{2})", text)
    return week or (m.group(1) if m else this_week())


def this_week() -> str:
    y, w, _ = date.today().isocalendar()
    return f"{y}-W{w:02d}"


def rebuild(text: str, week: str | None, needs: tuple = ORDER, page: str = "ADDONS.md",
            worked: dict | None = None, known: set | None = None) -> str:  # fmt: skip
    listed = addons()
    every = as_of(listed, week_of(text, week))
    if (
        known is not None
    ):  # the counts are the week's entries; a new one counts next week
        every = [a for a in every if a["name"] in known]
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
        if name == "list":  # each add-on as it is, its own line
            return section_list(listed, worked)
        return {"pools": section_pools, "languages": section_languages,
                "newest": section_newest, "summary": section_summary}[name](every)  # fmt: skip

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
    return [(ADDONS_MD, ORDER), (README, ("summary", "front"))]


def main(argv: list[str]) -> int:
    verb, rest = (argv[0], argv[1:]) if argv else ("", [])
    week = None
    if rest[:1] == ["--week"] and len(rest) == 2:
        week, rest = rest[1], []
    if rest or verb not in ("write", "check") or (week and verb == "check"):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    week = this_week() if verb == "write" and not week else week
    stale = []
    page = ADDONS_MD.read_text(encoding="utf-8") if ADDONS_MD.is_file() else ""
    try:
        worked, snapshot = week_worked(addons(), week_of(page, week))
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    kept = WEEK_FILE.read_text(encoding="utf-8") if WEEK_FILE.is_file() else ""
    if verb == "write" and kept != week_text(snapshot):
        WEEK_FILE.write_text(week_text(snapshot), encoding="utf-8")
        print(f"{WEEK_FILE.name}: the week's tags and nearest entries written")
    elif kept != week_text(snapshot):
        stale.append(WEEK_FILE.name)
    for path, needs in pages():
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        try:
            new = rebuild(text, week, needs, path.name, worked, set(snapshot["worked"]))
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
