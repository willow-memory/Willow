"""rules.py: a game's or a house's rules, sealed section by section, so the rule
asked for answers with the exact section. Python 3.9+.

    python adapters/stdlib/rules/rules.py propose --box DIR [--now TS] FILE
    python adapters/stdlib/rules/rules.py ask     --box DIR [--now TS] NAME...
    python adapters/stdlib/rules/rules.py list    --box DIR

FILE is a markdown file in your folder (a path under it). Each heading starts
a section, named by the heading, running to the next heading. `propose` asks
the kernel "rule NAME" for each section and proposes the section's text,
word for word, as the answer, citing the section's own passages the bite
served. Each waits for your seal, made with `kernel.py seal` and your key.

Once sealed, the kernel itself answers: `kernel.py bite --box DIR "rule NAME"`
gives the section back verbatim, and so does `ask`. Two
sections with one name, an empty one, or one too long to read on a card are
skipped and said. A name already sealed with other words is said, not
proposed again: the kernel answers with the sealed one until you decline it.

`list` says each rules section proposed: `sealed`, `waiting` on your seal,
`changed` (sealed, but your folder's words for it differ now or are gone;
the kernel still answers with what you sealed), or `outdated` (waiting, but
no longer what your folder says). It writes nothing.

Exit codes, the kernel's: `propose` 0 when every section is sealed, 42 when
one waits on your seal; `ask` 0 with the sealed section, 42 when no section of
that name is sealed; `list` 0, or 42 when one waits or has changed; 2 refused.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

ASK = "rule {}"
MAX_BODY = 20000  # a section a person can read on a card
_HEADING = re.compile(r"#{1,6}[ \t]+(.+?)[ \t]*#*[ \t]*")


def sections(text: str) -> tuple[list[dict], dict[str, str]]:
    """([{name, start, end, body}], {name: why skipped}). A section runs from
    its heading's line to the line before the next heading; its body is the
    lines after the heading, outer blank lines dropped, otherwise as written.
    Lines count from 1."""
    lines = text.splitlines()
    heads = [(i, m.group(1)) for i, ln in enumerate(lines)
             if (m := _HEADING.fullmatch(ln))]  # fmt: skip
    found = []
    for j, (i, name) in enumerate(heads):
        end = heads[j + 1][0] if j + 1 < len(heads) else len(lines)
        body = "\n".join(lines[i + 1 : end]).strip("\n")
        found.append({"name": name, "start": i + 1, "end": end, "body": body})
    keys = [kernel.bite_key(ASK.format(s["name"])) for s in found]
    skipped: dict[str, str] = {}
    for s, k in zip(found, keys):
        if keys.count(k) > 1:
            skipped[s["name"]] = "another section has the same name"
        elif not s["body"].strip():
            skipped[s["name"]] = "the section is empty"
        elif len(s["body"]) > MAX_BODY:
            skipped[s["name"]] = f"the section is over {MAX_BODY} characters"
    return [s for s in found if s["name"] not in skipped], skipped


def slug(name: str, n: int) -> str:
    return "-".join(kernel.words(name)) or str(n)


def proposals(box: Path, rows: list[dict]) -> list[dict]:
    """Every passing rules proposal: {subject, row, path, data, bite_key,
    sealed}, its file read while it still hashes to its subject."""
    good = kernel.sealed(box, rows)
    out = []
    for r in rows:
        if r["kind"] != "proposal" or r.get("verdict") != "pass":
            continue
        subj = r["subject"]
        try:
            prop = json.loads((box / "proposals" / f"{subj[9:]}.json").read_text())
        except (OSError, ValueError):
            continue
        if not isinstance(prop, dict) or not str(prop.get("path", "")).startswith(
            "rules/"
        ):
            continue
        if kernel.subject_of(prop) != subj:
            continue
        held = subj in good and kernel.standing(box, rows, subj, good[subj])[2] is None
        out.append({"subject": subj, "row": r["n"], "path": prop["path"],
                    "data": prop["data"], "claim": prop["claim"],
                    "bite_key": prop.get("bite_key"), "sealed": held})  # fmt: skip
    return out


def quiet(fn, *args) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = fn(*args)
    return code, out.getvalue()


def refuse(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


# ── the verbs ───────────────────────────────────────────────────────────────
def propose(box: Path, rows: list[dict], rel: str, ts: str) -> int:
    pile = Path(kernel.config(box)["pile"]).resolve()
    f = (pile / rel).resolve()
    if not f.is_relative_to(pile) or not f.is_file():
        return refuse(f"{rel} is not a file in your folder")
    try:
        text = f.read_text(encoding="utf-8")
    except (OSError, ValueError) as e:
        return refuse(f"{rel} can't be read as text: {type(e).__name__}")
    where = f.relative_to(pile).as_posix()
    found, skipped = sections(text)
    for name, why in skipped.items():
        print(f"skipped  {name}: {why}")
    if not found:
        print(f"no section of {where} to propose")
        return kernel.ESCALATE
    code = kernel.ALIVE
    for n, s in enumerate(found, 1):
        key = kernel.bite_key(ASK.format(s["name"]))
        mine = [p for p in proposals(box, kernel.read(box / "record.jsonl")[0])
                if p["bite_key"] == key]  # fmt: skip
        held = next((p for p in mine if p["sealed"]), None)
        if held and held["data"] == s["body"]:
            print(f"sealed   {s['name']}")
            continue
        if held:
            print(f"differs  {s['name']}: another text is sealed for it (row "
                  f"{held['row']}); the kernel answers with that one")  # fmt: skip
            continue
        same = next((p for p in mine if p["data"] == s["body"]), None)
        if same is None:
            got, said = quiet(kernel.bite, box, ASK.format(s["name"]), ts)
            if got == kernel.REFUSED:
                return refuse(f"the kernel wouldn't take the bite: {said.strip()}")
            served = json.loads(said).get("served", [])
            cites = sorted({c["id"] for c in served
                            if c["where"].rsplit(":", 1)[0] == where
                            and s["start"] <= int(c["where"].rsplit(":", 1)[1]) <= s["end"]})  # fmt: skip
            prop = {"path": f"rules/{where}/{slug(s['name'], n)}.md",
                    "data": s["body"], "cites": cites,
                    "claim": f"the rule {s['name']}, as {where} writes it"}  # fmt: skip
            got, said = quiet(kernel.propose, box, [json.dumps(prop)], ts)
            if "pass  proposal:" not in said:
                return refuse(f"the kernel's door: {said.strip()}")
            subj = kernel.subject_of(prop)
        else:
            subj = same["subject"]
        print(f"waiting  {s['name']}: python kernel.py seal --box {box} {subj}")
        code = kernel.ESCALATE
    return code


def ask(box: Path, name: str, ts: str) -> int:
    got, said = quiet(kernel.bite, box, ASK.format(name), ts)
    if got == kernel.REFUSED:
        return refuse(said.strip())
    doc = json.loads(said)
    if doc.get("state") == "sealed":
        print(doc["answer"])
        return kernel.ALIVE
    print(f"no rule named {name} is sealed")
    return kernel.ESCALATE


def in_folder(pile: Path, path: str) -> str | None:
    """The words a proposal's section has in your folder now, or None when
    its file or section is gone. The path is rules/<file>/<slug>.md."""
    rel, _, name = path[len("rules/") :].rpartition("/")
    f = (pile / rel).resolve()
    if not rel:
        return None
    if not f.is_relative_to(pile.resolve()):
        return None
    try:
        found, _ = sections(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return next((s["body"] for n, s in enumerate(found, 1)
                 if f"{slug(s['name'], n)}.md" == name), None)  # fmt: skip


def show(box: Path, rows: list[dict]) -> int:
    mine = proposals(box, rows)
    if not mine:
        print("no rules proposed yet: propose a file of them first")
        return kernel.ESCALATE
    pile = Path(kernel.config(box)["pile"])
    waits = False
    for p in mine:
        state = "sealed" if p["sealed"] else "waiting"
        if in_folder(pile, p["path"]) != p["data"]:
            state = "changed" if p["sealed"] else "outdated"
        waits = waits or state != "sealed"
        print(f"{state:<8} {p['claim']}")
    return kernel.ESCALATE if waits else kernel.ALIVE


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("propose", "ask", "list"):
        return usage()
    verb, opts, words = argv[0], {}, []
    it = iter(argv[1:])
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        elif a.startswith("--"):
            return usage()
        else:
            words.append(a)
    if not opts.get("--box") or any(not v for v in opts.values()):
        return usage()
    if verb == "list" and (words or "--now" in opts):
        return usage()
    if verb == "propose" and len(words) != 1 or verb == "ask" and not words:
        return usage()
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        return refuse("not a kernel box; init first")
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return refuse(f"the record doesn't verify ({breaks[0]}); a person looks first")
    ts = opts.get("--now") or kernel.now()
    if verb == "list":
        return show(box, rows)
    if verb == "ask":
        return ask(box, " ".join(words), ts)
    return propose(box, rows, words[0], ts)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
