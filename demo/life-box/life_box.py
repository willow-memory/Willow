"""life_box.py: the game box, with a person's life for its binder. Python 3.9+.

    python demo/life-box/life_box.py open   --who NAME --table DIR [--read] [--dates day-first|month-first] [--piles]
    python demo/life-box/life_box.py week   --table DIR
    python demo/life-box/life_box.py words  --table DIR
    python demo/life-box/life_box.py ask    --table DIR
    python demo/life-box/life_box.py decide --table DIR
    python demo/life-box/life_box.py recap  --table DIR

The game box lays a game master's binder, reads it through the game
master's words, preps a night with a stack, and lets nothing stand until
the one who holds the key seals it. This lays the same over one of
willow's made-up lives (demo/NAME, made by its make_life.py), read through
the starter words list a person begins with:

- `open` makes NAME's life at DIR/NAME/life, copies the starter words list
  to DIR/words.txt, and starts the record over the life at DIR/record,
  with a key made for NAME at DIR/NAME.key. NAME is made up, and so is the
  key: this demo seals for them. A real person's key is never made, read
  or used here.
- `--read` reads the life through willow's readers first, as a person
  with mail, calendars, chats, notes, spreadsheets, books and scans would:
  each reader mirrors what it reads into DIR/NAME-read, the files no reader
  took are copied beside them as they are, and the box is laid over that.
  Without it, the box is laid over the life as written, which suits a life
  of plain files; a scan or a spreadsheet is never read raw.
- `--dates day-first` (or month-first) says the order the life's dates
  are written in, which only its writer knows: the life is mirrored through
  that add-on, each date given its ISO form beside it, and the box laid over
  the mirror, so 03/11/2026 is the 3rd of November to every reader of dates.
  Without it, a date that reads both ways is left unread.
- `--piles` lays the life the way a person keeps it, a folder per matter,
  each its own pile with its own box (DIR/records/SLUG), all under the one
  key made for NAME: each top-level folder of the life is a pile; a folder
  holding exactly one folder and no files is walked through (`Notes/` to
  `Notes/Bernie's Vault/`), so the folders inside are the piles; files
  loose at a level are one more pile, named for that level (`.` for the
  top). A folder's own name then stops being a word every passage in it
  holds for free (a recipe in `Recipes/` is no likelier to hold "recipe"
  than a chat line saying it is). DIR/piles.json says which folder each
  box is. DIR/record is laid beside them over the whole life: the week
  and the spelling add-ons each read one box, and read it whole.
- `week` runs week.md, a week's prep over the life, at NAME's own today
  (the TODAY their make_life.py writes them at), kept in DIR/week/NNN,
  beside NNN.md, the stack as it ran.
- `ask` asks each of NAME's own questions (demo/NAME/QUESTIONS.md) and
  hands in every passage served as a suggested answer, citing it. A
  question is first read the way their files spell it: the typos add-on,
  then accents, each over the box; when that reads it differently
  ("dermatoligist referal letter" as "dermatologist referral letter") it is
  asked as read, once, and the claim and the recap say `asked as "..."`.
  Nothing
  is an answer yet: each waits on the seal. First the route add-on reads
  what kind each question is, and names the steps whose job that kind is
  ("has kirsty paid me yet" is money owed: debts and invoices) with the
  file the latest week kept each one's output in, kept in DIR/route.json.
  A sum over many passages is a step's to give, not one passage's.
  With piles, every pile's box is bitten, the passages each served are
  dealt out in turns by fair-merge's own rule (first of each pile, then
  second of each, a passage word for word in two piles once, the question
  asked back left out) up to DEAL of them, and each is proposed in the box
  that served it, citing that box's last bite. The claim's `from` is the
  path in the whole life, so NAME.json reads the same.
  A word of the question that names a pile ("on the kindle" names `Kindle/`;
  "recipe" names `Recipes/`, the way the kernel holds a word, so a plural
  or a stem counts) says where to look, not what the text says: the question
  is asked of that pile alone, without the naming words (`asked of Kindle as
  "that quote about loss i highlighted on the"`, in the claim and the recap),
  and the other piles are not asked. A question left with no content word is
  asked as it is. A pile is named for its own folder's last part, so the top
  level's loose files are never named.
  A question that asks two things is asked as each. ask-parts splits it
  ("what did colleen say about mam's headstone, how much was my half"
  into "what did colleen say about mam's headstone" and "how much was my
  half"), because the kernel serves a passage only when it holds half the
  question's content words, and the email that says "Your half is EUR 725"
  holds one of the five. Each part goes the whole way above (spelling read,
  a pile it names, every pile bitten, dealt in turns), and its passages are
  proposed right after its own bite in the box that served them, since a
  proposal reaches only that box's last bite. The parts share the question's
  DEAL, the first taking the remainder. The claim still says
  `answers question {i}, "{q}"` with the whole question, then ends with
  `, part 2 "how much was my half"`; recap shows each part line under the
  question. A question of one part is asked as it always was, its claim with
  no part.
- `words` is day two: a starter list is general, and a person's own words
  are theirs, learned from the questions that found nothing. For a NAME that
  has a NAME-words.txt beside this (bernadette-words.txt: only their lines,
  each with a comment saying whose file uses their word, and what it says
  instead), it writes DIR/words.txt again as the starter list and then their
  lines, readable only by them, and says what was added. Every box of the life
  was made pointing at that one file, and the kernel reads it at each bite,
  so no box is made again (a box that points at no list is what later-words
  is for) and no record changes: the rows already there stay as they were,
  and from the next bite on each row names the new list by its SHA-256.
  A NAME with no such file is refused, and nothing changes. Then `ask`
  again.
- `ask`, asked again, asks only the questions with no sealed answer yet: a
  question already answered is said so and left alone, since asking it
  would only add bites that serve nothing (the kernel answers a sealed
  question from the seal). A question that was offered, and declined, or
  found nothing, is asked again, with the words it has now.
- `decide` is NAME, deciding: every suggestion is sealed with NAME's key if
  NAME's answer key (NAME.json, beside this) names its file, and what it
  must say, for that question; every other is declined. It runs only for a
  made-up person with an answer key.
- `recap` prints what NAME sealed as their answers, and what they said no
  to, each question with the passage it rests on (with piles, naming the
  pile of each, walking every box).

Exit codes, the kernel's: 0 done; 42 waiting on the seal; 2 refused.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "fair-merge"))
import fair_merge  # noqa: E402

sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "ask-parts"))
import ask_parts  # noqa: E402

DEMO = ROOT / "demo"
STARTER = ROOT / "adapters" / "stdlib" / "starter-words" / "starter.py"
STACK = ROOT / "adapters" / "stdlib" / "stack" / "stack.py"
ROUTE = ROOT / "adapters" / "stdlib" / "route" / "route.py"
#: the add-ons that say how a question reads in the files' own spelling, in the order they run
SPELLING = [ROOT / "adapters" / "stdlib" / "typos" / "typos.py",
            ROOT / "adapters" / "stdlib" / "accents" / "accents.py"]  # fmt: skip
ORDERS = {  # a folder's date order, which only its writer knows, and the add-on that marks it
    "day-first": ROOT / "adapters" / "stdlib" / "day-first" / "day_first.py",
    "month-first": ROOT / "adapters" / "stdlib" / "month-first" / "month_first.py",
}
#: The readers --read runs, each by its own command line; pdf is a deps add-on,
#: read where pypdf is installed and said to be unreachable where it isn't
STD = ROOT / "adapters" / "stdlib"
READERS = [STD / "mail" / "mail.py", STD / "calendar" / "cal.py", STD / "chats" / "chats.py",
           STD / "notes" / "notes.py", STD / "office" / "office.py", STD / "books" / "books.py",
           ROOT / "adapters" / "deps" / "pdf" / "pdf.py"]  # fmt: skip
WEEK = HERE / "week.md"
#: passages dealt out across piles for one question. One box offers the
#: kernel's TOP (3), but three turns across a dozen piles never reach the later
#: piles (Bernadette's Q3 and Q15 answers are not reached at 3 or 6). By DEAL,
#: with a question that names a pile asked of that pile alone, answered / of 20
#: (Bernadette; without pypdf; Teodora): 3 is 10, 9, 11; 6 is 14, 14, 11; 7 is
#: 16, 15, 11, as many as 10 answers; 10 is 16, 15, 11, and seals three more
#: passages on questions already answered (a cancellation mail, a calendar line,
#: a jeweller's mail). The smallest that answers as many is 7.
#: The parts of a question that asks two things share its DEAL, 4 and 3 for two. Measured
#: on Bernadette's piles, Teodora's and one box, each part dealt DEAL and the parts sharing
#: it seal the same (25, 19, 22) and hold every trap; sharing offers five fewer on
#: Bernadette's piles, 91 against 96 (89 against 94 without pypdf)
DEAL = 7
TODAY = re.compile(r"^TODAY = date\((\d{4}), (\d{1,2}), (\d{1,2})\)", re.M)
QUESTION = re.compile(r"^\d+\. (.+)$", re.M)


def py(*argv, **kw) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *map(str, argv)], capture_output=True, text=True, check=False, **kw)  # fmt: skip


def fail(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def today_of(who: str) -> str:
    """NAME's own today, as their make_life.py writes them."""
    m = TODAY.search((DEMO / who / "make_life.py").read_text(encoding="utf-8"))
    if not m:
        raise ValueError(f"demo/{who}/make_life.py names no TODAY")
    y, mo, d = (int(g) for g in m.groups())
    return f"{y:04d}-{mo:02d}-{d:02d}T09:00:00Z"


