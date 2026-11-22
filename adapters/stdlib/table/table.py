"""table.py: one way to sit at any table on the record. Python 3.9+.

    python adapters/stdlib/table/table.py --box DIR [--words FILE]
    python adapters/stdlib/table/table.py --home FOLDER
    python adapters/stdlib/table/table.py --box DIR bring --as NAME [--at MATTER] "what they bring in"
    python adapters/stdlib/table/table.py --box DIR stands [--at MATTER] [--json]
    python adapters/stdlib/table/table.py moves [--seat host|guest]

A table is a box somebody sits down at: a game night, a call with a
landlord, a meeting. Two seats, and the moves each may make:

    host    the person whose box it is. Says what happened; answers what
            someone brought in; takes a yes back; sets a part aside; pauses;
            ends the sitting. Every one of these is typed at the terminal.
    guest   anyone else: a player, a clerk on the phone, a script, a model.
            One move: bring something in, under a name. It waits.

**Nothing is true at the table until the host says so.** The first form is
the host sitting down. What the host types and says yes to is handed to the
kernel as a suggestion and sealed on that typed yes, by the kernel's own
`seal`, with the key the kernel was given when the box was made; a typed no
is the kernel's `decline`. There is no option that answers for the host, and
nothing here answers on its own: closing it while a call waits leaves the
call waiting.

`bring` is the guest's one move. It hands the words in as a suggestion,
names who brought them, and stops: exit 42, waiting on the host. It can't
seal, and no seat but the host's is ever asked.

**The host's attention is the host's.** Sitting down opens on the host's
own prompt. What guests brought in is counted in one line and left alone:
nothing is asked until the host asks for it, with c. Then the calls come
oldest first, two at a time, each numbered ("3 of 7"); after two, Enter
brings the next two and n leaves the rest waiting. And guests may leave at
most five things waiting: a sixth is refused, with why, until the host has
answered some.

**The front door.** `--home FOLDER` lists the host's tables: each folder
under FOLDER whose box has been sat at or brought to, with how much it holds
true and how many things wait. The host picks one by its number and sits;
when that sitting ends, is paused or is left, they are back at the list, and
Enter leaves. A folder with a stack.md and no box is named under the list: it
can't be asked yet. A line typed there that is no number is a bite, asked at
every table in turn (a choice at a fork is asked once and used at each); when
it went to more than one table, what each want found is gathered into one
list, every line ending with its table and where it is from. A table's own words are read from the words file beside its
box, when it has one, and its title is the name it goes by in the list. A
box nobody has brought a word to is no table yet, and isn't opened to see.

**The first bite.** Sitting down asks "What is the first bite?", and a line
typed there that is no other move is a bite: a question for the host's own
files, asked their way. The forge add-on drafts the steps that could answer
it, a word that could mean more than one is put to the host as one plain
question, and on the host's yes what was drafted is sealed. A bite can also
be a page's name (`read NAME`, or the name alone): the same scan reads the
page, each thing it reaches says the line it came from, and the want goes on
in those words with the page's name, not its text. `say` keeps something as
settled instead, and is the only way a line is kept as true. The bite's
steps are added to the folder's own stack.md (no step twice, under a heading
of its own); a folder whose stack is made from a stack.src is left alone and
the table's prep sheet is used. Then just what the bite asked is run through
the stack add-on, no other step of the stack, and read back a want at a time:
the first few lines each step found, each with where it is from. Each run is
kept in a folder of its own beside the box (bites/001, bites/002). Last, what
the host's other stacks put beside those steps is said, up to three lines;
that only reads, and writes nothing to the record.

**The heads-up.** Before the host decides, what the table already holds true
about the same thing is shown first (the contradictions add-on's rule: the
two share at least two of their own words, and at least half the shorter
one's; it can't tell whether they disagree, and never picks a side). The
host chooses: mine stands now (the new word is sealed, and a replacement is
handed in and sealed with it, so the old one stays on the record and no
longer stands); keep the old one (the new word is not kept; one brought in
is declined); both are true (a row, so the pair isn't raised again); or,
for the host's own word, let me reword it. Without the contradictions
add-on beside this one there is no heads-up, and `moves` says so.

**Taking a yes back.** `u` takes back the last thing made true this
sitting, on the host's y: a replacement whose new word is nothing, sealed.
Nothing takes a seal back; this stands over it.

**Not now, with no reason asked.** `x` at a call sets it aside: nothing is
decided, the call waits, and only that it was set aside is kept (a
`table-x` row: no one named, no reason). `p` at any prompt pauses the whole
sitting the same way (a `table-pause` row), exit 42; sitting down again
picks it up.

**The end.** Enter at the table's prompt ends the sitting: what was made
true this time is read back, a line to remember for next time is kept (a
`table-note` row, the host's own words, shown the next time they sit down),
and on the host's yes the session-seal add-on bundles the sitting and it is
sealed as one, then the record is checked.

`stands` prints what the table holds true now, oldest first, each with the
day it was made true and who brought it; `--json` gives the same as data.
It reads, and writes nothing.

**One table, several matters.** A box made from several folders (the
kernel's `init --from NAME=FOLDER`, one a matter) is one table over all of
them: one record, one sitting, one seal at its end. Each folder's name is a
matter. `m` at the table's prompt says which matter the next words are
about; a guest says it with `--at MATTER`. What stands is read back a matter
at a time, and `stands --at MATTER` gives one alone. The heads-up looks
across every matter, and says which one the older word was about: that is
what one table is for, since what is settled about one thing in a life bears
on another. A word may also be about no matter: the table itself. A box over
one folder has no matters, and nothing here changes for it.

**The words are a table's own.** Every line a person reads is in a list
(`table.py`'s WORDS); `--words FILE` replaces any of them, `name: text` a
line, so a game says "Your call, GM" and a kitchen table says something
else. A name the list doesn't have is refused, so a slip isn't silent.

Exit codes, the kernel's: 0 the sitting ended, or `stands` and `moves`
printed; 42 something waits on the host (a call, a pause, a sitting left
open, what `bring` handed in), or `stands` found nothing; 2 refused.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STDLIB = HERE.parent
ROOT = STDLIB.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(STDLIB / "contradictions"))
import kernel  # noqa: E402

try:  # the heads-up's rule; without it, nothing is raised
    import contradictions  # noqa: E402
except ImportError:
    contradictions = None

KERNEL = ROOT / "kernel.py"
SEAL_END = STDLIB.joinpath("session-seal", "session_seal.py")
STACK = STDLIB.joinpath("stack", "stack.py")
FORGE = STDLIB.parent.joinpath("deps", "forge", "suggest.py")
#: a fork's two ways out, as the forge names them; and where it keeps a stack
FORGE_OUTS, FORGE_STACK = ("none", "not-now"), "forge/stack.md"
FORGE_CLOSE = "close"  # the fork for a sentence no card is named for
FORK_NAME = re.compile(r"fork “([^”]*)”")
#: a table's own stacks of wants, kept beside its box: before a sitting, and after
PREP, END = "prep.md", "end.md"
NAME = "table"
HOST, GUEST = "host", "guest"
SAID, REPLACES, BOTH = "table-said", "table-replaces", "table-both"
ASIDE, PAUSE, NOTE = "table-x", "table-pause", "table-note"
SLIP = "nothing: that yes was a slip"
LONGEST = 500  # a word kept at the table is one passage: the kernel's chunk
SET_ASIDE = "aside"  # what a prompt returns when the host pressed x there
AT_ONCE = 2  # how many calls the host is put before "more?" is asked
MOST_READ, RECENT = (
    5,
    3,
)  # past MOST_READ things settled, the opening reads the RECENT newest
PAGE_MOST, PAGE_LINE = 100_000, 100  # bytes of a page that are read; of a line, shown
#: a folder's own stack, and the source one is made from; where a bite is run
OWN_STACK, OWN_SRC, BITES = "stack.md", "stack.src", "bites.md"
SHOWN = 5  # how many lines a step found are read back at the table
MOST_WAITING = 5  # what guests may leave waiting on the host: six is too many

#: every line a person reads; --words FILE replaces any of them
WORDS = {
    "title": "The table",
    "previously": "Previously, this table made true:",
    "nothing_yet": "Nothing has been made true at this table yet.",
    "notes": "Just for you, from last time:",
    "waits": '{who} left {n} {things} here for you to look at. Type "look" to see {first}.',
    "none_wait": "Nothing has been left for you to look at.",
    "more_stand": 'and {n} more, settled earlier. Type "list" to read them all.',
    "nth": "{i} of {n}.",
    "rest": 'The rest will keep. Type "look" whenever you want the next two.',
    "all_answered": "That was the last of them.",
    "tables": "Hello. You have {n} {tables}.",
    "settled": "You've settled {n} {things} here.",
    "unsettled": "Nothing settled yet.",
    "left": "{who} left {n} {things} for you to look at.",
    "which_table": "Which one would you like? Type its number, or ask them all something. Enter on its own leaves. ",
    "ask_all": "Asking {n} {tables}, one at a time. A choice you make is asked once and used at each.",
    "back": "You're back at your tables.",
    "prep_there": 'This table has a prep sheet. Type "prep" to run it and see what it finds.',
    "prep_ran": "Your prep sheet, run just now:",
    "more_found": "and {n} more, in its page.",
    "next_beside": "Your other stacks put these beside those steps:",
    "all_found": "Everything that found, from every table:",
    "more_at": "and {n} more at {table}, in its page.",
    "no_box": "{n} more {folders} {have} a stack but no box yet: {names}.",
    "want_ask": "What do you want to find out before you sit down? Say it your way: ",
    "no_forge": "The forge add-on isn't here, so a sheet can't be drafted. One can be written by hand: a page named prep.md, beside the box.",
    "want_none": "I couldn't match that to anything this Willow can do. Try other words, or write the want by hand.",
    "fork": "“{word}” could be answered more than one way:",
    "fork_which": "Which would you like? A number, two as 1,2, n for neither, or s to leave it for later. ",
    "fork_said": "“{word}”: {pick}, as you said.",
    "fork_close": "Nothing here is named for that. These are the closest:",
    "fork_said_close": "{pick}, as you said.",
    "fork_why_close": "Why {pick}? A few words, or just press Enter: ",
    "fork_why": "Why {pick} for “{word}”? A few words, or just press Enter: ",
    "want_sheet": "Then these would go on your prep sheet:",
    "want_own": "Then these would be added to your own stack here, {page}:",
    "want_stack": "Added to your own stack, {page}: {n} new {steps}{had}.",
    "want_had": ", and {had} it already had",
    "want_made": "Your stack here is made from {src}, so I left it alone and used {page}.",
    "bite_ran": "Here is what that found:",
    "page_read": "I read {page}. These are the lines in it that ask for something:",
    "page_none": "I read {page}, and nothing in it matches anything this Willow can do.",
    "page_cant": "{page} isn't a page of text I can read.",
    "page_long": "It is a long page: I read its first {n} lines.",
    "no_page": "There is no page named {name} in your files here.",
    "want_keep": "Put them on it? (y/n) ",
    "want_dropped": "Nothing was kept, and nothing was written.",
    "want_later": "Nothing to put on a sheet this time. What you left is on your record as left.",
    "want_done": 'They are on your prep sheet now ({n} steps): a page of proposals you can cut from, in {page}. Typing "prep" runs it again any time.',
    "end_ran": "Your end-of-sitting sheet, run just now:",
    "no_sheet": "This table has no prep sheet. One is a page of wants named prep.md, beside its box.",
    "pages": "Each one's page is in {folder}",
    "more": "{n} more. Press Enter for the next two, or type n to stop here. ",
    "already": "This table already holds that true.",
    "hint": (
        "What is the first bite?\n"
        "(Ask your files anything, your way. Enter on its own finishes. Type ? to see what else you can do.)"
    ),
    "hint_again": "What is the next bite? (Enter on its own finishes. ? shows what else you can do.)",
    "say_ask": "What do you want kept as settled? ",
    "help": (
        "You can type:\n"
        "  look    see two of the things left for you\n"
        "  list    read everything settled here\n"
        "  who     keep something someone else said\n"
        "  undo    take back the last thing you said yes to\n"
        "  pause   stop for now; nobody needs to say why\n"
        "  want    say what you want to find out, and have a prep sheet drafted\n"
        "  prep    run this table's prep sheet, and read what it found\n"
        "  Enter   on its own, to finish\n"
        "  say     keep something as settled: say, then the words\n"
        "  read    ask from a page instead: read, then the page's name\n"
        "Anything else you type is a bite: a question for your files, asked your way."
    ),
    "is_right": "Is that right? Type y to keep it, n to drop it, or s to skip it for now. ",
    "call": "Your call.",
    "says": "{who} says:",
    "is_true": "Is that true? (y/n) ",
    "true_now": "It's true now.",
    "not_so": "It didn't happen.",
    "not_kept": "Not kept.",
    "before": "Before you decide:",
    "held": "on {day}{about} this table made this true:",
    "about": " (about {matter})",
    "no_matter": "the table itself",
    "one_matter": "This table is over one folder: it has no matters to choose from.",
    "matter_key": 'This table has several matters ({matters}). Type "about" to say which one you mean.',
    "which": "Which? ",
    "mine": "Mine stands now",
    "old": "Keep the old one",
    "both": "Both are true",
    "reword": "Let me reword it",
    "reworded": "Say it again, your way: ",
    "replaced": "It's true now, and the old one is replaced.",
    "old_stands": "The old one stands.",
    "beside": "It's true now, beside the old one.",
    "aside": "Skipped for now. Nothing is decided, and nobody needs to say why. It will keep.",
    "paused": "Paused. Nobody needs to say why. Come back whenever you're ready.",
    "waiting": "Left as it is. You can come back to it whenever you like.",
    "who": "Who brings it in? (or press Enter) ",
    "what": "What do they bring in? (or press Enter) ",
    "take_back": 'Take back "{fact}"? It stays on the record as a slip, and no longer stands. (y/n) ',
    "taken_back": "Taken back. It no longer stands.",
    "nothing_to_take": "Nothing has been made true this time to take back.",
    "end": "The end of this sitting",
    "made_true": "This time, the table made true:",
    "nothing_new": "This time, nothing new was made true.",
    "remember": "Anything to remember for next time? (or press Enter) ",
    "done": "That's it for now? (y/n) ",
    "stays_open": "Left open. You can come back to it whenever you like.",
    "saved": "Saved and checked: nothing can be changed after the fact.",
    "yn": "Type y for yes, or n for no.",
    "too_long": "That is longer than one passage ({most} characters). Say it shorter, or in two.",
}

#: each seat, and the moves it may make
MOVES = {
    HOST: [
        ("say", "say what happened: kept on your own typed yes"),
        ("call", "c: go through what was brought in, two at a time: yes, or no"),
        (
            "heads-up",
            "when a word meets one the table holds: mine, the old one, both, or reword",
        ),
        ("take back", "u: the last yes of this sitting, replaced by nothing"),
        ("set aside", "x at a call: nothing decided, it waits, no reason asked"),
        ("pause", "p: the whole sitting stops, no reason asked"),
        ("matter", "m: which of the table's matters the next words are about"),
        ("end", "Enter: a line for next time, and one seal over the sitting"),
    ],
    GUEST: [("bring", "hand something in, under a name: it waits on the host's call")],
}


class Refused(Exception):
    """Something the table can't go on from: said, and exit 2."""


