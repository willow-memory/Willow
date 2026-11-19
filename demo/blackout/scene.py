"""scene.py: the steelworks' eight boxes, the SEC stack, and what Audit can see that no one else can.

    python demo/blackout/scene.py run --life DIR --to DIR [--now TS] [--dry] [--box STUDYBOX]

DIR for --life is what make_life.py wrote: one folder per box. Each gets a box,
a seal key and an identity under --to, which must not be there yet; the piles
are copied there first, so the scene can edit a file without touching the repo.

1. Eight boxes, each a separate person's, over their own papers.
2. Compliance runs `fixity` over its own papers (2026-10-20), the first check
   there is, and on 10-26 Ruth edits the quiz key.
3. Legal seals a stack (the SEC check) and sends it to Compliance. Compliance
   receives it and signs it too, by passing it on to each of the other six boxes
   in a layer of its own: it arrives with two signatures, and a layer nobody can
   change without breaking both.
4. Each receiver checks the pin of every add-on the stack runs, seals the stack
   themselves and runs it over their own box. The files it reads never travel.
   The auditor declines it: an auditor runs no one's tools.
5. What the stack found, box by box: `fixity` says the quiz key was edited, with
   no word of why; `first-mention` says the shipments figure first appears in
   Investor Relations' box on 10-27 and in every other box on 11-05, the day of
   the filing; `contradictions` finds nothing anywhere.
6. Each person seals what their own papers say, in their own words, and sends it
   to Audit, which the committee's charter says takes from anyone. Nothing in an
   answer is a legal conclusion, and Compliance does not seal what `fixity` found.
7. Audit sets what it kept side by side (`kept-clash`): the blackout is 14 days in
   the trainee's sealed answers and 7 in Compliance's; the shipments figure is 33
   percent in Investor Relations' and 28 in the filing's that Legal sealed. Neither
   is picked, and no one box could have found either.
8. The join no one box holds: the plan administrator's sales by employee number,
   the steward's seniority list by department. The scene does it, and says so.
9. Audit holds each sender's chain to the packages it kept (`share witness`); every
   chain holds, and each record holds only its owner's seals. The report is due
   before the next filing, and what it says is outside every chain.

`--dry` replaces every question with nonsense over a pile plus one nonsense
passage; `--box STUDYBOX` appends one kernel row a pass rule to a box outside the
repo. It writes a transcript to standard output and scene.json under --to. Exit 0
when the scene plays as told, 1 when a step went otherwise.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402
from kernel import canon, h256  # noqa: E402

KERNEL = ROOT / "kernel.py"
STACK = ROOT / "adapters/stdlib/stack/stack.py"
SHARE = ROOT / "adapters/stdlib/share/share.py"
FIXITY = ROOT / "adapters/stdlib/fixity/fixity.py"
KEPT_CLASH = ROOT / "adapters/stdlib/kept-clash/kept_clash.py"
BOXES = ["trainee", "compliance", "legal", "ir", "floor", "plan", "steward", "audit"]
#: who gets the stack from the two who sign it, and what each does with it
RECEIVERS = ["trainee", "ir", "floor", "plan", "steward", "audit"]
DECLINES = {"audit"}
#: what every question becomes in a dry run
DRY_QUESTION = "qqqq zzzz"

LATER = "2026-10-30T11:00:00Z"  # the clock fixity reads, so the stack says the same thing twice
#: the SEC check: (pool, add-on, its arguments after --box {box})
STACK_STEPS = [
    ("what changed with no edit of yours", "fixity", f"--now {LATER}"),
    ("where the papers disagree", "contradictions", ""),
    (
        "when a figure first appears",
        "first-mention",
        '"shipments largest automotive customer"',
    ),
]
STACK_WORDS = "stack sec check"
STACK_NAME = "sec-check"
STACK_WHY = "what a box's own papers say about themselves, against the rules"

PLAN_IDS = (
    "E-1051 E-1090 E-1063 E-1118 E-1077 E-1147 E-1131 E-2038 E-2059 E-3045 E-0007"
)
#: what each person seals from their own papers: (who, question, the file its cite
#: comes from, the answer, why). Nothing here is a legal conclusion.
ANSWERS = [
    ("trainee", "what did the training sheet say about the blackout",
     "course/yard-training-sheet.txt",
     "The yard training sheet I was read says the blackout begins 14 days before each earnings release.",
     "the sheet read aloud at my shift"),
    ("trainee", "what answer did I give on the quiz about the blackout",
     "course/quiz-attempt-2026-10-20.txt",
     "On 2026-10-20 I passed the quiz, and my answer to the blackout question was 14 days.",
     "my quiz attempt, marked 5 of 5"),
    ("compliance", "when does the blackout begin under the policy",
     "policy/insider-trading-policy.txt",
     "Policy version 3, posted 2026-10-23, begins the blackout 7 days before each earnings release.",
     "section 4.2 of the policy"),
    ("legal", "what did counsel say about the change to the window",
     "memos/2026-10-30-window-question.txt",
     "Counsel's memo of 2026-10-30 says it depends, and asks for the dates of the change and of each trade.",
     "the memo itself"),
    ("legal", "what did the 8-K say shipments to the largest automotive customer did",
     "public/8k-2026-11-05.txt",
     "The Form 8-K says shipments to the largest automotive customer decreased 28 percent from the second quarter.",
     "the filing, Item 2.02, as filed"),
    ("ir", "what shipments figure was given on the call",
     "calls/2026-10-27-larch-street.txt",
     "The call notes record that one analyst was told shipments to the largest automotive customer were down 33 percent from the second quarter.",
     "my own call notes of the Tuesday call"),
    ("floor", "what does the order board show for the automotive customer",
     "board/order-board-export.txt",
     "The order board shows 0 coil orders from the largest automotive customer on each day from 2026-10-19.",
     "the order board export"),
    ("floor", "what was the EAF2 mode and operator ack",
     "historian/eaf2.log",
     "The furnace log records EAF2 mode HOLD at 02:10 on 2026-10-18, with no operator acknowledgement.",
     "the furnace's own log"),
    ("plan", "plan sales employee date shares",
     "trades/plan-sales-2026-q4.txt",
     f"The plan log records 11 sales from 2026-10-22 to 2026-10-28 by employee number: {PLAN_IDS}; the last, E-0007, sold 4000 shares on 2026-10-28.",
     "the administrator's sales log"),
    ("steward", "seniority list melt shop rolling mill",
     "roster/seniority-list.txt",
     "The seniority list puts on the melt shop: E-1042 E-1051 E-1063 E-1077 E-1084 E-1090 E-1102 E-1118 E-1125 E-1131 E-1147 E-1152; "
     "on the rolling mill: E-2011 E-2024 E-2038 E-2046 E-2059 E-2063; in plant services: E-3022 E-3045 E-3109.",
     "the local's seniority list"),
]  # fmt: skip
#: words no sealed answer may hold as its own finding: a legal conclusion is not a record
CONCLUSIONS = ("material", "violat", "illegal", "guilty", "unlawful", "tipping")

#: the pass rules, as frozen: each is a check the scene makes and scores
RULES = {
    "R1": "the SEC stack arrives in six boxes with two signatures and the same pins, five seal it "
    "and run it and flag only what the papers show, and the auditor declines",
    "R2": "no sealed package holds a long line of any pile but its sender's, the public filing "
    "and release aside",
    "R3": "no sealed answer holds a legal conclusion (material, violation, illegal, guilty, "
    "unlawful, tipping) as its own finding",
    "R4": "kept-clash at Audit sets exactly two disagreements side by side, the blackout's 14 "
    "days against 7 and the shipments' 33 percent against 28, each between two senders, picking "
    "neither, where no box's own stack found either",
    "R5": "the join of the plan log's employee numbers to the seniority list puts nine on the melt "
    "shop or rolling mill, one in plant services and one on no list",
    "R6": "fixity says the quiz key was edited, in Compliance's box and no other, and Compliance's "
    "sealed answers do not say so",
    "R7": "Audit's witness holds every sender's chain to the packages it kept, and every seal row "
    "is the person's own, as many as the scene's owners sealed",
}
#: the code a verdict is made with, hashed onto each verdict row
TOOLS = ["kernel.py", "adapters/stdlib/share/share.py", "adapters/stdlib/fixity/fixity.py",
         "adapters/stdlib/stack/stack.py", "adapters/stdlib/contradictions/contradictions.py",
         "adapters/stdlib/first-mention/first_mention.py",
         "adapters/stdlib/kept-clash/kept_clash.py",
         "demo/blackout/scene.py", "demo/blackout/make_life.py"]  # fmt: skip


def script(name: str) -> Path:
    return ROOT / "adapters" / "stdlib" / name / (name.replace("-", "_") + ".py")


def stack_text() -> str:
    """The stack file, each step's add-on pinned by its SHA-256 on a comment
    line, which stack.py skips and a receiver checks."""
    out = ["# the SEC check: " + STACK_WHY]
    for step in sorted({s for _, s, _ in STACK_STEPS}):
        out.append(f"# pin {step} {h256(script(step).read_text(encoding='utf-8'))}")
    for pool, step, args in STACK_STEPS:
        out += ["", f"## {pool}", f"- {step} -- --box {{box}} {args}".rstrip()]
    return "\n".join(out) + "\n"


def pins(text: str) -> dict[str, str]:
    return {w[2]: w[3] for w in (ln.split() for ln in text.splitlines())
            if w[:2] == ["#", "pin"] and len(w) == 4}  # fmt: skip


def innermost(pkg: dict) -> dict:
    """The layer that holds the answers: a forward wraps the package it passed on."""
    while pkg.get("wraps"):
        pkg = pkg["wraps"]
    return pkg


def public_texts() -> list[str]:
    sys.path.insert(0, str(HERE))
    import make_life

    return list(make_life.PUBLIC.values())


class Scene:
    def __init__(self, life: Path, to: Path, now: datetime, dry: bool = False):
        self.life, self.to, self.now, self.dry = life, to, now, dry
        self.pub: dict[str, str] = {}
        self.ids: dict[str, Path] = {}
        self.wrong: list[str] = []
        self.sealed: dict[str, list[str]] = {b: [] for b in BOXES}
        self.said: dict[str, list[dict]] = {b: [] for b in BOXES}
        self.answers: dict[str, list[str]] = {b: [] for b in BOXES}
        self.packages: list[Path] = []
        self.ran: dict[str, dict] = {}
        self.found_: dict = {}
        #: each pass rule's check, set False where a check fails (scored only on a real run)
        self.ok = {f"R{i}": True for i in range(1, 8)}

    def at(self, ts: str) -> None:
        self.now = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )

    def ts(self) -> str:
        self.now += timedelta(minutes=1)
        return self.now.strftime("%Y-%m-%dT%H:%M:%SZ")

    def run(self, *argv, want: tuple[int, ...] = (0,)) -> str:
        got = subprocess.run([sys.executable, *map(str, argv)], capture_output=True,
                             text=True, stdin=subprocess.DEVNULL)  # fmt: skip
        if got.returncode not in want:
            self.wrong.append(f"{Path(str(argv[0])).name} {argv[1]}: exit "
                              f"{got.returncode} {got.stderr.strip()}")  # fmt: skip
        return got.stdout

    def say(self, text: str = "") -> None:
        print(text)

    def box(self, who: str) -> Path:
        return self.to / who / "box"

    def pile(self, who: str) -> Path:
        return self.to / "_pile" / who

    def rows(self, who: str) -> list[dict]:
        text = (self.box(who) / "record.jsonl").read_text()
        return [json.loads(x) for x in text.splitlines()]

    def setup(self) -> None:
        self.to.mkdir()
        shutil.copytree(self.life, self.to / "_pile")
        for who in BOXES:
            if self.dry:
                # every question is nonsense, so each pile gets one passage the nonsense
                # finds (its words out of order, so it is no echo of the question)
                (self.pile(who) / "dry.md").write_text(
                    f"# dry\n\nqqqq is not zzzz, says the {who} pile's one dry passage.\n",
                    encoding="utf-8",
                )
            (self.to / who).mkdir()
            self.run(KERNEL, "init", "--box", self.box(who), "--pile", self.pile(who),
                     "--key", self.to / who / "key", "--now", self.ts())  # fmt: skip
            self.ids[who] = self.to / who / "id"
            self.pub[who] = self.run(SHARE, "id", "--to", self.ids[who]).strip()
            self.say(f"{who:11} box made, identity {self.pub[who][:12]}…")

    def share(self, cmd: str, who: str, *argv: str, want=(0,)) -> str:
        return self.run(SHARE, cmd, "--box", self.box(who), "--id", self.ids[who], *argv,
                        "--now", self.ts(), want=want)  # fmt: skip

    def propose(self, who: str, words: str, prop: dict) -> str:
        """The person's own words, a bite, and a proposal: its subject, or empty."""
        self.run(KERNEL, "bite", "--box", self.box(who), words, "--now", self.ts(),
                 want=(0, 42))  # fmt: skip
        sug = self.to / who / "suggestion.jsonl"
        sug.write_text(json.dumps(prop) + "\n")
        out = self.run(KERNEL, "propose", "--box", self.box(who), "--file", sug,
                       "--now", self.ts(), want=(42,))  # fmt: skip
        sug.unlink()
        return out.split()[1] if out.startswith("pass") else ""

    def keep(self, who: str, text: str, claim: str) -> str:
        """A stack is sealed like an answer that cites nothing: the owner's act,
        played through the kernel's own `seal`."""
        subj = self.propose(who, STACK_WORDS, {"path": f"stacks/{STACK_NAME}.md",
                                               "data": text, "cites": [], "claim": claim})  # fmt: skip
        self.run(KERNEL, "seal", "--box", self.box(who), subj, "--now", self.ts())
        self.sealed[who].append(subj)
        return subj

    def decline(self, who: str, text: str, why: str) -> str:
        subj = self.propose(who, STACK_WORDS, {"path": f"stacks/{STACK_NAME}.md",
                                               "data": text, "cites": [], "claim": why})  # fmt: skip
        return self.run(
            KERNEL, "decline", "--box", self.box(who), subj, "--now", self.ts()
        ).strip()

    def seal(self, who: str, question: str, source: str, data: str, claim: str) -> str:
        """The person asks, writes the answer from what was served, and seals it:
        the person's act, played through the kernel's own `seal`."""
        if self.dry:
            # a repeated question would serve the earlier sealed answer first, so each
            # one carries a different nonsense word the passage need not hold
            question = f"{DRY_QUESTION} {'x' * (4 + len(self.said[who]))}"
            source, data = "dry.md", f"nonsense answer {len(self.said[who])} from {who}"
        bite = json.loads(self.run(KERNEL, "bite", "--box", self.box(who), question,
                                   "--now", self.ts(), want=(0, 42)))  # fmt: skip
        cites = [
            s["id"]
            for s in bite.get("served", [])
            if s["where"].startswith(source + ":")
        ]
        if not cites:
            self.wrong.append(f"{who}: '{question}' served nothing from {source}")
            return ""
        subj = self.propose(who, question, {"path": f"{who}/{cites[0][:8]}.md", "data": data,
                                            "cites": cites[:1], "claim": claim})  # fmt: skip
        self.run(KERNEL, "seal", "--box", self.box(who), subj, "--now", self.ts())
        self.sealed[who].append(subj)
        self.answers[who].append(subj)
        self.said[who].append({"data": data, "claim": claim, "cite": source})
        self.say(f"  {who} sealed: {data[:100]}{'…' if len(data) > 100 else ''}")
        return subj

    def run_stack(self, who: str) -> subprocess.CompletedProcess:
        kept = self.box(who) / "written" / "stacks" / f"{STACK_NAME}.md"
        return subprocess.run([sys.executable, str(STACK), "--box", str(self.box(who)),
                               "--stack", str(kept)], capture_output=True, text=True)  # fmt: skip

    def report(self, who: str, label: str, pkg: str | None) -> dict:
        ran = self.run_stack(who)
        said = [ln for ln in ran.stdout.splitlines() if ln.strip()]
        flagged = [ln.strip() for ln in said if ln.lstrip().startswith(
            ("edited", "rot", "DATE", "AMOUNT"))]  # fmt: skip
        first = next((ln.split(": ")[2].split(" (")[0].split(";")[0] for ln in said
                      if ln.strip().startswith("first-mention: populated")), "")  # fmt: skip
        self.say(f"  {who:10} runs it over {label}: exit {ran.returncode}"
                 + (f", {flagged[0][:70]}" if flagged else ", nothing flagged")
                 + f"; the figure first appears {first or 'nowhere'}")  # fmt: skip
        if ran.returncode not in (0, 42) or not ran.stdout.strip():
            self.wrong.append(f"{who}'s run of the stack printed nothing")
        return {"taken": True, "exit": ran.returncode, "flagged": flagged, "first": first,
                "package": pkg}  # fmt: skip

    # ── the acts ───────────────────────────────────────────────────────────
    def play(self) -> dict:
        self.say("── 1. eight boxes, each over its own papers")
        self.at("2026-10-20T07:00:00Z")
        self.setup()

        self.say("\n── 2. the quiz key, checked once, then edited")
        first = self.run(FIXITY, "--box", self.box("compliance"), "--now", self.ts(),
                         want=(0, 42)).strip()  # fmt: skip
        self.say(
            f"  2026-10-20  compliance's first fixity check: {first.splitlines()[0]}"
        )
        self.at("2026-10-26T09:00:00Z")
        key = self.pile("compliance") / "course" / "quiz-key.txt"
        text = key.read_text(encoding="utf-8")
        edited = text.replace("4. 14 days.", "4. 7 days.")
        if edited == text:
            self.wrong.append("the quiz key had no 14 days to edit")
        key.write_text(edited, encoding="utf-8")
        self.say("  2026-10-26  Ruth edits the quiz key to match the new policy")

        self.say(
            "\n── 3. Legal seals the SEC check; Compliance signs it too and passes it on"
        )
        self.at("2026-10-30T10:00:00Z")
        text = stack_text()
        subj = self.keep("legal", text, STACK_WHY)
        self.say("  legal seals the SEC check stack")
        legal_pkg = self.to / "sec-check-legal-to-compliance.pkg"
        self.share("send", "legal", "--answer", subj, "--for", self.pub["compliance"],
                   "--to", legal_pkg, "--note", "The SEC check, from counsel")  # fmt: skip
        self.packages.append(legal_pkg)
        self.share("receive", "compliance", "--package", legal_pkg)
        self.say("  compliance receives it")
        for who in RECEIVERS:
            pkg = self.to / f"sec-check-compliance-to-{who}.pkg"
            self.share("forward", "compliance", "--package", legal_pkg, "--for",
                       self.pub[who], "--to", pkg, "--note", "Signed by Legal and by me")  # fmt: skip
            self.packages.append(pkg)
        self.say(
            f"  compliance passes it on, in a layer of its own, to {len(RECEIVERS)} boxes"
        )

        self.say(
            "\n── 4. each box checks the pins, takes it or declines it, and runs it"
        )
        self.keep("compliance", text, f"taken from {legal_pkg.name}, every pin checked")
        self.ran["compliance"] = self.report("compliance", "compliance's own box", None)
        for who in RECEIVERS:
            pkg = self.to / f"sec-check-compliance-to-{who}.pkg"
            got = self.share("receive", who, "--package", pkg)
            layers = got.count("└ from ")
            data = innermost(json.loads(pkg.read_text(encoding="utf-8")))["answers"][0][
                "data"
            ]
            same = len(pins(data)) == len({s for _, s, _ in STACK_STEPS}) and all(
                h256(script(s).read_text(encoding="utf-8")) == h
                for s, h in pins(data).items()
            )
            self.say(f"  {who:10} receives it: {layers + 1} signatures, every pin "
                     f"{'the same code here' if same else 'NOT the same code here'}")  # fmt: skip
            if layers != 1 or not same:
                self.wrong.append(f"{who}: {layers + 1} signatures, pins same: {same}")
                self.ok["R1"] = False
            if who in DECLINES:
                said = self.decline(
                    who, data, "offered by two others; an auditor runs no party's tools"
                )
                self.say(f"  {who:10} declines it: {said.split(';')[-1].strip()[:70]}")
                self.ran[who] = {"taken": False}
                continue
            self.keep(who, data, f"taken from {pkg.name}, every pin checked")
            self.ran[who] = self.report(who, who, pkg.name)

        self.say("\n── 5. what the stack found, and what it did not")
        self.stack_found()

        self.say(
            "\n── 6. each person seals what their own papers say, and sends it to Audit"
        )
        self.at("2026-10-31T09:00:00Z")
        for who, q, src, data, claim in ANSWERS:
            self.seal(who, q, src, data, claim)
        senders = [b for b in BOXES if self.answers[b]]
        for who in senders:
            pkg = self.to / f"{who}-to-audit.pkg"
            self.share("send", who, "--answer", ",".join(self.answers[who]), "--for",
                       self.pub["audit"], "--to", pkg, "--note", "Sealed, as the charter takes it")  # fmt: skip
            self.packages.append(pkg)
            self.share("receive", "audit", "--package", pkg)
        self.say(f"  {len(senders)} packages received by audit")
        self.conclusions()

        self.say("\n── 7. Audit sets what it kept side by side")
        self.clash()

        self.say("\n── 8. the join no one box holds")
        self.join()

        self.say("\n── 9. Audit holds each sender's chain to what it kept")
        self.witness()
        self.say("\n  Mavis's report is due before the next filing. What it says is outside "
                 "every chain.")  # fmt: skip

        self.say("\n── 10. every chain, and what crossed")
        self.walls()
        return self.summary()

    def stack_found(self) -> None:
        edited = [ln for ln in self.ran["compliance"]["flagged"] if "quiz-key" in ln]
        self.say(f"  fixity, in compliance's box: {edited[0] if edited else 'nothing'}")
        self.say("  fixity in every other box: nothing flagged")
        self.say(f"  first-mention, in ir's box: the figure first appears "
                 f"{self.ran['ir']['first']}; in every other box, {self.ran['trainee']['first']}")  # fmt: skip
        if not edited:
            self.wrong.append("fixity did not say the quiz key was edited")
            self.ok["R6"] = False
        for who, r in self.ran.items():
            if r.get("taken") and who != "compliance" and r["flagged"]:
                self.wrong.append(
                    f"{who}'s box flagged something it should not: {r['flagged']}"
                )
                self.ok["R1"] = False
        if not self.dry:
            if self.ran["ir"]["first"] != "2026-10-27":
                self.wrong.append(
                    "the figure did not first appear in ir's box on 10-27"
                )
                self.ok["R1"] = False
            for who in ("trainee", "floor", "plan", "steward"):
                if self.ran[who]["first"] != "2026-11-05":
                    self.wrong.append(f"{who}'s box saw the figure before the filing")
                    self.ok["R1"] = False
        self.say("  contradictions found nothing anywhere: it leaves two figures written on\n"
                 "  different days alone, as a plan changed, and picks neither")  # fmt: skip

    def conclusions(self) -> None:
        for who, items in self.said.items():
            for a in items:
                hit = [w for w in CONCLUSIONS if w in a["data"].lower()]
                if hit:
                    self.wrong.append(
                        f"{who}'s sealed answer holds a conclusion: {hit}"
                    )
                    self.ok["R3"] = False
        mentions = [a for a in self.said["compliance"]
                    if "quiz" in a["data"].lower() or "key" in a["data"].lower()]  # fmt: skip
        if mentions:
            self.wrong.append("compliance sealed something about the quiz key")
            self.ok["R6"] = False
        self.say("  no sealed answer holds a legal conclusion, and compliance sealed nothing "
                 "about the quiz key")  # fmt: skip

    def clash(self) -> None:
        pkgs = [self.to / f"{b}-to-audit.pkg" for b in BOXES if self.answers[b]]
        out = self.run(KEPT_CLASH, *pkgs, want=(0, 42))
        names = {self.pub[b][:12]: b for b in BOXES}
        found = []
        lines = out.splitlines()
        for i, ln in enumerate(lines):
            if re.match(r"(AMOUNT|DATE|TIME|WORD)\s", ln):
                pair = [re.search(r"key (\w{12})", x) for x in lines[i + 1 : i + 3]]
                vals = [
                    re.search(r"key \w+…\s+(\S+(?: \S+)?)\s+\(", x)
                    for x in lines[i + 1 : i + 3]
                ]
                found.append(
                    {
                        "kind": ln.split()[0],
                        "senders": [
                            names.get(m.group(1), "?") if m else "?" for m in pair
                        ],
                        "values": [v.group(1) if v else "?" for v in vals],
                    }
                )
        for f in found:
            self.say(f"  {f['kind']:7} {f['senders'][0]}: {f['values'][0]}   vs   "
                     f"{f['senders'][1]}: {f['values'][1]}   (neither side is picked)")  # fmt: skip
        self.found_["clash"] = found
        if self.dry:
            return
        kinds = sorted(tuple(sorted(f["values"])) for f in found)
        wanted = sorted([("14 days", "7 days"), ("28 percent", "33 percent")])
        distinct = all(
            len(set(f["senders"])) == 2 and "?" not in f["senders"] for f in found
        )
        if len(found) != 2 or kinds != wanted or not distinct:
            self.wrong.append(
                f"kept-clash did not set the two disagreements side by side: {found}"
            )
            self.ok["R4"] = False

    def join(self) -> None:
        if self.dry:  # nonsense answers hold no employee numbers to join
            self.found_["join"] = {}
            self.say("  (a dry run joins nothing: its answers are nonsense)")
            return
        # the list before the semicolon: the last clause names E-0007 a second time
        plan = (
            self.said["plan"][0]["data"].split(":", 1)[1].split(";")[0]
            if self.said["plan"]
            else ""
        )
        sold = re.findall(r"E-\d{4}", plan)
        text = self.said["steward"][0]["data"] if self.said["steward"] else ""
        listed: dict[str, str] = {}
        for label, dept in (("melt shop:", "melt shop"), ("rolling mill:", "rolling mill"),
                            ("plant services:", "plant services")):  # fmt: skip
            seg = text.split(label, 1)[1] if label in text else ""
            seg = re.split(r"; on |; in |\.$", seg)[0]
            for e in re.findall(r"E-\d{4}", seg):
                listed[e] = dept
        tally: dict[str, int] = {}
        for e in sold:
            tally[listed.get(e, "on no list")] = (
                tally.get(listed.get(e, "on no list"), 0) + 1
            )
        self.found_["join"] = tally
        self.say(f"  of {len(sold)} plan sales by employee number: "
                 + ", ".join(f"{n} {d}" for d, n in sorted(tally.items())))  # fmt: skip
        self.say("  the scene's own join: no add-on joins two people's sealed answers. It says\n"
                 "  who sold when, and nothing about who knew anything.")  # fmt: skip
        if self.dry:
            return
        melt_roll = tally.get("melt shop", 0) + tally.get("rolling mill", 0)
        got = (
            len(sold),
            melt_roll,
            tally.get("plant services", 0),
            tally.get("on no list", 0),
        )
        if got != (11, 9, 1, 1):
            self.wrong.append(f"the join did not come out as told: {tally}")
            self.ok["R5"] = False

    def witness(self) -> None:
        held = {}
        for who in [b for b in BOXES if self.answers[b]]:
            got = self.run(SHARE, "witness", "--box", self.box(who), "--package",
                           self.to / f"{who}-to-audit.pkg", want=(0,))  # fmt: skip
            held[who] = {ln.split()[0] for ln in got.splitlines()}
            self.say(
                f"  {who:10} {'holds' if held[who] == {'holds'} else sorted(held[who])}"
            )
            if held[who] != {"holds"}:
                self.wrong.append(f"{who}'s chain did not hold to its package")
                self.ok["R7"] = False
        self.found_["witness"] = {
            w: "holds" if v == {"holds"} else sorted(v) for w, v in held.items()
        }

    def walls(self) -> None:
        """No package holds a long line of any pile but its sender's, the public
        filing and release aside."""
        public = {ln for t in public_texts() for ln in t.splitlines() if len(ln) > 40}
        piles = {b: {ln for p in self.pile(b).rglob("*.txt")
                     for ln in p.read_text(encoding="utf-8").splitlines() if len(ln) > 40} - public
                 for b in BOXES}  # fmt: skip
        before = len(self.wrong)
        for pkg in self.packages:
            body = pkg.read_text(encoding="utf-8")
            sender = pkg.stem.split("-to-")[0].replace("sec-check-", "")
            for b, lines in piles.items():
                if b != sender and any(ln in body for ln in lines):
                    self.wrong.append(f"{pkg.name} holds a line of the {b} pile")
                    self.ok["R2"] = False
        if len(self.wrong) == before:
            self.say(f"  {len(self.packages)} packages: each holds only its sender's pile "
                     "and the public filing")  # fmt: skip

    def rules(self) -> dict:
        """Each pass rule's verdict. A dry run scores nothing: its rows say only
        whether the wiring ran (`wired`) or broke."""
        for who in BOXES:
            seals = [r for r in self.rows(who) if r["kind"] == "seal"]
            if len(seals) != len(self.sealed[who]) or any(
                r.get("standing") != "sealed" or r.get("who") != "human" for r in seals
            ):
                self.ok["R7"] = False
        if not any(r["kind"] == "fixity" for r in self.rows("compliance")):
            self.ok["R6"] = False
        out = {}
        for rule, text in RULES.items():
            if self.dry:
                state = "wired" if self.ok[rule] and not self.wrong else "broke"
            else:
                state = "pass" if self.ok[rule] else "fail"
            out[rule] = {"state": state, "text": text}
        return out

    def summary(self) -> dict:
        doc: dict = {"boxes": {}, "ran": self.ran, "found": self.found_, "dry": self.dry,
                     "wrong": self.wrong}  # fmt: skip
        names = {self.pub[b]: b for b in BOXES}
        pre = {self.pub[b][:12]: b for b in BOXES}
        for who in BOXES:
            ver = self.run(KERNEL, "verify", "--box", self.box(who))
            rows = self.rows(who)
            held = "holds" in ver.lower()
            self.say(f"{who:11} {ver.strip().splitlines()[-1] if ver.strip() else '?'}")
            doc["boxes"][who] = {
                "pub": self.pub[who], "held": held, "rows": len(rows),
                "seals": len(self.sealed[who]), "said": self.said[who],
                "sent": [{"to": names.get(r["to"], "?"), "package": r["package"][:20],
                          "n": r["n"], "ts": r["ts"]} for r in rows if r["kind"] == "sent"],
                "received": [{"from": pre.get(r["from"][:12], "?"), "package": r["package"][:20],
                              "verdict": r["verdict"], "n": r["n"]}
                             for r in rows if r["kind"] == "received"],
                "fixity": [r["ts"] for r in rows if r["kind"] == "fixity"],
            }  # fmt: skip
            if not held:
                self.wrong.append(f"{who}'s chain did not verify")
        doc["rules"] = self.rules()
        return doc