def questions(who: str) -> list[str]:
    return QUESTION.findall((DEMO / who / "QUESTIONS.md").read_text(encoding="utf-8"))


def words_of(text: str) -> list[str]:
    """A question's words as the kernel splits them: letters and digits."""
    return re.findall(r"[^\W_]+", text.lower())


def read_as(box: Path, q: str) -> str:
    """The question as the person's files spell it: typos, then accents, each
    taking the line starting "ask:  " as how the question reads. They only
    read; asking is ours. The question as written, when nothing changes."""
    read = q
    for script in SPELLING:
        out = py(script, "--box", box, read).stdout
        read = next((x[6:] for x in out.splitlines() if x.startswith("ask:  ")), read)
    return read if words_of(read) != words_of(q) else q


def who_of(table: Path) -> str:
    return (table / "who.txt").read_text(encoding="utf-8").strip()


def box_of(table: Path) -> Path:
    return table / "record"


def has_files(folder: Path) -> bool:
    return any(f.is_file() and not any(p.startswith(".") for p in f.relative_to(folder).parts) for f in folder.rglob("*"))  # fmt: skip


def split_piles(pile: Path) -> list[dict]:
    """The life as the piles a person keeps: each top-level folder is one; a
    folder holding exactly one folder and no files is walked through; the files
    loose at a level are one more, named for the level. Each is {slug, folder
    (relative to `pile`, "" at the top), loose (only its own files), name}."""
    found: list[tuple[str, bool]] = []

    def walk(at: Path, rel: str) -> None:
        kids = sorted(p for p in at.iterdir() if p.is_dir() and not p.name.startswith("."))  # fmt: skip
        if any(p.is_file() and not p.name.startswith(".") for p in at.iterdir()):
            found.append((rel, True))
        for k in kids:
            sub, way = f"{rel}/{k.name}" if rel else k.name, k
            while len(inside := [p for p in way.iterdir() if not p.name.startswith(".")]) == 1 and inside[0].is_dir():  # fmt: skip
                way = inside[0]  # a folder that only holds a folder is only a way in
                sub = f"{sub}/{way.name}"
            if way is not k:
                walk(way, sub)  # where the way in ends is a level of its own
            elif has_files(k):
                found.append((sub, False))

    walk(pile, "")
    out, seen = [], set()
    for rel, loose in found:
        base = re.sub(r"[^a-z0-9]+", "-", f"{rel}/{'loose' if loose else ''}".lower()).strip("-") or "loose"  # fmt: skip
        slug, n = base, 2
        while slug in seen:
            slug, n = f"{base}-{n}", n + 1
        seen.add(slug)
        out.append({"slug": slug, "folder": rel, "loose": loose, "name": (f"{rel}/." if rel else ".") if loose else rel})  # fmt: skip
    return out