class Pause(Exception):
    """The host stopped the whole sitting (p): nothing asked."""


# ── the record, read ─────────────────────────────────────────────────────────
def rows_of(box: Path) -> list[dict]:
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        raise Refused("the record doesn't check out: " + "; ".join(breaks))
    return rows


def ruling(box: Path, rows: list[dict], subject: str) -> tuple[str, dict | None]:
    """('sealed' | 'declined', the host's row) while its proof holds;
    ('broken', None) for a seal whose file is not what was sealed; or
    ('open', None) while the host has said nothing."""
    yes = kernel.sealed(box, rows).get(subject)
    no = kernel.declined(box, rows).get(subject)
    if yes and (not no or yes["n"] < no["n"]):
        why = kernel.standing(box, rows, subject, yes)[2]
        return ("broken", None) if why else ("sealed", yes)
    if no:
        return "declined", no
    return "open", None


def said(rows: list[dict]) -> list[dict]:
    """Everything handed in at the table, once each, in row order."""
    seen: dict[str, dict] = {}
    for r in rows:
        if r["kind"] == SAID:
            seen.setdefault(r["subject"], r)
    return list(seen.values())


def replaced(box: Path, rows: list[dict]) -> dict[str, dict]:
    """{the old subject: the replacing row} for each replacement the host sealed."""
    return {
        r["old"]: r
        for r in rows
        if r["kind"] == REPLACES and ruling(box, rows, r["subject"])[0] == "sealed"
    }


