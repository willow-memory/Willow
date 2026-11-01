"""A cited "this week" note for one demo person, from add-on output, by a small model.

    python weeknote.py URL MODEL PERSON NOW OUT.json

1. Run: the add-ons' output on the person's files, as of NOW, every line numbered.
2. Keep: the model reads ~40 numbered lines at a time and keeps the numbers that
   matter this week. A number not in that chunk is dropped.
3. Write: from the kept lines alone, the model writes the note, every point
   citing [n]. A point citing nothing, or a number not kept, is struck.
"""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from assemble import ask, parse  # noqa: E402

sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

STEPS = [
    ("coming-up", True),
    ("renewals", True),
    ("car", True),
    ("subscriptions", False),
    ("amounts", False),
    ("todo", False),
]
CHUNK = 40
SYSTEM = (
    "You help a person see what needs their attention, from lines found in their"
    " own files. Use only the numbered lines given. Reply with JSON only."
)
KEEP = (
    "Today is {today}. These numbered lines come from {who}'s own files:\n\n{lines}\n\n"
    "Which of these lines show something {who} needs to act on or know about in the"
    " next two weeks: a payment owed to them or by them, a deadline, a lapse, a"
    " promise? Skip routine, settled or old things. Keep at most 5, the most urgent. Reply as JSON:"
    ' {{"keep": [line numbers]}}'
)
WRITE = (
    "Today is {today}. Write {who} a short note: what needs attention this week, most"
    " urgent first, 3 to 6 points. Use only these numbered lines from her own files,"
    " and end every point with the numbers it rests on, like [12] or [3, 40]. If"
    " lines together show something (an invoice sent with no payment after it), say"
    " so, citing both.\n\n{lines}\n\nReply as JSON:"
    ' {{"points": ["... [n]", ...]}}'
)


def run_steps(person, now):
    lines = []
    with tempfile.TemporaryDirectory() as tmp:
        box = Path(tmp) / "box"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "kernel.py"),
                "init",
                "--box",
                str(box),
                "--pile",
                str(ROOT / "demo" / person / "life"),
                "--key",
                str(Path(tmp) / "key"),
                "--now",
                now,
            ],
            capture_output=True,
            check=True,
        )
        for name, dated in STEPS:
            script = next(
                p
                for p in (ROOT / "adapters/stdlib" / name).glob("*.py")
                if not p.name.startswith("test_")
            )
            cmd = [sys.executable, str(script), "--box", str(box)] + (
                ["--now", now] if dated else []
            )
            out = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT).stdout
            for ln in out.splitlines():
                ln = " ".join(ln.split())
                if ln:
                    lines.append(f"{name}: {ln}"[:240])
    return lines


def main(url, model, person, now, outp):
    who = {"teodora": "Teo"}.get(person, person)
    today = now[:10]
    lines = run_steps(person, now)
    print(f"[run] {len(lines)} lines from {len(STEPS)} add-ons", flush=True)
    kept, invented = [], []
    for i in range(0, len(lines), CHUNK):
        chunk = {n: lines[n - 1] for n in range(i + 1, min(i + CHUNK, len(lines)) + 1)}
        body = "\n".join(f"[{n}] {t}" for n, t in chunk.items())
        text, secs = ask(
            url, model, SYSTEM, KEEP.format(today=today, who=who, lines=body), 300
        )
        got = (parse(text) or {}).get("keep") or []
        nums = [int(x) for x in got if str(x).isdigit()]
        kept += [n for n in [n for n in nums if n in chunk][:5] if n not in kept]
        invented += [n for n in nums if n not in chunk]
        print(
            f"[keep] lines {i + 1}-{i + len(chunk)}: {secs}s kept {[n for n in nums if n in chunk]}"
            f"{' dropped ' + str([n for n in nums if n not in chunk]) if any(n not in chunk for n in nums) else ''}",
            flush=True,
        )
    body = "\n".join(f"[{n}] {lines[n - 1]}" for n in kept)
    text, secs = ask(
        url, model, SYSTEM, WRITE.format(today=today, who=who, lines=body), 900
    )
    points = [
        p for p in ((parse(text) or {}).get("points") or []) if isinstance(p, str)
    ]
    note, struck = [], []
    for p in points:
        cites = [
            int(x)
            for m in re.findall(r"\[([\d,\s]+)\]", p)
            for x in re.split(r"[,\s]+", m)
            if x
        ]
        want = set(kernel.words(re.sub(r"\[[\d,\s]+\]", "", p))) - kernel.FUNCTION
        have = set(kernel.words(" ".join(lines[c - 1] for c in cites if c in kept)))
        holds = len(want & have)
        if cites and not want:
            struck.append({"point": p, "why": "says nothing but its citation"})
        elif cites and all(c in kept for c in cites) and holds < len(want) / 2:
            struck.append(
                {"point": p, "why": f"its lines hold {holds} of its {len(want)} words"}
            )
        elif cites and all(c in kept for c in cites):
            note.append({"point": p, "cites": {c: lines[c - 1] for c in cites}})
        else:
            struck.append(
                {
                    "point": p,
                    "why": "cites nothing"
                    if not cites
                    else f"cites {[c for c in cites if c not in kept]}, not kept",
                }
            )
    print(f"[write] {secs}s: {len(note)} points kept, {len(struck)} struck\n")
    for n in note:
        print("•", n["point"])
        for c, t in n["cites"].items():
            print(f"     [{c}] {t[:150]}")
    for s in struck:
        print("✗ struck:", s["point"], "—", s["why"])
    Path(outp).write_text(
        json.dumps(
            {
                "model": model,
                "person": person,
                "now": now,
                "lines": lines,
                "kept": kept,
                "invented": invented,
                "raw": text,
                "note": note,
                "struck": struck,
            },
            indent=1,
            ensure_ascii=False,
        )
        + "\n"
    )


if __name__ == "__main__":
    main(*sys.argv[1:6])