def pile_words(p: dict) -> list[str]:
    """The words a pile's own name says: its folder's last part (a loose pile's
    level, so `Notes/Vault/.` says Vault), as the kernel splits words, less the
    common ones. The top level's loose files are named for nothing."""
    return [w for w in kernel.words(p["folder"].rsplit("/", 1)[-1]) if w not in kernel.FUNCTION]  # fmt: skip


def naming(q: str, piles: list[dict]) -> dict[str, str]:
    """The piles a question names, each with the question as that pile is asked:
    a word of it that the pile's own name holds (the way the kernel holds a
    word: "recipe" names `Recipes`) is where to look, not a word in the text, so
    it is left out. A question left with no content word is asked as it is."""
    found = {}
    for p in piles:
        toks = kernel.forms(pile_words(p))
        hit = {w for w in kernel.words(q) if w not in kernel.FUNCTION and kernel.holds(w, toks)}  # fmt: skip
        if hit:
            left = re.sub(r"[^\W_]+", lambda m: "" if unicodedata.normalize("NFC", m.group().lower()) in hit else m.group(), q)  # fmt: skip
            left = " ".join(left.split())
            found[p["slug"]] = left if set(kernel.words(left)) - kernel.FUNCTION else q
    return found


def piles_of(table: Path) -> list[dict]:
    """The piles open laid, in the order they take turns; none without --piles."""
    f = table / "piles.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else []