def standing(box: Path, rows: list[dict]) -> list[dict]:
    """What the table holds true now: each word the host sealed, unless a
    sealed replacement stands over it. Oldest first."""
    gone = set(replaced(box, rows))
    out = []
    for r in said(rows):
        what, got = ruling(box, rows, r["subject"])
        if what == "sealed" and r["subject"] not in gone:
            out.append({"subject": r["subject"], "fact": r["fact"], "by": r["by"],
                        "matter": r.get("matter", ""), "n": got["n"], "day": got["ts"][:10]})  # fmt: skip
    return sorted(out, key=lambda t: t["n"])


def matters(box: Path) -> list[str]:
    """The matters a table holds: the names of the places its box draws on,
    when it draws on more than one folder; none for a box over one pile."""
    cfg = kernel.config(box)
    return sorted(cfg["sources"]) if cfg.get("sources") else []


def by_matter(items: list[dict]) -> list[tuple[str, list[dict]]]:
    """ITEMS a matter at a time: those of no matter first, then A to Z."""
    names = sorted({t["matter"] for t in items})
    return [(m, [t for t in items if t["matter"] == m]) for m in names]


def waiting(box: Path, rows: list[dict]) -> list[dict]:
    """What was brought in and still waits on the host's call, oldest first."""
    return [r for r in said(rows) if ruling(box, rows, r["subject"])[0] == "open"]


def last_end(rows: list[dict], back: int = 1) -> int:
    """The last row of the sitting that ended BACK sittings ago, or -1."""
    ends = [r["to"] for r in rows if r["kind"] == "session"]
    return ends[-back] if len(ends) >= back else -1


def tonight(box: Path, rows: list[dict]) -> list[dict]:
    """What was made true since the last sitting ended, still standing."""
    after = last_end(rows)
    return [t for t in standing(box, rows) if t["n"] > after]


def stems(text: str) -> set:
    return {kernel.stem(w) for w in contradictions.subject(text)}


def meets(box: Path, rows: list[dict], fact: str, subject: str = "") -> list[dict]:
    """What the table holds true that FACT is about the same thing as: not
    itself, not the same words, and not a pair the host called both true."""
    if contradictions is None:
        return []
    ok = {frozenset(r["facts"]) for r in rows if r["kind"] == BOTH}
    mine = {"stems": stems(fact)}
    return [
        t
        for t in standing(box, rows)
        if t["subject"] != subject
        and t["fact"] != fact
        and frozenset((t["fact"], fact)) not in ok
        and contradictions.same(mine, {"stems": stems(t["fact"])})
    ]


# ── the record, written: through the kernel, on the host's choice ────────────
def kernel_says(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(KERNEL), *map(str, argv)],
                          capture_output=True, text=True, check=False)  # fmt: skip


def hand_in(box: Path, ts: str, question: str, prop: dict) -> str:
    """The suggestion's subject, once the kernel's own bite and propose have
    taken it."""
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "proposal.jsonl"
        f.write_text(json.dumps(prop) + "\n", encoding="utf-8")
        for argv in (["bite", question], ["propose", "--file", str(f)]):
            done = kernel_says(argv[0], "--box", box, "--now", ts, *argv[1:])
            if done.returncode == kernel.REFUSED:
                raise Refused(f"the kernel's {argv[0]}: {done.stderr.strip()}")
    subject = kernel.subject_of(prop)
    if f"pass  {subject}" not in done.stdout:
        raise Refused("the kernel's door refused it: " + done.stdout.strip())
    return subject


def answer(box: Path, ts: str, subject: str, yes: bool) -> None:
    """The host's typed yes or no, made the record's by the kernel. One
    already answered is left as it was answered: a word said twice in a day
    is the one suggestion, and the kernel keeps its first answer."""
    if ruling(box, rows_of(box), subject)[0] != "open":
        return
    done = kernel_says("seal" if yes else "decline", "--box", box, "--now", ts, subject)
    if done.returncode != kernel.ALIVE:
        raise Refused((done.stderr or done.stdout).strip())


def bring(box: Path, ts: str, by: str, fact: str, matter: str = "") -> str:
    """Words handed in at the table under a name: a suggestion that waits.
    The same words by the same name on the same day are one suggestion while
    it waits. Once the host has answered it, the kernel keeps that answer for
    good, so the same words said again that day are a suggestion of their
    own (`-2`, `-3`), for the host to answer anew. With MATTER, the words are
    about that one of the table's matters, and the same words about another
    are another suggestion."""
    claim = "The host's own word at the table" if by == HOST else f"Brought in at the table by {by}"  # fmt: skip
    claim += f", about {matter}." if matter else "."
    digest = kernel.h256(by + "\n" + fact)[:16]
    folder = f"table/said/{matter}" if matter else "table/said"
    rows = rows_of(box)
    seen = {r["subject"] for r in said(rows)}
    go = 1
    while True:
        again = "" if go == 1 else f"-{go}"
        prop = {"path": f"{folder}/{ts[:10]}-{digest}{again}.md", "data": fact + "\n",
                "cites": [], "claim": claim}  # fmt: skip
        subject = kernel.subject_of(prop)
        if subject not in seen:
            break
        if ruling(box, rows, subject)[0] == "open":
            return subject  # handed in and waiting: the one suggestion, once
        go += 1
    hand_in(box, ts, f"table: {fact}", prop)
    about = {"matter": matter} if matter else {}
    kernel.append(box, ts, SAID, who=NAME, by=by, fact=fact, subject=subject, **about)
    return subject


def replace(box: Path, ts: str, old: dict, new_subject: str, new_fact: str) -> None:
    """The host's "mine stands now": a replacement handed in and sealed, so
    nothing stops being true without the host's seal."""
    claim = f"From now on this stands in place of what the table made true on {old['day']}: {old['fact']}"  # fmt: skip
    tail = old["subject"].split(":")[-1][:16]
    prop = {"path": f"table/replaces/{ts[:10]}-{tail}.md", "data": new_fact + "\n",
            "cites": [], "claim": claim}  # fmt: skip
    subject = hand_in(box, ts, f"table replaces {old['subject']}", prop)
    kernel.append(box, ts, REPLACES, who=NAME, old=old["subject"], new=new_subject,
                  fact=new_fact, subject=subject)  # fmt: skip
    answer(box, ts, subject, True)


def keep_both(box: Path, ts: str, old: dict, new_subject: str, new_fact: str) -> None:
    """The host's "both are true": the pair isn't raised again. It changes
    no truth, so it is a row and no seal."""
    kernel.append(box, ts, BOTH, who=NAME, pair=sorted((old["subject"], new_subject)),
                  facts=sorted((old["fact"], new_fact)))  # fmt: skip


def standing_by(box: Path, ts: str, choice: str, met: list[dict], subject: str, fact: str) -> None:  # fmt: skip
    """What the host's choice at a heads-up keeps, once the new word is sealed."""
    for old in met:
        if choice == "mine":
            replace(box, ts, old, subject, fact)
        elif choice == "both":
            keep_both(box, ts, old, subject, fact)


# ── the forge, asked as a guest: what could answer a want ────────────────────
def forge(*argv) -> tuple[dict | None, str]:
    """(the forge add-on's report as data, what it said beside it), or (None,
    why) when it printed no report: a refusal, in its own words."""
    done = subprocess.run([sys.executable, str(FORGE), *map(str, argv), "--json"],
                          capture_output=True, text=True, check=False)  # fmt: skip
    try:
        return json.loads(done.stdout), done.stderr.strip()
    except ValueError:
        return None, (done.stderr or done.stdout).strip()


def named(row: dict) -> tuple[str, str]:
    """(a card's name, its line) from a row of the forge's report."""
    name, _, line = row["what"].partition(": ")
    return name, line.split(" (writes")[0]


# ── a table's sheets: stacks of wants, run before and after a sitting ────────
def sheet(box: Path, which: str) -> Path | None:
    """The table's prep or end sheet, when it has one and the stack add-on
    is here to run it."""
    page = box.parent.joinpath(which)
    return page if page.is_file() and STACK.is_file() else None


def added(old: str, new: str) -> tuple[str, int]:
    """What of NEW (a stack's pools, each want a few lines and its step) is
    not already in OLD, a stack file: (the pools to add, how many steps OLD
    had already). A step is the same step when its line is the same; a pool
    left with nothing in it is not added."""
    have = {ln.strip() for ln in old.splitlines() if ln.strip().startswith("- ")}
    blocks, block, had = [], [], 0
    for ln in new.splitlines() + [""]:
        if ln.strip():
            block.append(ln)
            continue
        step = next((b.strip() for b in block if b.startswith("- ")), None)
        if step is not None and step in have:
            had += 1
        elif block:
            blocks.append(block)
        block = []
    keep = [
        b
        for i, b in enumerate(blocks)
        if not b[0].startswith("## ")
        or (i + 1 < len(blocks) and not blocks[i + 1][0].startswith("## "))
    ]
    return "\n\n".join("\n".join(b) for b in keep) + ("\n" if keep else ""), had


