"""story_ideas.py: story ideas between sessions, dealt from a game box's own words. Python 3.9+.

    python adapters/stdlib/story-ideas/story_ideas.py --box DIR --worlds DIR --pile DIR [--seed TEXT] [--count N]

For the game master's eyes, between sessions. Nothing here is canon and
nothing is handed in: an idea the GM likes, they write in their binder or
into a story. DIR for --box is the game's record, --worlds the folder of
game-master worlds it plays, --pile the binder the box reads, laid out as
willow's game box lays one: `people/` and `monsters/` (a page each, its
first heading the name), `sessions/` and `scanned/` (the notes of each night,
typed or scanned).

Four parts, all from the box itself:

- **Seeds.** A grammar built from the box's own words: the characters and
  places of the story last played (every world, when none has been), the
  monsters and people of the binder, the threads promised for next time, and
  what the table made true (each fact the GM sealed in game-master). The
  oracle-text add-on deals readings from it with the seeded stream, so a seed
  (the day, unless given) and a number always deal the same ideas again.
- **Set up, never played.** A monster or person with a page in the binder
  whose name no session's notes, typed or scanned, have said yet.
- **Still open.** Every line of the binder that says "next time".
- **Something you wrote and forgot.** One passage drawn by the
  random-passage add-on, replayable from its seed (its `surprise` row on the
  record is the one thing this writes, through it).

Exit codes, the kernel's: 0 done; 2 refused.
"""

from __future__ import annotations

import datetime
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STDLIB = HERE.parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(STDLIB / "game-master"))
import game_master as gm  # noqa: E402
import kernel  # noqa: E402

ORACLE = STDLIB / "oracle-text" / "oracle_text.py"
SURPRISE = STDLIB / "random-passage" / "random_passage.py"
NOTES = ("sessions", "scanned")
CAST = ("monsters", "people")
USAGE = __doc__.split("\n\n")[1]