def boxes_of(table: Path) -> list[Path]:
    """The boxes to walk: one per pile, or the one box."""
    return [table / "records" / p["slug"] for p in piles_of(table)] or [box_of(table)]


def sealed_answers(table: Path) -> dict[int, list[str]]:
    """Each question number with a sealed answer in any box, and where each
    answer is: read from the claim of the proposal that was sealed."""
    out: dict[int, list[str]] = {}
    for box in boxes_of(table):
        rows, _ = kernel.read(box / "record.jsonl")
        for r in rows:
            if r["kind"] == "seal":
                prop = json.loads((box / "proposals" / f"{r['subject'][9:]}.json").read_text(encoding="utf-8"))  # fmt: skip
                if m := CLAIM.match(prop["claim"]):
                    out.setdefault(int(m.group(1)), []).append(f"{m.group(4)}:{m.group(5)}")  # fmt: skip
    return out


def read_life(life: Path, to: Path) -> list[str]:
    """Every reader over the life into one mirror, then the files no reader
    took copied beside them; what each reader said, one line each."""
    said = []
    for script in READERS:
        got = py(script, "mirror", "--from", life, "--to", to)
        if got.returncode == 2 and ("pip install" in got.stderr or "ModuleNotFoundError" in got.stderr):  # fmt: skip
            said.append(f"{script.parent.name}: unreachable, {script.parent.name}'s package isn't installed")  # fmt: skip
        elif got.returncode == 2:
            raise ValueError(f"{script.parent.name}: {got.stderr.strip()}")
        else:
            said.append(f"{script.parent.name}: {(got.stdout.strip().splitlines() or ['read nothing'])[-1].replace(str(to), to.name)}")  # fmt: skip
    left = 0
    for f in sorted(life.rglob("*")):
        rel = f.relative_to(life)
        if f.is_file() and not any(p.startswith(".") for p in rel.parts) and not (to / f"{rel}.txt").exists():  # fmt: skip
            (to / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, to / rel)
            left += 1
    said.append(f"copied: {left} files no reader took, as they are")
    return said


def cmd_open(
    who: str, table: Path, dates: str = "", read: bool = False, piles: bool = False
) -> int:
    if not re.fullmatch(r"[a-z][a-z-]*", who) or not (DEMO / who / "make_life.py").is_file():  # fmt: skip
        return fail(
            f"{who!r} isn't one of willow's made-up lives (demo/NAME/make_life.py)"
        )
    if not (DEMO / who / "QUESTIONS.md").is_file():
        return fail(f"demo/{who} has no QUESTIONS.md of their own")
    if dates and dates not in ORDERS:
        return fail(f"--dates is {' or '.join(ORDERS)}: the order the life's dates are written in")  # fmt: skip
    if table.exists():
        return fail(f"{table} is there already: a life box is laid in a new folder")
    table.mkdir(parents=True)
    shutil.copytree(DEMO / who, table / who, ignore=shutil.ignore_patterns("life", "__pycache__"))  # fmt: skip
    made = py(table / who / "make_life.py", cwd=table / who)
    if made.returncode != 0:
        return fail(f"{who}'s make_life.py: {made.stderr.strip()}")
    pile = table / who / "life"
    if read:
        try:
            said = read_life(pile, table / f"{who}-read")
        except ValueError as e:
            return fail(f"reading the life: {e}")
        pile = table / f"{who}-read"
        print("read:\n" + "".join(f"  {s}\n" for s in said), end="")
    if (
        dates
    ):  # each date given its ISO form beside it, so every reader of dates can place it
        marked = py(
            ORDERS[dates], "mirror", "--from", pile, "--to", table / f"{who}-{dates}"
        )
        if marked.returncode != 0:
            return fail(f"{dates}: {marked.stderr.strip()}")
        pile = table / f"{who}-{dates}"
    now = today_of(who)
    words = py(STARTER, "copy", "--to", table / "words.txt")
    if words.returncode != 0:
        return fail(f"the starter words list: {words.stderr.strip()}")
    init = py(ROOT / "kernel.py", "init", "--box", box_of(table), "--pile", pile,
              "--key", table / f"{who}.key", "--words", table / "words.txt", "--now", now)  # fmt: skip
    if init.returncode != 0:
        return fail(f"the record: {init.stderr.strip()}")
    laid = []
    if piles:
        # the whole life stays one box too (DIR/record): the week and the
        # spelling add-ons each read one box. Every pile's box then takes the
        # same key, which init accepts once it is there.
        for p in split_piles(pile):
            if p[
                "loose"
            ]:  # a box lays a folder, so a level's own files are copied to one
                at = table / "loose" / p["slug"]
                at.mkdir(parents=True)
                for f in sorted((pile / p["folder"]).iterdir()):
                    if f.is_file() and not f.name.startswith("."):
                        shutil.copyfile(f, at / f.name)
            else:
                at = pile / p["folder"]
            made = py(ROOT / "kernel.py", "init", "--box", table / "records" / p["slug"], "--pile", at,
                      "--key", table / f"{who}.key", "--words", table / "words.txt", "--now", now)  # fmt: skip
            if made.returncode != 0:
                return fail(f"the {p['name']} pile's record: {made.stderr.strip()}")
            p["files"] = sum(1 for f in at.rglob("*") if f.is_file())
            laid.append(p)
        (table / "piles.json").write_text(json.dumps(laid, indent=1, ensure_ascii=False), encoding="utf-8")  # fmt: skip
    (table / "who.txt").write_text(who + "\n", encoding="utf-8")
    files = sum(1 for p in pile.rglob("*") if p.is_file())
    print(
        f"{who}'s life is laid at {table}: {files} files, read through the starter words list,"
    )
    if dates:
        print(f"its dates read {dates}, each given its ISO form beside it by the {dates} add-on, at {pile}.")  # fmt: skip
    if piles:
        print(f"as {len(laid)} piles, a box each under the one key:")
        for p in laid:
            print(f"  {p['slug']:<40} {p['files']:>4} files  {p['name']}")
    print(f"the record started at {now[:10]}, their today. {table / f'{who}.key'} is a key made for {who}, who is made up.")  # fmt: skip
    return kernel.ALIVE