def stack_add_on():
    """The stack add-on's own module, from beside this one: its reading of a
    stack file and of a run's log, so the two can't come to disagree."""
    spec = importlib.util.spec_from_file_location("willow_table_stack", STACK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_sheet(box: Path, which: str, page: Path | None = None) -> tuple[Path, list[tuple[str, str, list]]] | None:  # fmt: skip
    """Run the table's prep or end sheet through the stack add-on, each run
    kept in a folder of its own beside the box (prep/001, prep/002, and so
    on), as Die-Namic's open_table.py keeps them. (the run's folder, [(the
    want, or the step's name when none is written above it; what the step
    said; what it found, each line with where it is from)]), or None when
    the table has no such sheet. It runs add-ons, each held to its own
    card; this seals nothing."""
    page = page or sheet(box, which)  # a page handed in is run as it is
    if page is None or not STACK.is_file():
        return None
    home = box.parent.joinpath(Path(which).stem)
    home.mkdir(exist_ok=True)
    last = max((int(d.name) for d in home.iterdir() if d.name.isdigit()), default=0)
    to = home.joinpath(str(last + 1).zfill(3))
    text = page.read_text(encoding="utf-8")
    # the stack add-on fills {box} and nothing else, so {tmp} (the forge's
    # backup step writes there) is filled here: a folder of the run's own
    # that the run makes as it goes, never one named with braces
    with tempfile.TemporaryDirectory() as hold:
        kept = Path(hold).joinpath(page.name)
        kept.write_text(
            text.replace("{tmp}", str(to.joinpath("tmp"))), encoding="utf-8"
        )
        subprocess.run([sys.executable, str(STACK), "--box", str(box), "--stack", str(kept), "--to", str(to)],
                       capture_output=True, text=True, check=False)  # fmt: skip
    st = stack_add_on()
    pools, _ = st.parse_stack(text)
    above = st.notes(text)[1] if hasattr(st, "notes") else {}
    logs = sorted(to.glob("0*-stack.txt")) if to.is_dir() else []
    done = (
        st.ended(logs[0].read_text(encoding="utf-8", errors="replace")) if logs else {}
    )
    width = len(logs[0].name.split("-")[0]) if logs else 2
    out = []
    for n, (name, _) in enumerate((s for _, steps in pools for s in steps), 1):
        stem = str(n).zfill(width) + "-" + name
        line, found = "did not run", []
        if n in done:
            try:
                doc = json.loads(
                    to.joinpath("reports", stem + ".json").read_text(encoding="utf-8")
                )
                line = doc["state"] + ", " + doc["said"]
                found = [
                    (r["where"], r["what"]) for g in doc["groups"] for r in g["rows"]
                ]
            except (OSError, ValueError, KeyError):
                words = to.joinpath("words", stem + ".txt")
                words = words if words.is_file() else to.joinpath(stem + ".txt")
                try:
                    first = [
                        ln.strip()
                        for ln in words.read_text(
                            encoding="utf-8", errors="replace"
                        ).splitlines()
                        if ln.strip()
                    ]
                except OSError:
                    first = []
                line = first[0] if first else "said nothing"
                found = [("", ln) for ln in first[1:]]
        out.append((above.get(n, [name])[0], name + ": " + line, found))
    return to, out


# ── the host's seat: a terminal ──────────────────────────────────────────────
class Seat:
    """The host at a terminal: the table's words, the box, and the time."""

    def __init__(self, box: Path, now: str, words: dict):
        self.box, self.now, self.w = box, now, words
        self.matters = matters(box)  # the table's matters, if it has any
        self.at = ""  # the matter the next words are about; "" for none
        #: what the host answered at a fork this bite: {word: (names, why)}.
        #: The front door shares one between its tables, so a bite asked
        #: of them all puts each fork to the host once.
        self.said: dict[str, tuple[list[str], str]] = {}
        #: what the last bite's steps found: [(the want, [(where, what)])].
        #: The front door gathers these across its tables.
        self.found: list[tuple[str, list]] = []

    def about(self, matter: str) -> str:
        """ ", about MATTER" for a line that says which matter, or ""."""
        return self.w["about"].format(matter=matter) if matter else ""

    def listed(self, items: list[dict]) -> str:
        """ITEMS as a list to read: plain at a table of one matter, and
        under each matter's name at a table of several."""
        if not any(t["matter"] for t in items):
            return "\n".join(f"  - {t['fact']}" for t in items)
        out = []
        for matter, its in by_matter(items):
            out.append(f"  {matter or self.w['no_matter']}")
            out += [f"    - {t['fact']}" for t in its]
        return "\n".join(out)

    def which_matter(self) -> bool | None:
        """m: the host says which matter the next words are about. None if
        they've gone."""
        if not self.matters:
            print("   " + self.w["one_matter"])
            return False
        for i, m in enumerate(self.matters, 1):
            print(f"   {i}. {m}")
        print(f"   0. {self.w['no_matter']}")
        while True:
            got = self.ask("   " + self.w["which"])
            if got is None:
                return None
            if got.isdigit() and int(got) <= len(self.matters):
                self.at = self.matters[int(got) - 1] if int(got) else ""
                return True
            if got in self.matters:
                self.at = got
                return True
            print(f"   0 to {len(self.matters)}.")

    def ask(self, prompt: str) -> str | None:
        """What the host typed, or None when there is no one to type."""
        try:
            return input(prompt).strip()
        except EOFError:
            print()
            return None

    def keys(self, got: str, at_call: bool) -> bool:
        """p (or pause) pauses the sitting, and raises; s, x or skip at a
        call sets it aside."""
        key = got.lower()
        if key in ("p", "pause"):
            kernel.append(self.box, self.now, PAUSE, who=NAME)
            raise Pause
        if key in ("s", "x", "skip") and at_call:
            kernel.append(self.box, self.now, ASIDE, who=NAME, part="call")
            return True
        return False

    def yes(self, prompt: str, at_call: bool = False) -> bool | str | None:
        """The host's yes or no, asked until it is one; None if they've gone."""
        while True:
            got = self.ask(prompt)
            if got is None:
                return None
            if self.keys(got, at_call):
                return SET_ASIDE
            if got.lower() in ("y", "yes"):
                return True
            if got.lower() in ("n", "no"):
                return False
            print("   " + self.w["yn"])

    def heads_up(self, met: list[dict], reword: bool, at_call: bool) -> str | None:
        """Before the host decides: what the table already holds true about
        the same thing, and their choice; None if they've gone."""
        print("   " + self.w["before"])
        for t in met:
            held = self.w["held"].format(day=t["day"], about=self.about(t["matter"]))
            print(f"   {held}\n   {t['fact']}")
        keys = ["mine", "old", "both"] + (["reword"] if reword else [])
        for i, k in enumerate(keys, 1):
            print(f"   {i}. {self.w[k]}")
        while True:
            got = self.ask("   " + self.w["which"])
            if got is None:
                return None
            if self.keys(got, at_call):
                return SET_ASIDE
            if got.isdigit() and 1 <= int(got) <= len(keys):
                return keys[int(got) - 1]
            print(f"   1 to {len(keys)}.")

    def decide(self, fact: str, subject: str, reword: bool, at_call: bool) -> tuple[str | None, list]:  # fmt: skip
        """The host's choice over FACT: "yes", "no", "mine", "old", "both",
        "reword", SET_ASIDE, or None if they've gone; and what it met."""
        met = meets(self.box, rows_of(self.box), fact, subject)
        if met:
            return self.heads_up(met, reword, at_call), met
        got = self.yes("   " + self.w["is_right" if at_call else "is_true"], at_call)
        return (
            {True: "yes", False: "no"}.get(got, got) if got is not None else None
        ), []

    def said_of(self, choice: str) -> str:
        return {"mine": self.w["replaced"], "both": self.w["beside"], "yes": self.w["true_now"],
                "old": self.w["old_stands"], "no": self.w["not_so"]}[choice]  # fmt: skip

    def call(self, by: str, fact: str, subject: str, matter: str = "", nth: str = "") -> str | None:  # fmt: skip
        """What someone brought in, put to the host; their answer made the
        record's by the kernel. SET_ASIDE leaves it waiting; None, gone."""
        who = by + self.about(matter)
        head = " ".join(
            x for x in (nth, self.w["call"], self.w["says"].format(who=who)) if x
        )
        print(f"\n{head}\n\n   {fact}\n")
        choice, met = self.decide(fact, subject, reword=False, at_call=True)
        if choice is None:
            return None
        if choice == SET_ASIDE:
            print("   " + self.w["aside"])
            return SET_ASIDE
        kept = choice not in ("no", "old")
        answer(self.box, self.now, subject, kept)
        if kept:
            standing_by(self.box, self.now, choice, met, subject, fact)
        print("   " + self.said_of(choice))
        return choice

    def own(self, line: str) -> bool | None:
        """The host's own word: kept on their yes, with the heads-up first.
        True if kept, False if not, None if they've gone."""
        while True:
            if len(line) > LONGEST:
                print("   " + self.w["too_long"].format(most=LONGEST))
                return False
            now = standing(self.box, rows_of(self.box))
            if any((t["fact"], t["matter"]) == (line, self.at) for t in now):
                print("   " + self.w["already"])  # the same words stand once
                return False
            choice, met = self.decide(line, "", reword=True, at_call=False)
            if choice is None:
                return None
            if choice == "reword":
                line = self.ask("   " + self.w["reworded"]) or ""
                if not line:
                    print("   " + self.w["not_kept"])
                    return False
                continue
            if choice in ("no", "old"):
                print("   " + self.w["not_kept" if choice == "no" else "old_stands"])
                return False
            subject = bring(self.box, self.now, HOST, line, self.at)
            answer(self.box, self.now, subject, True)
            standing_by(self.box, self.now, choice, met, subject, line)
            print("   " + self.said_of(choice))
            return True

    def brought(self) -> bool | None:
        """Someone at the table brings something in. The host is asked
        first, and only then is it handed in and answered, so leaving midway
        leaves nothing half done. None if the host has gone."""
        who = self.ask("   " + self.w["who"])
        if not who:
            return None if who is None else False
        if who.lower() == HOST:
            who = "a guest"
        fact = self.ask("   " + self.w["what"])
        if not fact:
            return None if fact is None else False
        if len(fact) > LONGEST:
            print("   " + self.w["too_long"].format(most=LONGEST))
            return False
        shown = who + self.about(self.at)
        print(f"\n{self.w['call']} {self.w['says'].format(who=shown)}\n\n   {fact}\n")
        choice, met = self.decide(fact, "", reword=False, at_call=True)
        if choice is None:
            return None
        if choice == SET_ASIDE:
            print("   " + self.w["aside"])
            return False
        kept = choice not in ("no", "old")
        subject = bring(self.box, self.now, who, fact, self.at)
        answer(self.box, self.now, subject, kept)
        if kept:
            standing_by(self.box, self.now, choice, met, subject, fact)
        print("   " + self.said_of(choice))
        return kept

    def undo(self) -> bool | None:
        """A yes pressed by mistake: the last thing made true this sitting,
        taken back on the host's word."""
        made = tonight(self.box, rows_of(self.box))
        if not made:
            print("   " + self.w["nothing_to_take"])
            return False
        last = made[-1]
        sure = self.yes("   " + self.w["take_back"].format(fact=last["fact"]))
        if sure is not True:
            return None if sure is None else False
        replace(self.box, self.now, last, "", SLIP)
        print("   " + self.w["taken_back"])
        return True

    def stands(self) -> None:
        now = standing(self.box, rows_of(self.box))
        if not now:
            print("   " + self.w["nothing_yet"])
        for matter, its in by_matter(now):
            if any(t["matter"] for t in now):
                print(f"   {matter or self.w['no_matter']}")
            for t in its:
                print(f"   {t['day']}  {t['fact']}" + ("" if t["by"] == HOST else f"  ({t['by']})"))  # fmt: skip

    def previously(self) -> None:
        """What the table holds true, and the host's own notes from last time."""
        rows = rows_of(self.box)
        now = standing(self.box, rows)
        if now:
            print(self.w["previously"])
            long = len(now) > MOST_READ and not any(t["matter"] for t in now)
            print(self.listed(now[-RECENT:] if long else now))
            if long:  # the newest few; the rest is a word away, not a wall to scroll
                print("  " + self.w["more_stand"].format(n=len(now) - RECENT))
        else:
            print(self.w["nothing_yet"])
        notes = [
            r["text"] for r in rows if r["kind"] == NOTE and r["n"] > last_end(rows, 2)
        ]
        if notes:
            print("\n" + self.w["notes"])
            print("\n".join(f"  {t}" for t in notes))
        print()

    def end(self) -> int:
        """The end of the sitting: what was made true, a line to remember,
        and the host's yes, sealed as one."""
        true = tonight(self.box, rows_of(self.box))
        print("\n" + self.w["end"])
        if true:
            print(self.w["made_true"])
            print(self.listed(true))
        else:
            print(self.w["nothing_new"])
        note = self.ask(self.w["remember"])
        if note is None:
            return kernel.ESCALATE
        if note:
            kernel.append(self.box, self.now, NOTE, who=NAME, text=note[:LONGEST])
        done = self.yes(self.w["done"])
        if done is not True:
            print(self.w["stays_open"])
            return kernel.ESCALATE
        if not SEAL_END.is_file():
            print("The session-seal add-on isn't here, so the sitting can't be sealed as one.")  # fmt: skip
            return kernel.ESCALATE
        # the table's own end sheet first, when it has one: tonight's pages
        # read, a copy kept, where the record ends. It may bundle the sitting
        # itself (a session-seal step); when it doesn't, that is done here.
        bundled = sum(1 for r in rows_of(self.box) if r["kind"] == "session")
        if sheet(self.box, END):
            self.ran(END, "end_ran")
        if sum(1 for r in rows_of(self.box) if r["kind"] == "session") == bundled:
            subprocess.run([sys.executable, str(SEAL_END), "--box", str(self.box), "--now", self.now],
                           capture_output=True, text=True, check=False)  # fmt: skip
        rows = rows_of(self.box)
        ends = [r for r in rows if r["kind"] == "session"]
        if ends and ruling(self.box, rows, ends[-1]["subject"])[0] != "sealed":
            answer(self.box, self.now, ends[-1]["subject"], True)
        held = kernel_says("verify", "--box", self.box)
        if held.returncode != kernel.ALIVE:
            raise Refused((held.stderr or held.stdout).strip())
        print(self.w["saved"])
        return kernel.ALIVE

    def calls(self) -> bool | None:
        """c: what was brought in and waits, put to the host, oldest first,
        AT_ONCE at a time; then "more?", and their no leaves the rest
        waiting. Nothing is asked until the host asks for it. None if
        they've gone."""
        left = waiting(self.box, rows_of(self.box))
        if not left:
            print("   " + self.w["none_wait"])
            return False
        for i, r in enumerate(left):
            if i and i % AT_ONCE == 0:
                got = self.ask("\n   " + self.w["more"].format(n=len(left) - i))
                if got is None:
                    return None
                self.keys(got, False)  # p pauses here too
                if got.lower() not in ("", "y", "yes"):
                    print("   " + self.w["rest"])
                    return False
            nth = self.w["nth"].format(i=i + 1, n=len(left))
            if (
                self.call(r["by"], r["fact"], r["subject"], r.get("matter", ""), nth)
                is None
            ):
                return None
        if not waiting(self.box, rows_of(self.box)):  # none set aside along the way
            print("\n   " + self.w["all_answered"])
        return True

    def want(self, words: str | None = None) -> bool | None:
        """The host says what they want to find out, and the forge add-on
        drafts the steps for it. A word that could mean more than one card is
        put to the host as one plain question; what would go on the sheet is
        shown; and only on their yes is anything handed in. Their typed picks
        and that yes are what seal the forge's suggestions, by the kernel, as
        any call's answer is. Leaving before the yes leaves nothing behind.
        Then the wants go on the table's prep sheet, a page they can cut from.
        None if the host has gone."""
        self.found = []
        if not FORGE.is_file():
            print("   " + self.w["no_forge"])
            return False
        words = words or self.ask("   " + self.w["want_ask"])
        if not words:
            return None if words is None else False
        doc, err = forge("suggest", "--box", self.box, words)
        if doc is None or doc.get("state") == "unreachable":
            print("   " + ((doc or {}).get("said") or err or self.w["no_forge"]))
            return False
        forks, steps, rides = {}, [], []
        for g in doc["groups"]:
            name = g["name"] or ""
            rows = [named(r) for r in g["rows"] if r["where"] not in FORGE_OUTS]
            if fork := FORK_NAME.match(
                name
            ):  # the word, whatever the group says after it
                forks[fork.group(1)] = rows
            elif name == "steps":
                steps = rows
            elif name.startswith("defaults"):
                rides = rows
        if not forks and not steps:
            print("   " + self.w["want_none"])
            return False
        choose: dict[str, list[str]] = {}

        def mine(word: str) -> str:  # the close fork is this sentence's own
            return word if word != FORGE_CLOSE else f"{word}: {words}"

        for word, options in forks.items():
            before = self.said.get(mine(word))
            if before and all(n in dict(options) or n in FORGE_OUTS for n in before[0]):
                choose[word] = before[0]
                pick = " and ".join(before[0])
                print(
                    "   "
                    + (
                        self.w["fork_said_close"].format(pick=pick)
                        if word == FORGE_CLOSE
                        else self.w["fork_said"].format(word=word, pick=pick)
                    )
                )
                continue
            print(
                "\n   "
                + (
                    self.w["fork_close"]
                    if word == FORGE_CLOSE
                    else self.w["fork"].format(word=word)
                )
            )
            for i, (name, line) in enumerate(options, 1):
                print(f"   {i}. {name}: {line}")
            while word not in choose:
                got = self.ask("   " + self.w["fork_which"])
                if got is None:
                    return None
                self.keys(got, False)  # p pauses here too
                low = got.lower().replace(" ", "")
                picks = [x for x in low.split(",") if x]
                if low in ("n", "none", "neither"):
                    choose[word] = [FORGE_OUTS[0]]
                elif low in ("s", "skip", "later"):
                    choose[word] = [FORGE_OUTS[1]]
                elif picks and all(
                    x.isdigit() and 1 <= int(x) <= len(options) for x in picks
                ):
                    choose[word] = [
                        options[int(x) - 1][0] for x in dict.fromkeys(picks)
                    ]
                else:
                    print(f"   1 to {len(options)}, n or s.")
        taken = [n for names in choose.values() for n in names if n not in FORGE_OUTS]
        why: dict[str, str] = {}
        for word, names in choose.items():
            if names[0] in FORGE_OUTS:
                continue
            was = self.said.get(mine(word))
            if was and was[0] == names:
                if was[1]:
                    why[word] = was[1]
                continue
            said = self.ask(
                "   "
                + (
                    self.w["fork_why_close"].format(pick=" and ".join(names))
                    if word == FORGE_CLOSE
                    else self.w["fork_why"].format(pick=" and ".join(names), word=word)
                )
            )
            if said is None:
                return None
            if said:
                why[word] = said
        self.said.update(
            {mine(w): (names, why.get(w, "")) for w, names in choose.items()}
        )
        going = [n for n, _ in steps] + taken
        if going:
            lines = dict(rides)
            for options in forks.values():
                lines.update(dict(options))
            lines.update(dict(steps))
            page = self.bites_go()[0]
            print("\n   " + (self.w["want_own"].format(page=page.name) if page.name == OWN_STACK else self.w["want_sheet"]))  # fmt: skip
            for name in going + [n for n, _ in rides if n not in going]:
                print(f"   - {name}: {lines[name]}")
            keep = self.yes("   " + self.w["want_keep"])
            if keep is not True:
                print("   " + self.w["want_dropped"])
                return None if keep is None else False
        picked = [
            x
            for word, names in choose.items()
            for x in ("--choose", word + "=" + ",".join(names))
        ]
        whys = [x for word, said in why.items() for x in ("--why", word + "=" + said)]
        doc, err = forge("propose", "--box", self.box, words, *picked, *whys)
        if doc is None:
            print("   " + err)
            return False
        stack = None
        for g in doc["groups"]:
            for r in g["rows"]:
                subject = (r["what"].split() or [""])[0]
                if subject.startswith("proposal:"):
                    answer(self.box, self.now, subject, True)
                    stack = subject if r["where"] == FORGE_STACK else stack
        if stack is None:
            print("   " + self.w["want_later"])
            return True
        kept = self.box.joinpath("proposals", stack[9:] + ".json")
        data = json.loads(kept.read_text(encoding="utf-8"))["data"]
        page, made = self.bites_go()
        whole, had = data, 0
        if page.is_file():  # adding to it: under a heading of its own, no step twice
            old = page.read_text(encoding="utf-8")
            new, had = added(old, data[data.index("## ") :])
            whole = old.rstrip("\n") + ("\n\n" + new if new else "\n")
        if whole != data or not page.is_file():
            page.write_text(whole, encoding="utf-8")
        if made:
            print("   " + self.w["want_made"].format(src=OWN_SRC, page=page.name))
        if page.name == OWN_STACK:
            n = sum(1 for ln in data.splitlines() if ln.startswith("- ")) - had
            also = self.w["want_had"].format(had=had) if had else ""
            print("   " + self.w["want_stack"].format(n=n, steps=plural(n, "step"), had=also, page=page))  # fmt: skip
        else:
            n = sum(1 for ln in whole.splitlines() if ln.startswith("- "))
            print("   " + self.w["want_done"].format(n=n, page=page))
        # asked, so answered: what this bite asked is run now, and only that
        with tempfile.TemporaryDirectory() as tmp:
            bite = Path(tmp).joinpath(BITES)
            bite.write_text(data, encoding="utf-8")
            self.ran(BITES, "bite_ran", bite)
        self.next_to(words)
        return True

    def next_to(self, words: str) -> None:
        """What the host's other stacks put beside the steps this bite
        brought: the forge's `next`, at most three lines under one. The
        folders it looks in are those beside this table's own, and only when
        one of them has a stack. It reads, writes nothing to the record, and
        says nothing at all when it has nothing or can't be reached."""
        home = self.box.parent.parent
        if not FORGE.is_file() or not any(
            p.parent != self.box.parent for p in home.glob("*/stack.md")
        ):
            return
        doc, _ = forge("next", words, "--box", self.box, "--stacks", home)
        lines = []
        for g in (doc or {}).get("groups", []):
            if (g["name"] or "").startswith("what your stacks put beside"):
                for r in g["rows"][:3]:
                    name, line = named(r)
                    how = r["what"].rpartition("); ")[2] if "); " in r["what"] else ""
                    lines.append(
                        f"{name}: {line.rstrip('.')}" + (f"; {how}" if how else "")
                    )
        if lines:
            print("\n   " + self.w["next_beside"])
            for ln in lines:
                print("   - " + ln)

    def bites_go(self) -> tuple[Path, bool]:
        """(the page a bite's wants are added to, whether the folder's own
        stack was passed over because it is made from a source). The folder's
        own stack, stack.md beside the box, when it has one that is written
        by hand; else the table's prep sheet."""
        home = self.box.parent
        own = home.joinpath(OWN_STACK)
        made = own.is_file() and home.joinpath(OWN_SRC).is_file()
        return (own if own.is_file() and not made else home.joinpath(PREP)), made

    def page_named(self, typed: str) -> Path | None | bool:
        """The page a typed line names: a file under the folder the box reads,
        beside the box, or at the path as typed. None when the line names no
        file (so it is a sentence); False when it said `read` and none is
        there, which is said."""
        asked = typed.lower().startswith("read ")
        name = typed[5:].strip() if asked else typed.strip()
        if name and "\n" not in name:
            try:
                roots = [kernel.folder(kernel.config(self.box)), self.box.parent]
            except Exception:  # noqa: BLE001  a box that won't say what it reads
                roots = [self.box.parent]
            for at in [Path(name).expanduser()] + [
                Path(r).joinpath(name) for r in roots
            ]:
                try:
                    if at.is_file():
                        return at
                except OSError:
                    pass
        if asked:
            print("   " + self.w["no_page"].format(name=name))
            return False
        return None

    def read(self, page: Path) -> bool | None:
        """A page as the bite. The forge's scan is given the page's text, the
        same scan a sentence gets; each thing it reaches is shown with the
        line it came from; and the want goes on in those words alone, with
        the page's name, so the page's text is not what the record keeps.
        None if the host has gone."""
        if not FORGE.is_file():
            print("   " + self.w["no_forge"])
            return False
        try:
            raw = page.read_bytes()
        except OSError:
            raw = b"\0"
        if b"\0" in raw[:4096]:
            print("   " + self.w["page_cant"].format(page=page.name))
            return False
        text = raw[:PAGE_MOST].decode("utf-8", errors="replace")
        lines = text.splitlines()

        def reached(span: str) -> tuple[list[str], set] | None:
            doc, _ = forge("suggest", "--plan", "--box", self.box, span)
            if not doc or "forks" not in doc:
                return None
            words = list(doc["forks"])
            for step in doc["steps"]:
                said = re.search("“(.+?)”", step["why"])
                words.append(said.group(1) if said else step["name"])
            return words, set(doc["forks"]) | {x["name"] for x in doc["steps"]}

        got = reached(text)
        if got is None:
            print("   " + self.w["no_forge"])
            return False
        at: dict[int, list[str]] = {}
        for word in dict.fromkeys(got[0]):
            find = re.compile(r"(?<!\w)" + re.escape(word), re.IGNORECASE)
            n = next((i for i, ln in enumerate(lines, 1) if find.search(ln)), None)
            if n is not None:
                at.setdefault(n, []).append(word)
        if not at:
            print("   " + self.w["page_none"].format(page=page.name))
            return False
        print("   " + self.w["page_read"].format(page=page.name))
        if len(raw) > PAGE_MOST:
            print("   " + self.w["page_long"].format(n=len(lines)))
        for n in sorted(at):
            words = ", ".join(f"“{w}”" for w in at[n])
            print(
                f"     {page.name}:{n}  {lines[n - 1].strip()[:PAGE_LINE]}  ({words})"
            )
        words = [w for n in sorted(at) for w in at[n]]
        # the want, in the page's own words that reached something; held to
        # reach just what the page reached, or said in the lines themselves
        for sentence in (", ".join(words) + f" (from {page.name})", " ".join(words)):
            if (again := reached(sentence)) is not None and again[1] == got[1]:
                break
        else:
            sentence = " ".join(lines[n - 1].strip() for n in sorted(at))
        return self.want(sentence)

    def ran(self, which: str, lead: str, page: Path | None = None) -> bool:
        """The table's prep or end sheet, run now, and read back a want at a
        time: what was wanted, then what the step that answers it said."""
        got = run_sheet(self.box, which, page)
        if got is None:
            print("   " + self.w["no_sheet"])
            return False
        folder, said = got
        self.found = [(want, found) for want, _, found in said if found]
        print("\n" + self.w[lead])
        for want, line, found in said:
            print("  " + want + "\n     " + line)
            # asked, so answered: the lines themselves, the first few, each
            # with where it is from; the rest are in the step's page
            for where, what in found[:SHOWN]:
                print("       " + what + (f"  ({where})" if where else ""))
            if len(found) > SHOWN:
                print("       " + self.w["more_found"].format(n=len(found) - SHOWN))
        print("\n" + self.w["pages"].format(folder=folder))
        return True

    def sit(self) -> int:
        """The sitting: the table's own prompt, until Enter. What was brought
        in is counted in one line and left alone until the host asks (c)."""
        print(self.w["title"] + "\n")
        self.previously()
        left = waiting(self.box, rows_of(self.box))
        if left:
            print(left_for_you(self.w["waits"], left) + "\n")
        if self.matters:
            print(self.w["matter_key"].format(matters=", ".join(self.matters)) + "\n")
        if sheet(self.box, PREP):
            print(self.w["prep_there"] + "\n")
        first = True
        while True:
            print(self.w["hint" if first else "hint_again"])
            first = False
            got = self.ask(f"{self.at}> ")
            if got is None:
                print(self.w["waiting"])
                return kernel.ESCALATE
            if got == "":
                return self.end()
            key = SAID_AS.get(got.lower(), "")
            if key == "o":
                gone = self.brought() is None
            elif key == "c":
                gone = self.calls() is None
            elif key == "m":
                gone = self.which_matter() is None
            elif key == "s":
                gone = self.stands() is not None
            elif key == "u":
                gone = self.undo() is None
            elif key == "p":
                gone = self.keys(got, False)
            elif key == "w":
                gone = self.want() is None
            elif key == "r":
                gone = self.ran(PREP, "prep_ran") is None
            elif key == "?":
                gone = print(self.w["help"]) is not None
            elif key == "k":
                line = self.ask("   " + self.w["say_ask"])
                gone = line is None or (bool(line) and self.own(line) is None)
            elif got.lower().startswith(("say ", "keep ")):
                gone = self.own(got.split(None, 1)[1].strip()) is None
            else:  # the default: a bite, a question for the host's files
                page = self.page_named(got)
                if page is None:
                    gone = self.want(got) is None
                else:  # a page is a sentence that ran long: the same scan reads it
                    gone = page is not False and self.read(page) is None
            if gone:
                print("\n" + self.w["waiting"])
                return kernel.ESCALATE
            print()


# ── the command line ─────────────────────────────────────────────────────────
def read_words(path: Path) -> dict:
    """The table's words with a file's own put over them: `name: text` a
    line, `#` a comment, `\\n` a new line. A name the list lacks is refused."""
    out = dict(WORDS)
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name, sep, text = line.partition(":")
        if not sep or name.strip() not in WORDS:
            raise Refused(
                f"{path} line {n}: {name.strip()!r} is not one of the table's words"
            )
        out[name.strip()] = text.strip().replace("\\n", "\n") + (" " if WORDS[name.strip()].endswith(" ") else "")  # fmt: skip
    return out


def cmd_moves(seat: str | None) -> int:
    for s in [seat] if seat else [HOST, GUEST]:
        print(f"{s}:")
        for name, what in MOVES[s]:
            print(f"  {name:<10} {what}")
    if contradictions is None:
        print("no heads-up: the contradictions add-on isn't here")
    return kernel.ALIVE


def a_matter(box: Path, at: str) -> str:
    """AT, if it is one of this table's matters; refused, naming them, if not."""
    names = matters(box)
    if at and at not in names:
        raise Refused(
            f"--at {at}: this table's matters are {', '.join(names)}" if names
            else f"--at {at}: this table is over one folder, and has no matters to name"
        )  # fmt: skip
    return at


def cmd_stands(box: Path, as_json: bool, at: str = "") -> int:
    now = standing(box, rows_of(box))
    if a_matter(box, at):
        now = [t for t in now if t["matter"] == at]
    of = f" about {at}" if at else ""
    if as_json:
        print(json.dumps([{k: t[k] for k in ("day", "by", "matter", "fact", "subject")} for t in now],
                         ensure_ascii=False))  # fmt: skip
    elif not now:
        print(f"table: nothing has been made true at this table yet{of}")
    else:
        print(
            f"table: {len(now)} thing{'s' * (len(now) != 1)} this table holds true{of}"
        )
        for matter, its in by_matter(now):
            if any(t["matter"] for t in now) and not at:
                print(f"  {matter or 'the table itself'}")
            for t in its:
                print(f"  {t['day']}  {t['by']:<8}  {t['fact']}")
    return kernel.ALIVE if now else kernel.ESCALATE


def cmd_bring(box: Path, now: str, by: str, fact: str, at: str = "") -> int:
    a_matter(box, at)
    by, fact = " ".join(by.split()), " ".join(fact.split())
    if not by or by.lower() == HOST or len(by) > 40:
        raise Refused("--as NAME: who brings it in, in 40 characters; the host's own word is said at the table")  # fmt: skip
    if not fact or len(fact) > LONGEST:
        raise Refused(
            f"what they bring in is one passage, at most {LONGEST} characters"
        )
    what, when, subject = offered(box, rows_of(box), by, fact, at)
    if what == "declined":
        print(f"the host said no to this on {when}: it is not offered again")
        return kernel.ALIVE
    if what == "sealed":
        print(f"this table has held this true since {when}")
        return kernel.ALIVE
    there = len(waiting(box, rows_of(box)))
    if what != "open":
        if there >= MOST_WAITING:
            # attention is the host's: what waits is never more than they can
            # get through, so a guest is told to wait its turn, with why
            raise Refused(
                f"{there} things already wait on the host, and {MOST_WAITING} is the most: "
                "nothing more is brought in until they have answered some"
            )
        subject = bring(box, now, by, fact, at)
        there += 1
    print(f"waiting on the host's call: {subject}")
    print(f"  {there} waiting on them now, of {MOST_WAITING} at most; they are asked only when they choose")  # fmt: skip
    return kernel.ESCALATE


def offered(box: Path, rows: list[dict], by: str, fact: str, at: str = "") -> tuple[str, str, str]:  # fmt: skip
    """Whether these words by this name, about this matter, were handed in
    before, on any day, and where that stands: ("open", "", its subject)
    while it still waits; ("declined", the day, "") once the host said no;
    ("sealed", the day, "") while it stands; ("", "", "") when it is new, or
    was true and has since been replaced or taken back, so saying it again
    is a new suggestion. What the host refused is not offered to them again
    (CONST-V-11); it is theirs to bring back, at the table."""
    still = {t["subject"]: t for t in standing(box, rows)}
    for r in reversed(said(rows)):
        if (r["by"], r["fact"], r.get("matter", "")) != (by, fact, at):
            continue
        what, got = ruling(box, rows, r["subject"])
        if what == "open":
            return "open", "", r["subject"]
        if what == "declined":
            return "declined", got["ts"][:10], ""
        if r["subject"] in still:
            return "sealed", still[r["subject"]]["day"], ""
        return "", "", ""
    return "", "", ""


TABLE_WORDS = "table-words.txt"  # a table's own words, kept beside its box
#: what the host may type at the table's prompt, and the move each is
SAID_AS = {"look": "c", "c": "c", "list": "s", "s": "s", "who": "o", "o": "o",
           "undo": "u", "u": "u", "pause": "p", "p": "p", "about": "m", "m": "m",
           "?": "?", "help": "?", "prep": "r", "want": "w", "say": "k", "keep": "k"}  # fmt: skip


def plural(n: int, word: str) -> str:
    return word if n == 1 else word + "s"


def left_for_you(words: str, left: list[dict]) -> str:
    """One sentence on what waits: who left it (each name once, without
    what kind of word they said it was), and how much."""
    names = list(dict.fromkeys(r["by"].split(",")[0].strip() for r in left))
    who = names[0] if len(names) == 1 else f"{names[0]} and {names[1]}" if len(names) == 2 else f"{names[0]} and others"  # fmt: skip
    n = len(left)
    return words.format(who=who, n=n, things=plural(n, "thing"),
                        first="it" if n == 1 else "the first two")  # fmt: skip


def tables(home: Path) -> list[dict]:
    """The tables under HOME: each folder there whose box has been sat at
    or brought to, A to Z. For each: its box, its words (its own file beside
    the box, when there is one), how many things it holds true, and how many
    wait. A box is a table once it has been sat at or brought a word, or
    once a table was laid for it: its words, a prep sheet or an end sheet
    put beside it. Any other box is no table yet, and is not opened to
    find out; one whose record doesn't check out is named as so."""
    out = []
    for box in [home.joinpath("box")] + sorted(home.glob("*/box")):
        record = box / "record.jsonl"
        try:
            laid = any(
                box.parent.joinpath(f).is_file() for f in (TABLE_WORDS, PREP, END)
            )
            sat_at = '"table-' in record.read_text(encoding="utf-8", errors="replace")
            if not (box / "kernel.json").is_file() or not (laid or sat_at):
                continue
        except OSError:
            continue
        own = box.parent / TABLE_WORDS
        try:
            words = read_words(own) if own.is_file() else dict(WORDS)
            rows = rows_of(box)
            t = {"stands": standing(box, rows), "waiting": waiting(box, rows)}
        except Refused as e:
            words, t = dict(WORDS), {"broken": str(e)}
        name = words["title"] if words["title"] != WORDS["title"] else box.parent.name
        out.append({"box": box, "words": words, "name": name, **t})
    return out


def gather(gathered: dict[str, list[tuple[str, list]]]) -> None:
    """What a bite asked at every table found, together: for each want, the
    lines from every table, each ending with the table's name and where the
    line is from. At most SHOWN from each table, and how many more."""
    if not any(lines for tabs in gathered.values() for _, lines in tabs):
        return
    print("\n" + WORDS["all_found"])
    for want, tabs in gathered.items():
        print("  " + want)
        for name, lines in tabs:
            for where, what in lines[:SHOWN]:
                print("       " + what + "  (" + name + (", " + where if where else "") + ")")  # fmt: skip
            if len(lines) > SHOWN:
                print("       " + WORDS["more_at"].format(n=len(lines) - SHOWN, table=name))  # fmt: skip


def cmd_home(home: Path, now: str | None) -> int:
    """The front door: the host's tables, each with what it holds and what
    waits; they pick one and sit; when that sitting ends, is paused or is
    left, they are back here. Enter leaves."""
    if not home.is_dir():
        raise Refused(f"{home} isn't a folder")
    while True:
        found = tables(home)
        if not found:
            print(
                f"No table under {home} has been sat at yet: table.py --box DIR sits at one."
            )
            return kernel.ESCALATE
        print(
            WORDS["tables"].format(n=len(found), tables=plural(len(found), "table"))
            + "\n"
        )
        for i, t in enumerate(found, 1):
            print(f"  {i}. {t['name']}")
            if "broken" in t:
                print(f"     {t['broken']}")
                continue
            n = len(t["stands"])
            line = (
                WORDS["settled"].format(n=n, things=plural(n, "thing"))
                if n
                else WORDS["unsettled"]
            )
            if t["waiting"]:
                line += " " + left_for_you(WORDS["left"], t["waiting"])
            print(f"     {line}")
        no_box = sorted(
            p.parent.name
            for p in home.glob("*/stack.md")
            if not p.parent.joinpath("box").exists()
        )
        if no_box:
            n = len(no_box)
            print("\n" + WORDS["no_box"].format(n=n, folders=plural(n, "folder"),
                                                have="has" if n == 1 else "have",
                                                names=", ".join(no_box)))  # fmt: skip
        try:
            got = input("\n" + WORDS["which_table"]).strip()
        except EOFError:
            print()
            return kernel.ALIVE
        if got == "":
            return kernel.ALIVE
        if not got.isdigit() and len(got) > 1:  # a bite, asked at every table here
            ask, said, gathered = [t for t in found if "broken" not in t], {}, {}
            print(
                "\n"
                + WORDS["ask_all"].format(n=len(ask), tables=plural(len(ask), "table"))
            )
            for t in ask:
                print("\n" + t["name"])
                seat = Seat(t["box"], now or kernel.now(), t["words"])
                seat.said = said
                try:
                    page = seat.page_named(got)
                    gone = (
                        page is False
                        or (seat.read(page) if page else seat.want(got)) is None
                    )
                except Pause:
                    print("\n" + t["words"]["paused"])
                    break
                for want, lines in seat.found:
                    gathered.setdefault(want, []).append((t["name"], lines))
                if gone:
                    break
            if len(ask) > 1:
                gather(gathered)
            print("\n" + WORDS["back"] + "\n")
            continue
        if not (got.isdigit() and 1 <= int(got) <= len(found)) or "broken" in found[int(got) - 1]:  # fmt: skip
            print(f"  1 to {len(found)}.\n")
            continue
        t = found[int(got) - 1]
        print()
        try:
            Seat(t["box"], now or kernel.now(), t["words"]).sit()
        except Pause:
            print("\n" + t["words"]["paused"])
        print("\n" + WORDS["back"] + "\n")


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    rest: list[str] = []
    it = iter(argv)
    for a in it:
        if (
            a in ("--box", "--home", "--words", "--now", "--as", "--at", "--seat")
            and a not in opts
        ):
            opts[a] = next(it, "")
        elif a == "--json" and a not in opts:
            opts[a] = "yes"
        else:
            rest.append(a)
    cmd = rest[0] if rest else ""
    takes = {"": {"--box", "--home", "--words", "--now"}, "bring": {"--box", "--now", "--as", "--at"},
             "stands": {"--box", "--json", "--at"}, "moves": {"--seat"}}  # fmt: skip
    if (
        cmd not in takes
        or set(opts) - takes[cmd]
        or any(not v for v in opts.values())
        or len(rest) != (2 if cmd == "bring" else 1 if cmd else 0)
        or (cmd in ("bring", "stands") and "--box" not in opts)
        or (cmd == "" and ("--box" in opts) == ("--home" in opts))
        or ("--home" in opts and "--words" in opts)
        or (cmd == "bring" and "--as" not in opts)
        or opts.get("--seat", HOST) not in MOVES
        or any(a.startswith("--") for a in rest)
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    try:
        if cmd == "moves":
            return cmd_moves(opts.get("--seat"))
        if "--home" in opts:
            return cmd_home(Path(opts["--home"]).expanduser(), opts.get("--now"))
        box = Path(opts["--box"])
        if not (box / "kernel.json").is_file():
            raise Refused("not a kernel box; init first")
        now = opts.get("--now") or kernel.now()
        if cmd == "stands":
            return cmd_stands(box, "--json" in opts, opts.get("--at", ""))
        if cmd == "bring":
            return cmd_bring(box, now, opts["--as"], rest[1], opts.get("--at", ""))
        words = read_words(Path(opts["--words"])) if "--words" in opts else dict(WORDS)
        try:
            return Seat(box, now, words).sit()
        except Pause:
            print("\n" + words["paused"])
            return kernel.ESCALATE
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    except OSError as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
