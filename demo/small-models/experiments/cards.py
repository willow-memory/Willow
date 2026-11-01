"""cards.py: willow's add-on cards as the experiments read them.

    WORK=DIR python demo/small-models/experiments/cards.py

Writes WORK/small-models/cards.json (each card's header: name, section,
line, writes, network, and its first usage line) and uses.json (each
README's opening paragraph under its title, in its author's own words).
Both come from the repository as it is checked out.
"""

import json
import os
import re
import tempfile
from pathlib import Path

WORK = Path(os.environ.get("WORK") or tempfile.gettempdir()) / "small-models"
WORK.mkdir(parents=True, exist_ok=True)

ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    cards, uses = [], {}
    for p in sorted(ROOT.glob("adapters/*/*/README.md")):
        t = p.read_text(encoding="utf-8")
        m = re.match(r"<!-- willow-addon\n(.*?)-->", t, re.S)
        if not m:
            continue
        h = dict(
            ln.split(": ", 1) for ln in m.group(1).strip().splitlines() if ": " in ln
        )
        code = re.search(r"```\n?(python [^\n]+)", t) or re.search(
            r"\n    (python [^\n]+)", t
        )
        cards.append(
            {
                "name": p.parent.name,
                "kind": p.parent.parent.name,
                "section": h.get("section"),
                "line": h.get("line"),
                "writes": h.get("writes"),
                "network": h.get("network"),
                "usage": code.group(1) if code else None,
            }
        )
        body = re.sub(r"^\s*# .*\n", "", t.split("-->", 1)[1].lstrip(), count=1)
        para = []
        for ln in body.splitlines():
            if not ln.strip() or ln.startswith(("```", "    ", "#", "|", "<")):
                if para:
                    break
                continue
            para.append(ln.strip())
        uses[p.parent.name] = " ".join(para)
    (WORK / "cards.json").write_text(json.dumps(cards, ensure_ascii=False, indent=1))
    (WORK / "uses.json").write_text(json.dumps(uses, ensure_ascii=False, indent=1))
    print(f"wrote {len(cards)} cards to {WORK}")


if __name__ == "__main__":
    main()