STARTER_LIST = ROOT / "adapters" / "stdlib" / "starter-words" / "words.txt"


def cmd_words(table: Path) -> int:
    who = who_of(table)
    own = HERE / f"{who}-words.txt"
    if not own.is_file():
        return fail(f"{who} has no words of their own beside this ({own.name}): the starter list stays as it is")  # fmt: skip
    words = table / "words.txt"
    for box in boxes_of(table):
        cfg = kernel.config(box)
        if "words" not in cfg or Path(cfg["words"]).resolve() != words.resolve():
            return fail(f"{box.name} reads no words list at {words}: make it again with later-words first")  # fmt: skip
    starter = STARTER_LIST.read_text(encoding="utf-8")
    theirs = own.read_text(encoding="utf-8")
    text = (
        f"{starter.rstrip(chr(10))}\n\n# {who}'s own words, from {own.name}\n{theirs}"
    )
    why = kernel.parse_words(text)[1]
    if why:
        return fail(f"{own.name}: {why}")
    if words.read_text(encoding="utf-8") == text:
        print(f"{words} already holds {who}'s own words; nothing changed.")
        return kernel.ALIVE
    words.write_text(text, encoding="utf-8")
    words.chmod(0o600)
    added = kernel.parse_words(theirs)[0]
    print(
        f"{who}'s own words, added to the starter list at {words} (readable only by them):"
    )
    for w, ts in sorted(added.items()):
        print(f"  {w} = {', '.join(ts)}")
    print("No record changed; each box reads the list at its next bite. Ask again.")
    return kernel.ALIVE


def cmd_week(table: Path) -> int:
    who = who_of(table)
    n = len(list((table / "week").glob("[0-9][0-9][0-9]"))) + 1 if (table / "week").is_dir() else 1  # fmt: skip
    run = table / "week" / f"{n:03d}"
    run.parent.mkdir(parents=True, exist_ok=True)
    stack = (
        run.parent / f"{n:03d}.md"
    )  # the week at their today; the run's folder is the stack's own
    now = today_of(who)  # the steps' {today} only: the prose naming it stays as written
    text = "".join(ln.replace("{today}", now) if ln.startswith("- ") else ln for ln in WEEK.read_text(encoding="utf-8").splitlines(keepends=True))  # fmt: skip
    stack.write_text(text, encoding="utf-8")  # fmt: skip
    got = py(STACK, "--box", box_of(table), "--stack", stack, "--to", run)
    print(got.stdout, end="")
    print(got.stderr, end="", file=sys.stderr)
    return got.returncode