def fail(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def titled(folder: Path) -> list[str]:
    """Each page's first heading: the name it was written under."""
    out = []
    for p in sorted(folder.glob("*.md")):
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        head = next((ln[2:].strip() for ln in lines if ln.startswith("# ")), "")
        if head:
            out.append(head)
    return out


def said_in_notes(pile: Path) -> str:
    """Every word the session notes, typed and scanned, have said, lower case."""
    text = []
    for name in NOTES:
        folder = pile / name
        for p in sorted(folder.glob("*")) if folder.is_dir() else []:
            if p.is_file():
                text.append(p.read_text(encoding="utf-8", errors="replace").lower())
    return "\n".join(text)


def unplayed(pile: Path) -> list[str]:
    """The binder's monsters and people no session's notes have named yet."""
    said = said_in_notes(pile)
    out = []
    for folder in CAST:
        for name in titled(pile / folder):
            words = [w for w in re.findall(r"[a-z']+", name.lower()) if w not in ("the", "a", "an")]  # fmt: skip
            if words and not all(re.search(rf"\b{re.escape(w)}\b", said) for w in words):  # fmt: skip
                out.append(f"{name}  ({folder}/)")
    return out


def promised(pile: Path) -> list[tuple[str, int, str]]:
    """Every line of the binder that says next time, oldest file first."""
    out = []
    for p in sorted(pile.rglob("*")):
        if p.is_file() and p.suffix in (".md", ".txt"):
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            for i, text in enumerate(lines, 1):
                if "next time" in text.lower():
                    out.append((p.relative_to(pile).as_posix(), i, text.strip()))
    return out


def sealed_facts(box: Path, rows: list[dict]) -> list[str]:
    """Each fact the GM sealed in game-master, asked or offered, in row order."""
    out = []
    for g in gm.games(rows):
        for a in [*g["asks"], *g["offers"]]:
            what, got = gm.ruling(box, rows, a["subject"])
            if what == "sealed":
                out.append((got["n"], a["fact"]))
    return [fact for _, fact in sorted(out)]


def lower_first(text: str) -> str:
    """A capital lowered where a word begins a sentence, never an acronym's."""
    return text[:1].lower() + text[1:] if text[:1].isupper() and not text[1:2].isupper() else text  # fmt: skip


def mid_sentence(name: str) -> str:
    """A name said mid-sentence: only a leading The is lowered."""
    return "the " + name[4:] if name.startswith("The ") else name


def story(worlds: Path, rows: list[dict]) -> list[dict]:
    """The story last played on this record, the one ideas are for: its
    world, or every world in the folder when none has been played yet."""
    by_id = {}
    for f in sorted(worlds.glob("*.json")):
        try:
            w = gm.load_world(f)
        except gm.WorldError:
            continue
        by_id[w["id"]] = w
    played = [g["open"].get("world") for g in gm.games(rows) if g["beats"] or g["offers"]]  # fmt: skip
    return [by_id[played[-1]]] if played and played[-1] in by_id else list(by_id.values())  # fmt: skip


def grammar(box: Path, worlds: Path, pile: Path, rows: list[dict]) -> dict:
    """A Tracery grammar of the box's own words."""
    who, npc, places = [], [], []
    for w in story(worlds, rows):
        for c in w["characters"]:
            (who if c["seat"] else npc).append(c["name"])
        places += [p["name"] for p in w["places"]]
    npc += [n for n in titled(pile / "people") if n not in npc]
    npc = [mid_sentence(n) for n in npc]
    monsters = [f"the {n.lower()}" for n in titled(pile / "monsters")]
    threads = []
    for _, _, line in promised(pile):
        m = re.search(r"next time:?\s*(.+)", line, re.IGNORECASE)
        if m and len(m.group(1).split()) > 2:
            threads.append(m.group(1).rstrip(".!?"))
    canon = [lower_first(f.split("  [offered by")[0].split(":")[0].rstrip(".")) for f in sealed_facts(box, rows)]  # fmt: skip
    g = {
        "who": sorted(set(who)),
        "npc": sorted(set(npc)),
        "place": sorted({mid_sentence(p) for p in places}),
        "monster": monsters,
        "thread": threads,
        "canon": canon,
    }
    g = {k: v for k, v in g.items() if v}
    origin = []
    if {"who", "thread"} <= g.keys():
        origin.append("What if #who# finds out #thread#, and doesn't tell the others?")
    if {"monster", "place", "who"} <= g.keys():
        origin.append("At #place#, #who# comes face to face with #monster#.")
    if {"npc", "who", "thread"} <= g.keys():
        origin.append("#npc.capitalize# asks #who# for help with #thread#.")
    if {"canon", "npc"} <= g.keys():
        origin.append("Because #canon#, #npc# owes someone at the table a favour.")
    if {"canon", "monster"} <= g.keys():
        origin.append("Now that #canon#, #monster# has nowhere to go.")
    if {"who", "npc"} <= g.keys():
        origin.append("#who.capitalize# and #npc# want the same thing, for different reasons.")  # fmt: skip
    g["origin"] = origin
    return g


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--worlds", "--pile", "--seed", "--count"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if args or not all(opts.get(k) for k in ("--box", "--worlds", "--pile")):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    box, worlds, pile = Path(opts["--box"]), Path(opts["--worlds"]), Path(opts["--pile"])  # fmt: skip
    if not (box / "kernel.json").is_file():
        return fail(f"{box} isn't a box: make one with kernel.py init")
    for name, folder in (("--worlds", worlds), ("--pile", pile)):
        if not folder.is_dir():
            return fail(f"{name} {folder} isn't a folder")
    try:
        count = int(opts.get("--count", "5"))
    except ValueError:
        return fail("--count is a whole number")
    if count < 1:
        return fail("--count is at least 1")
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return fail("the record doesn't verify: " + "; ".join(breaks))
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    seed = opts.get("--seed") or f"ideas {today}"
    g = grammar(box, worlds, pile, rows)
    print("# Ideas, for the GM's eyes\n")
    if g["origin"]:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "grammar.json"
            f.write_text(json.dumps(g), encoding="utf-8")
            got = subprocess.run([sys.executable, str(ORACLE), "--seed", seed, "--grammar", str(f), "--count", str(count)],
                                 capture_output=True, text=True, check=False)  # fmt: skip
        if got.returncode != kernel.ALIVE:
            return fail(f"oracle-text: {got.stderr.strip()}")
        print(f"## Seeds (seed {seed!r}: the same seed deals them again)\n")
        print("\n".join(f"  - {ln}" for ln in got.stdout.splitlines() if ln.strip()))
    else:
        print("## Seeds\n\n  The box has too little in it yet to deal from.")
    gone = unplayed(pile)
    print("\n## Set up, never played\n")
    print("\n".join(f"  - {x}" for x in gone) or "  Everything the binder sets up has come out at the table.")  # fmt: skip
    promises = promised(pile)
    print("\n## Still open\n")
    print("\n".join(f"  {p}:{i}  {t}" for p, i, t in promises) or "  No promises made for next time.")  # fmt: skip
    got = subprocess.run([sys.executable, str(SURPRISE), "--box", str(box)], capture_output=True, text=True, check=False)  # fmt: skip
    print("\n## Something you wrote and forgot\n")
    print("\n".join(f"  {ln}" for ln in got.stdout.rstrip().splitlines()) or "  (nothing long enough to draw)")  # fmt: skip
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
