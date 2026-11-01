"""Small models assembling willow's own add-on cards, a batch at a time.

    python assemble.py URL MODEL OUT.json

Map: each batch of about 20 cards (one section, or a slice of a big one) is
handed to the model, which picks 2 to 4 add-ons more useful together than
apart. Check: a name not on that batch's cards is thrown out, the way an
uncited answer is. Assemble: the surviving picks go back in, and the model
builds one pipeline of 3 to 6 steps for one person's need. Check again:
every step's name was offered, nothing repeats, and what goes online is said.
"""

import json
import os
import tempfile
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = Path(os.environ.get("WORK") or tempfile.gettempdir()) / "small-models"
WORK.mkdir(parents=True, exist_ok=True)
CARDS = json.loads((WORK / "cards.json").read_text(encoding="utf-8"))
BY = {c["name"]: c for c in CARDS}
SIZE = 20


def ask(url, model, system, user, max_tokens=600):
    body = {
        "model": model,
        "temperature": 0,
        "seed": 0,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    req = urllib.request.Request(
        url.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    t = time.time()
    with urllib.request.urlopen(req, timeout=900) as r:
        doc = json.loads(r.read())
    return doc["choices"][0]["message"]["content"], round(time.time() - t, 1)


def parse(text):
    try:
        return json.loads(text)
    except ValueError:
        m = re.search(r"\{.*\}", text, re.S)
        try:
            return json.loads(m.group(0)) if m else None
        except ValueError:
            return None


def card_line(c):
    return f"- {c['name']} (writes {c['writes']}; network {c['network']}): {c['line']}"


def batches():
    out = []
    sections = {}
    for c in CARDS:
        sections.setdefault(c["section"], []).append(c)
    for sec, cs in sections.items():
        for i in range(0, len(cs), SIZE):
            out.append((sec, cs[i : i + SIZE]))
    return out


SYSTEM = (
    "You design with willow, a tool that answers questions from a person's own"
    " files and keeps a tamper-evident record. Its add-ons are described by cards."
    " Use only add-on names that appear on the cards you are given, spelled"
    " exactly. Reply with JSON only."
)

MAP = (
    "Cards:\n{cards}\n\nPick 2 to 4 of these add-ons that would be more useful"
    " together than apart, for a real person. Reply as JSON:"
    ' {{"names": ["exact-name", ...], "why": "one sentence"}}'
)

ASSEMBLE = (
    "These groups of add-ons were each picked as working well together:\n"
    "{groups}\n\nThe add-ons on offer, with their cards:\n{cards}\n\n"
    "Assemble ONE pipeline of 3 to 6 steps, using only add-ons on offer, that"
    " does something worthwhile for one specific kind of person. Order the steps"
    " so each one's output feeds the next where it can. Reply as JSON:"
    ' {{"for": "who it is for", "goal": "what they get, one sentence",'
    ' "steps": [{{"name": "exact-name", "does": "what it does here"}}, ...]}}'
)


def main(url, model, out):
    log = {"model": model, "url": url, "map": [], "assemble": None}
    picks = []
    cache_path = Path(out).with_suffix(".cache.json")
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    for i, (sec, cs) in enumerate(batches()):
        offered = {c["name"] for c in cs}
        if str(i) in cache:
            text, secs = cache[str(i)]
        else:
            text, secs = ask(
                url, model, SYSTEM, MAP.format(cards="\n".join(map(card_line, cs)))
            )
            cache[str(i)] = [text, secs]
            cache_path.write_text(json.dumps(cache, ensure_ascii=False))
        doc = parse(text) or {}
        names = doc.get("names") if isinstance(doc.get("names"), list) else []
        kept = [n for n in dict.fromkeys(names) if n in offered]
        invented = [n for n in names if n not in offered]
        ok = len(kept) >= 2
        log["map"].append(
            {
                "section": sec,
                "cards": len(cs),
                "seconds": secs,
                "raw": text,
                "kept": kept,
                "invented": invented,
                "why": doc.get("why"),
                "ok": ok,
            }
        )
        print(
            f"[map] {sec[:26]:26} {secs:6}s kept {kept} invented {invented}", flush=True
        )
        if ok:
            picks.append({"names": kept, "why": doc.get("why", "")})
    offered = sorted({n for p in picks for n in p["names"]})
    groups = "\n".join(f"- {', '.join(p['names'])}: {p['why']}" for p in picks)
    cards = "\n".join(card_line(BY[n]) for n in offered)
    text, secs = ask(
        url, model, SYSTEM, ASSEMBLE.format(groups=groups, cards=cards), 900
    )
    doc = parse(text) or {}
    steps = doc.get("steps") if isinstance(doc.get("steps"), list) else []
    names = [s.get("name") for s in steps if isinstance(s, dict)]
    check = {
        "steps": len(names),
        "not_offered": [n for n in names if n not in offered],
        "repeats": sorted({n for n in names if names.count(n) > 1}),
        "online": [
            n for n in names if n in BY and BY[n]["network"] not in ("none", "loopback")
        ],
        "writes": {n: BY[n]["writes"] for n in names if n in BY},
    }
    check["ok"] = (
        3 <= len(names) <= 6 and not check["not_offered"] and not check["repeats"]
    )
    log["assemble"] = {
        "seconds": secs,
        "raw": text,
        "plan": doc,
        "check": check,
        "offered": offered,
    }
    print(f"[assemble] {secs}s for: {doc.get('for')}\n  goal: {doc.get('goal')}")
    for s in steps:
        print(f"  - {s.get('name')}: {s.get('does')}")
    print(f"  check: {json.dumps(check)}")
    Path(out).write_text(json.dumps(log, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:4])