def verdict_rows(box: Path, doc: dict) -> None:
    """One kernel row a rule, on a box outside the repo: its state, the rule, the
    SHA-256 of the answers it was scored on and of the code that scored them."""
    if not (box / "record.jsonl").exists():
        with contextlib.redirect_stdout(io.StringIO()):
            made = kernel.init(
                box, HERE, box.parent / (box.name + ".key"), kernel.now()
            )
        if made != kernel.ALIVE:
            raise SystemExit(f"refused: couldn't start a record at {box}")
    tools = {rel: h256((ROOT / rel).read_text(encoding="utf-8")) for rel in TOOLS}
    scored = {
        "rules": {k: v["state"] for k, v in doc["rules"].items()},
        "found": doc["found"],
    }
    answers = h256(canon(scored))
    for rule, v in doc["rules"].items():
        gate = f"blackout:{'dry:' if doc['dry'] else ''}{rule}"
        kernel.append(box, kernel.now(), "verdict", who="blackout", gate=gate,
                      state=v["state"], rule=v["text"], answers_sha256=answers, tools=tools)  # fmt: skip


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] != "run" or "--life" not in argv or "--to" not in argv:
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        return 2
    dry = "--dry" in argv
    study = Path(argv[argv.index("--box") + 1]) if "--box" in argv else None
    life = Path(argv[argv.index("--life") + 1])
    to = Path(argv[argv.index("--to") + 1])
    now = datetime(2026, 10, 20, 7, tzinfo=timezone.utc)
    if "--now" in argv:
        now = datetime.strptime(argv[argv.index("--now") + 1], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc)  # fmt: skip
    if to.exists() or not all((life / b).is_dir() for b in BOXES):
        print(
            "refused: --to must be new, and --life what make_life.py wrote",
            file=sys.stderr,
        )
        return 2
    scene = Scene(life, to, now, dry)
    doc = scene.play()
    (to / "scene.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    for rule, v in doc["rules"].items():
        print(f"{rule}  {v['state']:6}  {v['text']}")
    for w in scene.wrong:
        print(f"WRONG: {w}")
    if study is not None:
        verdict_rows(study, doc)
        print(f"verdicts appended to {study}: kernel.py verify --box {study}")
    return 1 if scene.wrong else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