def routes(table: Path, asked: list[str]) -> dict[int, dict]:
    """Each question's kind, and the steps whose job it is, with the file the
    latest week kept that step's output in: route's own reading, kept."""
    weeks = sorted((table / "week").glob("[0-9][0-9][0-9]")) if (table / "week").is_dir() else []  # fmt: skip
    qfile = table / "questions.txt"
    qfile.write_text("".join(q + "\n" for q in asked), encoding="utf-8")
    got = py(ROUTE, "--questions", qfile, *(["--run", weeks[-1]] if weeks else []), "--json")  # fmt: skip
    qfile.unlink()
    out: dict[int, dict] = {}
    for g in json.loads(got.stdout).get("groups", []) if got.stdout.strip() else []:
        kind = g["name"].rsplit(":", 1)[0]
        steps = []
        for r in g["rows"]:
            if r["where"].startswith("-> "):
                kept = r["what"].rsplit("   ", 1)[-1] if str(table) in r["what"] else ""
                steps.append({"step": r["where"][3:], "kept": str(Path(kept).relative_to(table)) if kept else ""})  # fmt: skip
            elif r["where"].isdigit():
                out[int(r["where"])] = {"kind": kind, "steps": [x for x in steps if x["step"] != "ask"]}  # fmt: skip
    (table / "route.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def sent_to(route: dict) -> str:
    return "".join(f"      see       {x['step']}: {x['kept'] or 'not in this week'}\n" for x in route.get("steps", []))  # fmt: skip


def cmd_ask(table: Path) -> int:
    who, box = who_of(table), box_of(table)
    now = today_of(who)
    piles = piles_of(table)
    handed = 0
    routed = routes(table, questions(who))
    done = sealed_answers(table)
    for i, q in enumerate(questions(who), 1):
        if i in done:  # asked again: an answered question is left alone
            print(
                f"{i:>2}. {q}\n      already answered: sealed, {'; '.join(done[i])}\n",
                end="",
            )
            continue
        kind = f"  ({routed[i]['kind']})" if i in routed else ""
        asks = ask_parts.parts(q)  # a question that asks two things is asked as each
        lines = ""
        for n, part in enumerate(asks, 1):
            read = read_as(box, part)  # asked as the files spell it, once
            how = f'\n      asked as "{read}"' if read != part else ""
            as_ = f', asked as "{read}"' if read != part else ""
            sent = naming(read, piles) if piles else {}
            how += "".join(f'\n      asked of {p["name"]} as "{sent[p["slug"]]}"' for p in piles if p["slug"] in sent)  # fmt: skip
            tag = f', part {n} "{part}"' if len(asks) > 1 else ""
            if piles:
                served, passed = ask_piles(table, piles, i, q, read, as_, now, sent, tag, n if tag else 0, len(asks))  # fmt: skip
            else:
                bite = py(ROOT / "kernel.py", "bite", "--box", box, "--now", now, read)
                served = json.loads(bite.stdout).get("served", []) if bite.stdout.strip() else []  # fmt: skip
                props = [json.dumps({"path": f"answers/q{i:02d}{f'-p{n}' if tag else ''}-{k}.txt", "data": s["text"], "cites": [s["id"]],
                                     "claim": f"answers question {i}, \"{q}\"{as_}, from {s['where']}{tag}"})  # fmt: skip
                         for k, s in enumerate(served, 1)]  # fmt: skip
                passed = 0
                if props:
                    sugg = table / "suggestions.jsonl"
                    sugg.write_text("\n".join(props) + "\n", encoding="utf-8")
                    got = py(ROOT / "kernel.py", "propose", "--box", box, "--now", now, "--file", sugg)  # fmt: skip
                    sugg.unlink()
                    passed = got.stdout.count("pass ")
            lines += f'\n      part {n} "{part}"' if tag else ""
            lines += how
            if served:
                lines += f"\n      {passed} suggested: " + "; ".join(
                    s["where"] for s in served
                )
                handed += passed
            else:
                lines += "\n      nothing in the life holds it"
        print(f"{i:>2}. {q}{kind}{lines}\n" + sent_to(routed.get(i, {})), end="")
    left = f" {len(done)} questions already have a sealed answer and were not asked again." if done else ""  # fmt: skip
    print(
        f"\n{handed} answers wait on {who}'s seal; nothing is an answer until then.{left}"
    )
    return kernel.ESCALATE if handed else kernel.ALIVE


def ask_piles(table: Path, piles: list[dict], i: int, q: str, read: str, as_: str, now: str, sent: dict[str, str], tag: str = "", part: int = 0, of_parts: int = 1) -> tuple[list[dict], int]:  # fmt: skip
    """One question put to every pile's box, the passages they served dealt out
    in turns (fair-merge's rule), each proposed in the box that served it,
    citing only that box's last bite. When the question names piles (`sent`,
    from `naming`) only those are asked, each without the naming words.
    `tag` is the claim's part group when the question was asked in parts, `part`
    its number (0 when it was one), so a part's passages keep paths of their own;
    `of_parts` is how many there are. The parts share the question's DEAL, the
    first parts taking the remainder: 7 passages over two parts is 4 and 3.
    (what was dealt, how many passed)"""

    if sent:  # a question that names a pile is asked of that pile alone
        piles = [p for p in piles if p["slug"] in sent]

    def bitten(p: dict) -> list[dict]:
        bite = py(ROOT / "kernel.py", "bite", "--box", table / "records" / p["slug"], "--now", now, sent.get(p["slug"], read))  # fmt: skip
        got = json.loads(bite.stdout).get("served", []) if bite.stdout.strip() else []
        pre = f"{p['folder']}/" if p["folder"] else ""
        return [{**s, "where": pre + s["where"]} for s in got if not s["echo"]]

    with ThreadPoolExecutor(
        4
    ) as pool:  # each box is its own folder: the bites don't meet
        lists = [(p["slug"], got) for p, got in zip(piles, pool.map(bitten, piles))]
    lists, _ = fair_merge.joined(lists)
    dealt, _ = fair_merge.merge(lists, max(1, DEAL // of_parts + (part <= DEAL % of_parts)) if part else DEAL)  # fmt: skip
    passed = 0

    def of(
        p: dict,
    ) -> str:  # sent to the pile by name: where to look, said in the claim
        return (
            f', asked of {p["name"]} as "{sent[p["slug"]]}"'
            if p["slug"] in sent
            else ""
        )

    for p in piles:
        mine = [(k, s) for k, (name, s) in enumerate(dealt, 1) if name == p["slug"]]
        if not mine:
            continue
        props = [json.dumps({"path": f"answers/q{i:02d}{f'-p{part}' if part else ''}-{k}.txt", "data": s["text"], "cites": [s["id"]],
                             "claim": f"answers question {i}, \"{q}\"{as_}, from {s['where']}{of(p)}{tag}"})  # fmt: skip
                 for k, s in mine]  # fmt: skip
        sugg = table / "suggestions.jsonl"
        sugg.write_text("\n".join(props) + "\n", encoding="utf-8")
        got = py(ROOT / "kernel.py", "propose", "--box", table / "records" / p["slug"], "--now", now, "--file", sugg)  # fmt: skip
        sugg.unlink()
        passed += got.stdout.count("pass ")
    names = {p["slug"]: p["name"] for p in piles}
    return [
        {**s, "where": f"{s['where']} [{names[name]}]"} for name, s in dealt
    ], passed


def waiting(box: Path) -> list[tuple[str, dict]]:
    """Each suggestion that passed and has no seal or decline yet, with its claim."""
    rows, _ = kernel.read(box / "record.jsonl")
    done = {r.get("subject") for r in rows if r["kind"] in ("seal", "decline")}
    out = []
    for r in rows:
        if (
            r["kind"] == "proposal"
            and r.get("verdict") == "pass"
            and r["subject"] not in done
        ):
            prop = json.loads((box / "proposals" / f"{r['subject'][9:]}.json").read_text(encoding="utf-8"))  # fmt: skip
            out.append((r["subject"], prop))
    return out


CLAIM = re.compile(
    r'^answers question (\d+), "(.*?)"(?:, asked as "(.*?)")?, from (.+?):(\d+)(?:, asked of (.+?) as "(.*?)")?(?:, part (\d+) "(.*?)")?$'
)


def accepted(key: dict, prop: dict) -> bool:
    m = CLAIM.match(prop["claim"])
    if not m:
        return False
    q, where = m.group(1), m.group(4)
    for a in key["answers"].get(q, []):
        f = a["file"]
        if (where == f or (f.endswith("/") and where.startswith(f))) and a.get("says", "") in prop["data"]:  # fmt: skip
            return True
    return False


def cmd_decide(table: Path) -> int:
    who = who_of(table)
    keyfile = HERE / f"{who}.json"
    if not keyfile.is_file():
        return fail(
            f"{who} has no answer key beside this ({keyfile.name}): only they can decide"
        )
    key = json.loads(keyfile.read_text(encoding="utf-8"))
    now = today_of(who)
    sealed = declined = 0
    for box in boxes_of(table):  # every pile's box, one key
        for subj, prop in waiting(box):
            verb = "seal" if accepted(key, prop) else "decline"
            got = py(ROOT / "kernel.py", verb, "--box", box, "--now", now, subj)
            if got.returncode not in (0, 42):
                return fail(f"{verb} {subj}: {got.stderr.strip()}")
            sealed, declined = (
                (sealed + 1, declined) if verb == "seal" else (sealed, declined + 1)
            )
    print(
        f"{who} sealed {sealed} answers and declined {declined}, with the key made for them."
    )
    return kernel.ALIVE


def cmd_recap(table: Path) -> int:
    who = who_of(table)
    piles = piles_of(table)
    names = {table / "records" / p["slug"]: p["name"] for p in piles}
    by_q: dict[int, dict] = {}
    for box in boxes_of(table):
        rows, _ = kernel.read(box / "record.jsonl")
        verdict = {r["subject"]: r["kind"] for r in rows if r["kind"] in ("seal", "decline")}  # fmt: skip
        for r in rows:
            if r["kind"] == "proposal" and r.get("verdict") == "pass":
                prop = json.loads((box / "proposals" / f"{r['subject'][9:]}.json").read_text(encoding="utf-8"))  # fmt: skip
                m = CLAIM.match(prop["claim"])
                if m:
                    q = by_q.setdefault(int(m.group(1)), {"q": m.group(2), "read": m.group(3) or "", "of": {}, "parts": {}, "seal": [], "decline": [], "wait": []})  # fmt: skip
                    if m.group(6):
                        q["of"][m.group(6)] = m.group(7)  # sent to this pile by name
                    if m.group(8):
                        q["parts"][int(m.group(8))] = m.group(
                            9
                        )  # asked in parts: this is one
                    tag = f"   [{names[box]}]" if piles else ""  # the pile it came from
                    k = int(re.search(r"-(\d+)\.txt$", prop["path"]).group(1))  # its turn in the deal  # fmt: skip
                    q[verdict.get(r["subject"], "wait")].append(((int(m.group(8) or 0), k), f"{m.group(4)}:{m.group(5)}{tag}"))  # fmt: skip
    for g in by_q.values():
        for v in ("seal", "decline", "wait"):
            g[v] = [w for _, w in sorted(g[v], key=lambda x: x[0])]
    asked = questions(who)
    routed = json.loads((table / "route.json").read_text(encoding="utf-8")) if (table / "route.json").is_file() else {}  # fmt: skip
    print(f"# What {who} made true\n")
    for i, q in enumerate(asked, 1):
        got = by_q.get(i)
        see = sent_to(routed.get(str(i), {}))
        if got is None:
            print(f"{i:>2}. {q}\n      nothing in the life holds it\n{see}", end="")
            continue
        line = f"{i:>2}. {q}\n" + (
            f'      asked as "{got["read"]}"\n' if got["read"] else ""
        )
        line += "".join(
            f'      part {k} "{v}"\n' for k, v in sorted(got["parts"].items())
        )
        line += "".join(f'      asked of {k} as "{v}"\n' for k, v in got["of"].items())
        line += "".join(f"      sealed    {w}\n" for w in got["seal"])
        line += "".join(f"      declined  {w}\n" for w in got["decline"])
        line += "".join(f"      waiting   {w}\n" for w in got["wait"])
        print(line + see, end="")
    answered = sum(1 for g in by_q.values() if g["seal"])
    print(f"\n{answered} of {len(asked)} questions have an answer {who} sealed.")
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--read", "--piles"):
            opts[a] = "yes"
        elif a in ("--who", "--table", "--dates"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    verb = args[0] if len(args) == 1 else ""
    if verb not in ("open", "week", "words", "ask", "decide", "recap") or not opts.get("--table") or (verb == "open") != bool(opts.get("--who")):  # fmt: skip
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    table = Path(opts["--table"])
    if verb == "open":
        return cmd_open(
            opts["--who"],
            table,
            opts.get("--dates", ""),
            "--read" in opts,
            "--piles" in opts,
        )
    if not (table / "who.txt").is_file():
        return fail(f"{table} isn't a life box laid by open")
    return {
        "week": cmd_week,
        "words": cmd_words,
        "ask": cmd_ask,
        "decide": cmd_decide,
        "recap": cmd_recap,
    }[verb](table)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
