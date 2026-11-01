"""sent-log: which passages were handed to which model, and where, from the record.

    python adapters/stdlib/sent-log/sent_log.py --box DIR

The record holds no model identity. A `proposal` row is the kernel's own
(`who` is "kernel", never the model's), and holds only the subject, the
verdict and the bite it answered. The one place a model is named is the
proposal's `claim`, in the proposal file, which the subject hashes: for
`openai-compatible` it reads "MODEL at URL answered from N of the M passages
served". So for each proposal that passed this reads the file (only if it is
the bytes the subject names), takes the model and endpoint from that claim,
and lists the passages its bite served, from the bite row. A claim that does
not say so is shown as unnamed, never guessed.

    row 4  2026-10-23T00:00:00Z  proposal:eb63d0addbe2…
           gemma-3-4b-it at http://127.0.0.1:8080/v1 (this machine)
           went: garden.md:1 63d9b600aca4

What this cannot tell, and says: the claim is the proposer's own words, not
an attested card; a person's own suggestion looks the same as a model's; an
ask whose reply cited nothing, or whose endpoint failed, leaves a bite and no
proposal, though the passages may already have left. So the list is a floor.

Exit codes, the kernel's: 0 every proposal names its model and endpoint (or
there are none); 42 one does not, or its file is missing or not what was
proposed; 2 refused (a bad command line, a record that doesn't verify).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

CLAIM = re.compile(r"(.+) at (\S+) answered from (\d+) of the (\d+) passages served")
LOCAL = ("localhost", "::1")


def where_to(url: str) -> str:
    """ "this machine" for a loopback address, else "online" with the host."""
    try:
        host = urlsplit(url).hostname or ""
    except ValueError:
        return "unreadable address"
    if host in LOCAL or host.startswith("127."):
        return "this machine"
    return f"online: {host}" if host else "unreadable address"


def proposal_file(box: Path, subj: str) -> tuple[dict | None, str | None]:
    """(the proposal, None), or (None, why it can't be read as proposed)."""
    path = box / "proposals" / f"{subj[9:]}.json"
    try:
        prop = json.loads(path.read_text(encoding="utf-8"))
        if kernel.subject_of(prop) != subj:
            return None, "its proposal file is not the bytes proposed"
    except OSError:
        return None, "its proposal file is missing"
    except (ValueError, KeyError, TypeError):
        return None, "its proposal file is not the bytes proposed"
    return prop, None


def check(box: Path) -> tuple[int, list[dict]]:
    """(exit code, one entry per passed proposal, then the closing counts)."""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return kernel.REFUSED, [{"refused": b} for b in breaks]
    out, answered = [], set()
    for r in rows:
        if r["kind"] != "proposal" or r.get("verdict") != "pass":
            continue
        bite = rows[r["bite_row"]] if isinstance(r.get("bite_row"), int) else {}
        answered.add(r.get("bite_row"))
        passages = [
            {"id": s["id"], "where": s["where"]}
            for s in bite.get("served", [])
            if not s.get("echo")
        ]
        e = {
            "row": r["n"],
            "ts": r["ts"],
            "subject": r["subject"],
            "passages": passages,
        }
        prop, why = proposal_file(box, r["subject"])
        m = CLAIM.fullmatch(prop["claim"]) if prop else None
        if why:
            e["broken"] = why
        elif m is None:
            e["unnamed"] = prop["claim"]
        else:
            e["model"], e["url"] = m.group(1), m.group(2)
            e["to"] = where_to(m.group(2))
            e["counted"] = int(m.group(4)) == len(passages)
        out.append(e)
    silent = sum(
        r["kind"] == "bite"
        and r["n"] not in answered
        and any(not s.get("echo") for s in r.get("served", []))
        for r in rows
    )
    refused = sum(
        r["kind"] == "proposal" and r.get("verdict") == "refused" for r in rows
    )
    out.append({"silent": silent, "refused": refused})
    bad = any(e.get("broken") or "unnamed" in e for e in out[:-1])
    return (kernel.ESCALATE if bad else kernel.ALIVE), out


def show(e: dict) -> None:
    head = f"row {e['row']}  {e['ts']}  {e['subject'][:21]}…"
    if "broken" in e:
        print(f"{head}\n       broken: {e['broken']}; no model can be read from it")
        return
    if "unnamed" in e:
        print(f"{head}\n       model not named; its claim says {e['unnamed'][:80]!r}")
        return
    print(f"{head}\n       {e['model']} at {e['url']} ({e['to']})")
    note = (
        "went"
        if e["counted"]
        else "served, may have gone (the claim counts another number)"
    )
    places = " ".join(f"{p['where']} {p['id'][:12]}" for p in e["passages"])
    print(f"       {note}: {places or 'none'}")


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "--box":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    code, entries = check(box)
    if code == kernel.REFUSED:
        for e in entries:
            print(f"refused: {e['refused']}", file=sys.stderr)
        return code
    *sends, tail = entries
    for e in sends:
        show(e)
    print(
        f"{len(sends)} proposal(s) on the record; {tail['silent']} bite(s) served"
        f" passages and were proposed on by no one, which this cannot see past;"
        f" {tail['refused']} refused proposal(s) name nothing"
    )
    if not sends:
        print("nothing on the record says a passage went to a model; that is a floor")
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
