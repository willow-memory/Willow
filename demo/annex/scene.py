"""scene.py: the first beats of integration day, in eight boxes that never touch.

    python demo/annex/scene.py run --life DIR --to DIR [--now TS] [--dry] [--box STUDYBOX]

DIR for --life is what make_life.py wrote: one folder per box. Each gets a box,
a seal key and an identity under --to, which must not be there yet. Then:

1. Every compartment's box is made, over its own pile only.
2. The wall: Vask asks her box about the Halvern chief executive and is told
   there is nothing on record (exit 42); Counterintel's box, asked the same,
   serves the unsealed summary. One question, two boxes, two answers.
3. Vask seals what her own files say and sends it to Oversight.
4. Lumen's field engineer has her moment: her firm's manifest answer, sealed
   and sent to Oversight, asked of no one.
5. A package edited on the way is refused where it lands.
6. Four boxes seal a stack of their own (Intake's gate check, Program's
   schedule check, Karst's and Lumen's claim checks) and run it over their own
   pile. Each finds nothing wrong: no box sees its own clash.
7. The clash, and the clocks. Karst's spec says an operator is a process;
   Lumen's data sheet says a person. The program schedule says integration day
   began at 08:00; the gate log says 09:00. Each box seals its own line and
   sends it to Oversight, the one place both sides arrive.
8. The spec asks every party for its manifest before tasking (2.2), so three
   boxes each send Karst a sealed answer. The pattern is in Karst's chain and
   in each sender's, and in no one chain alone.
9. The planner's log. Karst's planning model keeps a log of what it was asked;
   the inspector's standing rule has each party seal and send its own. Its
   line, at 06:10, asks for a profile of the Helio evaluation lead, a
   psychologist. Intake's gate log says a Helio badge was issued at 07:42, and
   the schedule has badges issuing from 07:30. `fixity` says the log was not
   touched. Nothing explains it, and the scene does not try to.
10. Counterintel, asked, seals the one innocent line about its review log and
   sends it to Oversight. Later its chain is rewritten: the seal backdated to
   before the day, every row after it re-hashed, so its own `verify` still says
   the chain holds. Oversight holds each chain to the packages it kept
   (`share witness`): every chain holds but one, and that one is `rewritten`.
11. Counterintel seals a scope for an assistant (`approved-only`): the one file
    a model may read holds the review line, and the rumour is not in it.
12. No package holds a line of another box's pile, the rumour is in no
    package or served file, and every chain verifies with only its owner's
    seals on it. The inspector's report is due at close of day, and is outside
    every chain.

`annex_os.py` puts a fictional terminal over what this writes. It writes a transcript to standard
output and scene.json under --to. Exit 0 when the scene plays as told, 1 when a
step went otherwise.
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
STACK = ROOT / "adapters" / "stdlib" / "stack" / "stack.py"
FIXITY = ROOT / "adapters" / "stdlib" / "fixity" / "fixity.py"
APPROVED = ROOT / "adapters" / "stdlib" / "approved-only" / "approved_only.py"
SHARE = ROOT / "adapters" / "stdlib" / "share" / "share.py"
BOXES = ["intake", "vask", "karst", "lumen", "program", "counter", "oversight", "prior"]

#: the question both Vask and Counterintel are asked, word for word
HALVERN = "what is known about the Halvern chief executive"
#: what every question becomes in a dry run
DRY_QUESTION = "qqqq zzzz"
#: (who, question, file its cite comes from, the answer, why)
SEALED = [
    ("vask", "what does the harness do with two programs that agree",
     "helio/notes.md",
     "The Helio harness cannot tell two programs that agree from two that were told to.",
     "my own notes, integration day"),
    ("lumen", "what was delivered to the program on integration day",
     "notes/manifest.md",
     "One sensor stream was delivered to the program on 2026-11-18, under contract L-4.",
     "the Lumen manifest; the other delivery is not on it"),
]  # fmt: skip


#: the clash and the clocks: each box's own line, sealed by its owner
CLASH = [
    ("karst", "what is an operator", "spec/interface.md",
     "Karst's interface spec, 2.1: an operator is a running process that holds a tasking channel.",
     "the interface specification, section 2.1"),
    ("lumen", "what is an operator", "sheet/datasheet.md",
     "Lumen's data sheet: an operator is the person who tasks the sensor array.",
     "the data sheet"),
    ("program", "when does integration day begin", "schedule.md",
     "The schedule says integration day begins at 08:00.",
     "the integration day schedule"),
    ("intake", "when does integration day begin", "badge-log.md",
     "The gate log says integration day begins at 09:00.",
     "the gate badge log"),
]  # fmt: skip

#: each box's own stack: (who, the words it is sealed under, why, [(pool, add-on)])
STACKS = [
    ("intake", "stack gate log check", "what the gate log shows about itself",
     [("where the log stops", "gaps")]),
    ("program", "stack schedule check", "whether the program's own papers agree",
     [("where the papers disagree", "contradictions")]),
    ("karst", "stack claim check", "whether Karst's own papers agree",
     [("where the papers disagree", "contradictions")]),
    ("lumen", "stack claim check", "whether Lumen's own papers agree",
     [("where the papers disagree", "contradictions")]),
]  # fmt: skip


#: what the spec's 2.2 asks of each party, sealed from its own papers
MANIFEST = ("vask", "does Helio deliver model weights", "helio/task-order.md",
            "Helio delivers the evaluation harness; it does not deliver model weights.",
            "the Helio task order")  # fmt: skip
#: Counterintel's one innocent line, asked for by Oversight
REVIEW = ("counter", "when was the summary last reviewed", "review.md",
          "The summary file was last reviewed on 2026-11-17 and marked hold, not for release.",
          "the review log")  # fmt: skip


#: the planner's line and the gate's, each sealed by its own box
PLANNED = [
    ("karst", "what was the planner asked about the Helio evaluation lead", "planner/log.md",
     "Karst's planner log: at 06:10 on 2026-11-18 it was asked for a profile of the Helio "
     "evaluation lead, background in clinical psychology.",
     "the planner's own log"),
    ("intake", "when was a badge issued to Helio", "badge-log.md",
     "The gate log: a badge was issued to one Helio visitor at 07:42 on 2026-11-18.",
     "the gate badge log"),
]  # fmt: skip


#: the pass rules, as frozen: each is a check the scene makes and scores
RULES = {
    "R1": "no sealed package holds a long line of any pile but its sender's",
    "R2": "the rumour is in no package and not in the file an assistant is served",
    "R3": "asked about another box's subject, a box answers nothing on record (exit 42) "
    "and serves nothing, while the box that holds it serves its own",
    "R4": "the witness holds every real chain and names exactly the rewritten copy",
    "R5": "a package edited on the way is refused as broken where it lands",
    "R6": "nothing but the person's own `seal` wrote a seal: every seal row is "
    "the person's, and each box holds as many as its owner sealed",
    "R7": "the corridor wrote no row on any chain, and the question asked after "
    "it holds no word of itself",
    "R8": "no box alone finds the clash or the clocks: each box's own stack flags nothing",
}
#: the code a verdict is made with, hashed onto each verdict row
TOOLS = ["kernel.py", "adapters/stdlib/share/share.py", "adapters/stdlib/fixity/fixity.py",
         "adapters/stdlib/approved-only/approved_only.py", "adapters/stdlib/stack/stack.py",
         "adapters/stdlib/contradictions/contradictions.py", "adapters/stdlib/gaps/gaps.py",
         "demo/annex/scene.py", "demo/annex/make_life.py"]  # fmt: skip


class Scene:
    def __init__(self, life: Path, to: Path, now: datetime, dry: bool = False):
        self.life, self.to, self.now, self.dry = life, to, now, dry
        #: each pass rule's check, set False where a check fails (scored only on a real run)
        self.ok = {f"R{i}": True for i in range(1, 9)}
        self.pub: dict[str, str] = {}
        self.ids: dict[str, Path] = {}
        self.wrong: list[str] = []
        self.sealed: dict[str, list[str]] = {b: [] for b in BOXES}
        self.answers: dict[str, list[str]] = {b: [] for b in BOXES}
        self.said: dict[str, list[dict]] = {b: [] for b in BOXES}
        self.packages: list[Path] = []

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

    def setup(self) -> None:
        self.to.mkdir()
        if self.dry:
            # every question is nonsense, so each pile gets one passage the nonsense finds
            # (its words out of order, so it is no echo of the question)
            pile = self.to / "_pile"
            shutil.copytree(self.life, pile)
            for who in BOXES:
                (pile / who / "dry.md").write_text(
                    f"# dry\n\nqqqq is not zzzz, says the {who} pile's one dry passage.\n",
                    encoding="utf-8",
                )
            self.life = pile
        for who in BOXES:
            (self.to / who).mkdir()
            self.run(KERNEL, "init", "--box", self.box(who), "--pile", self.life / who,
                     "--key", self.to / who / "key", "--now", self.ts())  # fmt: skip
            self.ids[who] = self.to / who / "id"
            self.pub[who] = self.run(SHARE, "id", "--to", self.ids[who]).strip()
            self.say(f"{who:10} box made, identity {self.pub[who][:12]}…")

    def seal(self, who: str, question: str, source: str, data: str, claim: str) -> str:
        """The person asks, writes the answer from what was served, and seals it:
        the person's act, played through the kernel's own `seal`."""
        if self.dry:
            # a repeated question would serve the earlier sealed answer first, so
            # each one carries a different nonsense word the passage need not hold
            question, source = (
                f"{DRY_QUESTION} {'x' * (4 + len(self.said[who]))}",
                "dry.md",
            )
            data = f"nonsense answer {len(self.said[who])} from {who}"
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
        prop = {"path": f"{who}/{cites[0][:8]}.md", "data": data, "cites": cites[:1],
                "claim": claim}  # fmt: skip
        sug = self.to / who / "suggestion.jsonl"
        sug.write_text(json.dumps(prop) + "\n")
        out = self.run(KERNEL, "propose", "--box", self.box(who), "--file", sug,
                       "--now", self.ts(), want=(42,))  # fmt: skip
        sug.unlink()
        subj = out.split()[1] if out.startswith("pass") else ""
        self.run(KERNEL, "seal", "--box", self.box(who), subj, "--now", self.ts())
        self.sealed[who].append(subj)
        self.answers[who].append(subj)
        self.said[who].append({"data": data, "claim": claim, "cite": source})
        self.say(f"  {who} sealed: {data}")
        return subj

    def send(self, who: str, subject: str, to_whom: str, name: str, note: str) -> Path:
        pkg = self.to / f"{name}.pkg"
        self.run(SHARE, "send", "--box", self.box(who), "--id", self.ids[who],
                 "--answer", subject, "--for", self.pub[to_whom], "--to", pkg,
                 "--note", note, "--now", self.ts())  # fmt: skip
        self.packages.append(pkg)
        self.say(f"  {who} packs {name} for {to_whom}")
        return pkg

    def receive(self, who: str, pkg: Path, want=(0,)) -> str:
        out = self.run(SHARE, "receive", "--box", self.box(who), "--id", self.ids[who],
                       "--package", pkg, "--now", self.ts(), want=want)  # fmt: skip
        self.say(f"{who} receives {pkg.name}:")
        for line in out.splitlines():
            self.say(f"  {line}")
        return out

    def stack_text(self, who: str, why: str, steps: list) -> str:
        """The stack file, each step's add-on pinned by SHA-256 on a comment line."""
        out = [f"# {who}'s stack: {why}"]
        for _, step in steps:
            path = (
                ROOT / "adapters" / "stdlib" / step / (step.replace("-", "_") + ".py")
            )
            out.append(f"# pin {step} {h256(path.read_text(encoding='utf-8'))}")
        for pool, step in steps:
            out += ["", f"## {pool}", f"- {step} -- --box {{box}}"]
        return "\n".join(out) + "\n"

    def keep(self, who: str, words: str, name: str, text: str, claim: str) -> str:
        """A stack is sealed like an answer that cites nothing: the owner's act."""
        self.run(KERNEL, "bite", "--box", self.box(who), words, "--now", self.ts(),
                 want=(0, 42))  # fmt: skip
        sug = self.to / who / "suggestion.jsonl"
        sug.write_text(json.dumps({"path": f"stacks/{name}.md", "data": text,
                                   "cites": [], "claim": claim}) + "\n")  # fmt: skip
        out = self.run(KERNEL, "propose", "--box", self.box(who), "--file", sug,
                       "--now", self.ts(), want=(42,))  # fmt: skip
        sug.unlink()
        subj = out.split()[1] if out.startswith("pass") else ""
        self.run(KERNEL, "seal", "--box", self.box(who), subj, "--now", self.ts())
        self.sealed[who].append(subj)
        return subj

    def own_stacks(self) -> None:
        for who, words, why, steps in STACKS:
            name = words.split(" ", 1)[1].replace(" ", "-")
            self.keep(who, words, name, self.stack_text(who, why, steps), why)
            kept = self.box(who) / "written" / "stacks" / f"{name}.md"
            ran = subprocess.run([sys.executable, str(STACK), "--box", str(self.box(who)),
                                  "--stack", str(kept)], capture_output=True, text=True)  # fmt: skip
            first = next((ln for ln in ran.stdout.splitlines()[::-1] if ln.strip()), "")
            self.say(f"  {who:8} seals its {name.replace('-', ' ')} and runs it: exit "
                     f"{ran.returncode}, {first.strip()[:80]}")  # fmt: skip
            if ran.returncode not in (0, 42) or not ran.stdout.strip():
                self.wrong.append(f"{who}'s {name} printed nothing")
            if "DATE" in ran.stdout or "AMOUNT" in ran.stdout:
                self.wrong.append(f"{who}'s own box found a clash it should not see")
                self.ok["R8"] = False

    def clash(self) -> None:
        got: dict[str, tuple[str, Path]] = {}
        for who, q, src, data, claim in CLASH:
            subj = self.seal(who, q, src, data, claim)
            pkg = self.send(who, subj, "oversight", f"{who}-clash-to-oversight",
                            "Sealed from my own papers, as asked")  # fmt: skip
            self.receive("oversight", pkg)
            got[who] = (data, pkg)
        self.say("\n  Oversight lays what arrived side by side (the scene's own "
                 "comparison: no add-on reads\n  received packages yet)")  # fmt: skip
        if self.dry:
            return
        k, l_ = got["karst"][0], got["lumen"][0]
        if "process" not in k or "person" not in l_:
            self.wrong.append("the operator definitions did not arrive as sealed")
        self.say(f"  OPERATOR   Karst: {k.split(': ', 1)[1][:60]}")
        self.say(
            f"             Lumen: {l_.split(': ', 1)[1][:60]}   (neither side is picked)"
        )
        clocks = {w: re.findall(r"\d\d:\d\d", got[w][0]) for w in ("program", "intake")}
        if clocks["program"] != ["08:00"] or clocks["intake"] != ["09:00"]:
            self.wrong.append("the two clocks did not arrive as sealed")
        self.say(f"  CLOCK      Program: {clocks['program'][0]}    Intake: {clocks['intake'][0]}"
                 "   (one hour, in no single box)")  # fmt: skip

    def asked(self) -> None:
        """Spec 2.2 asks every party for its manifest. Three send; the pattern is
        in no one chain, but in all of them."""
        mine = self.seal(*MANIFEST)
        gave = {"vask": mine, "lumen": self.answers["lumen"][0],
                "program": self.answers["program"][0]}  # fmt: skip
        for who, subj in gave.items():
            pkg = self.send(who, subj, "karst", f"{who}-to-karst", "As spec 2.2 asks")
            self.receive("karst", pkg)
        names = {self.pub[b]: b for b in BOXES}
        self.say("\n  every chain's sent rows, read together (the scene's view: no one "
                 "box has it)")  # fmt: skip
        got_by: dict[str, set[str]] = {b: set() for b in BOXES}
        for who in BOXES:
            for r in self.rows(who):
                if r["kind"] == "sent":
                    got_by[names[r["to"]]].add(who)
        for b in ("karst", "oversight"):
            self.say(f"  {b:10} was sent to by {', '.join(sorted(got_by[b]))}")
        if got_by["karst"] != {"vask", "lumen", "program"}:
            self.wrong.append("Karst did not receive from the three boxes it asked")
        sent_by_karst = {
            names[r["to"]] for r in self.rows("karst") if r["kind"] == "sent"
        }
        self.say(f"  karst received from three and sent to {', '.join(sorted(sent_by_karst))} "
                 "only: spec 2.2 took from each what it gave none")  # fmt: skip

    def planned(self) -> dict:
        """The planner was asked about Vask before her badge existed. fixity says
        the log is as it was first seen; the scene does not explain it."""
        karst = self.box("karst")
        first = self.run(FIXITY, "--box", karst, "--now", self.ts())
        for who, q, src, data, claim in PLANNED:
            subj = self.seal(who, q, src, data, claim)
            pkg = self.send(who, subj, "oversight", f"{who}-log-to-oversight",
                            "Sealed under the inspector's standing rule")  # fmt: skip
            self.receive("oversight", pkg)
        again = self.run(FIXITY, "--box", karst, "--now", self.ts())
        if "needs you" in first + again or "holds" not in again:
            self.wrong.append(
                f"fixity said something about the planner log: {again.strip()}"
            )
        if self.dry:
            return {"asked": "", "badge": "", "minutes": 0, "fixity": "untouched"}
        asked = re.findall(r"\d\d:\d\d", self.said["karst"][-1]["data"])[0]
        badge = re.findall(r"\d\d:\d\d", self.said["intake"][-1]["data"])[0]
        mins = (int(badge[:2]) * 60 + int(badge[3:])) - (
            int(asked[:2]) * 60 + int(asked[3:])
        )
        self.say(f"\n  PLANNER  asked about the Helio lead at {asked}")
        self.say(f"  GATE     issued the Helio badge at {badge}")
        self.say(f"  {mins} minutes before the badge, and before badges issue (07:30)."
                 "\n  fixity: the planner log is as it was first seen. Nothing explains it.")  # fmt: skip
        if mins <= 0:
            self.wrong.append("the planner's query does not predate the badge")
        return {"asked": asked, "badge": badge, "minutes": mins, "fixity": "untouched"}

    def rows(self, who: str) -> list[dict]:
        text = (self.box(who) / "record.jsonl").read_text()
        return [json.loads(line) for line in text.splitlines()]

    def rewrite(self) -> dict:
        """Counterintel's seal is backdated to before the day and every row after
        it re-hashed, so its own verify can't see it."""
        real = self.box("counter")
        fake = self.to / "counter-rewritten"
        shutil.copytree(real, fake)
        rows = [json.loads(x) for x in (fake / "record.jsonl").read_text().splitlines()]
        n = [r["n"] for r in rows if r["kind"] == "seal"][0]
        rows[n]["ts"] = "2026-11-17T22:00:00Z"
        for i in range(n, len(rows)):
            rows[i]["prev"] = rows[i - 1]["hash"]
            body = {k: v for k, v in rows[i].items() if k != "hash"}
            rows[i]["hash"] = h256(canon(body))
        (fake / "record.jsonl").write_text("".join(canon(r) + "\n" for r in rows))
        said = self.run(KERNEL, "verify", "--box", fake).strip()
        self.say(f"  Counterintel's rewritten copy, by its own verify: {said}")
        if not said.startswith("the chain holds"):
            self.wrong.append("the rewritten copy did not fool verify")
        return {"real": real, "fake": fake}

    def witness(self) -> dict:
        self.say("  Counterintel, asked, seals one innocent line and sends it up")
        line = self.seal(*REVIEW)
        cpkg = self.send("counter", line, "oversight", "counter-to-oversight",
                         "The review log, as asked")  # fmt: skip
        self.receive("oversight", cpkg)
        boxes = self.rewrite()
        out: dict[str, str] = {}
        self.say("\n  Oversight holds each chain to the packages it kept")
        for who in ("vask", "lumen", "karst", "program", "intake", "counter"):
            kept = [str(p) for p in self.packages if p.stem.startswith(f"{who}-")
                    and p.stem.endswith("-to-oversight")]  # fmt: skip
            got = self.run(SHARE, "witness", "--box", boxes["real"] if who == "counter"
                           else self.box(who), "--package", ",".join(kept), want=(0,))  # fmt: skip
            verdicts = {ln.split()[0] for ln in got.splitlines()}
            out[who] = "holds" if verdicts == {"holds"} else "/".join(sorted(verdicts))
            self.say(f"  {who:10} real record: {out[who]}")
        got = self.run(SHARE, "witness", "--box", boxes["fake"], "--package",
                       str(self.to / "counter-to-oversight.pkg"), want=(42,))  # fmt: skip
        verdicts = {ln.split()[0] for ln in got.splitlines()}
        self.say(f"  counter    rewritten copy: {'/'.join(sorted(verdicts))}")
        if set(out.values()) != {"holds"}:
            self.wrong.append(f"a real chain did not hold: {out}")
            self.ok["R4"] = False
        if verdicts != {"rewritten"}:
            self.wrong.append("the witness did not name the rewritten chain")
            self.ok["R4"] = False
        self.say("\n  Oversight's report is due at close of day. What it says is "
                 "outside every chain.")  # fmt: skip
        return {"real": out, "rewritten": sorted(verdicts)}

    def play(self) -> dict:
        self.say("── 1. eight boxes, each over its own pile")
        self.setup()

        self.say("\n── 2. the wall: one question, two boxes")
        asked = {}
        for who in ("vask", "counter"):
            got = subprocess.run([sys.executable, KERNEL, "bite", "--box", self.box(who),
                                  DRY_QUESTION if self.dry else HALVERN, "--now", self.ts()],
                                 capture_output=True, text=True)  # fmt: skip
            doc = json.loads(got.stdout)
            asked[who] = (got.returncode, doc)
            self.say(f"  {who:8} exit {got.returncode}, {len(doc['served'])} served")
        if not self.dry and (asked["vask"][0] != 42 or asked["vask"][1]["served"]):
            self.wrong.append("Vask's box answered about the Halvern executive")
            self.ok["R3"] = False
        if not asked["counter"][1]["served"]:
            self.wrong.append("Counterintel's box did not serve its own summary")
            self.ok["R3"] = False

        self.say("\n── 3. Vask seals what her own files say, and sends it to Oversight")
        mine = self.seal(*SEALED[0])
        vpkg = self.send(
            "vask", mine, "oversight", "vask-to-oversight", "My notes, as asked"
        )
        self.receive("oversight", vpkg)

        self.say("\n── 4. Lumen's engineer, asked by no one")
        lum = self.seal(*SEALED[1])
        lpkg = self.send("lumen", lum, "oversight", "lumen-to-oversight",
                         "Sent on my own. Ask me about the manifest.")  # fmt: skip
        self.receive("oversight", lpkg)

        self.say("\n── 5. a copy edited on the way")
        text = vpkg.read_text(encoding="utf-8")
        edited = text.replace(
            "nonsense answer" if self.dry else "cannot tell two programs",
            "forged answer" if self.dry else "can tell two programs",
        )
        if edited == text:
            self.wrong.append("the edit found nothing to change")
        (self.to / "edited.pkg").write_text(edited, encoding="utf-8")
        bad = self.receive("oversight", self.to / "edited.pkg", want=(42,))
        if " broken" not in (bad.splitlines() or [""])[0]:
            self.wrong.append("the edited copy wasn't refused as broken")
            self.ok["R5"] = False

        self.say("\n── 6. each box's own stack, over its own pile")
        self.own_stacks()

        self.say("\n── 7. the clash and the clocks arrive at Oversight")
        self.clash()

        self.say("\n── 8. the spec asks for everything, of everyone")
        self.asked()

        self.say("\n── 9. the planner's log")
        planner = self.planned()

        self.say("\n── 10. the rewrite, and the witness")
        self.found = {**self.witness(), "planner": planner}

        self.say("\n── 11. the one file an assistant may read")
        self.briefing()

        self.say("\n── 12. the corridor")
        self.found["corridor"] = self.corridor()

        self.say("\n── 13. what crossed, and what did not")
        self.walls()
        return self.summary()

    def corridor(self) -> dict:
        """Two people talk, and no chain hears it. What is checked is what is
        missing: no row in the window, and a question asked afterwards whose row
        holds a hash, not its words."""
        paras = (HERE / "corridor.md").read_text(encoding="utf-8").split("\n\n")
        talk = [ln for ln in "\n\n".join(paras[2:]).splitlines() if ln.strip()]
        last = max(r["ts"] for b in BOXES for r in self.rows(b))
        self.say(f"  the last row on any chain is at {last}. The corridor starts here.")
        self.say("  ── OFF THE RECORD " + "─" * 40)
        for ln in talk:
            self.say(f"  | {ln}")
        self.say("  ── " + "─" * 55)
        self.now += timedelta(minutes=33)
        question = DRY_QUESTION if self.dry else HALVERN
        got = subprocess.run(
            [sys.executable, KERNEL, "bite", "--box", self.box("vask"), question,
             "--now", self.ts()], capture_output=True, text=True)  # fmt: skip
        after = self.rows("vask")[-1]
        if after["kind"] != "bite" or (not self.dry and got.returncode != 42):
            self.wrong.append(
                "Vask's question after the corridor was not an empty bite"
            )
            self.ok["R7"] = False
        if any(
            w in json.dumps(after).lower() for w in ("halvern", "executive", "chief")
        ):
            self.wrong.append("a row on Vask's chain holds the words of her question")
            self.ok["R7"] = False
        inside = [(b, r["n"]) for b in BOXES for r in self.rows(b)
                  if last < r["ts"] < after["ts"]]  # fmt: skip
        if inside:
            self.wrong.append(f"rows were written in the corridor's window: {inside}")
            self.ok["R7"] = False
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        before = max(r["ts"] for r in self.rows("vask") if r["ts"] <= last)
        gap = int((datetime.strptime(after["ts"], fmt)
                   - datetime.strptime(before, fmt)).total_seconds() // 60)  # fmt: skip
        silent = [b for b in BOXES if b != "vask"
                  and max(r["ts"] for r in self.rows(b)) <= last]  # fmt: skip
        self.say(
            f"  rows written on any of the eight chains in that window: {len(inside)}"
        )
        self.say(f"  vask's chain: {gap} minutes from the row before to the row after")
        self.say(f"  the other seven: {len(silent)} wrote nothing at all after {last}")
        self.say("  vask asks her box about the executive: exit 42, and her record's row "
                 f"holds {after['bite_key'][:12]}\u2026, not the question")  # fmt: skip
        return {"from": last, "to": after["ts"], "rows_in_window": len(inside),
                "vask_gap_minutes": gap, "silent_chains": len(silent),
                "bite_row": after["bite_key"][:12], "lines": talk}  # fmt: skip

    def briefing(self) -> None:
        """The one file an assistant may read: only a scope its owner sealed."""
        who = "counter"
        self.run(KERNEL, "bite", "--box", self.box(who),
                 DRY_QUESTION if self.dry else "what was marked hold, not for release",
                 "--now", self.ts(), want=(0, 42))  # fmt: skip
        out = self.run(
            APPROVED, "scope", "--box", self.box(who), "--now", self.ts(), want=(42,)
        )
        subj = next(
            (
                w
                for ln in out.splitlines()
                for w in ln.split()
                if w.startswith("proposal:")
            ),
            "",
        )
        self.run(KERNEL, "seal", "--box", self.box(who), subj, "--now", self.ts())
        self.sealed[who].append(subj)
        served = self.to / who / "served.md"
        self.run(APPROVED, "--box", self.box(who), "--to", served, "--now", self.ts())
        text = served.read_text(encoding="utf-8") if served.is_file() else ""
        self.say(
            f"  counter seals a scope and serves {len(text.splitlines())} lines to an assistant"
        )
        if "Halvern" in text or "affairs" in text or not (self.dry or "review" in text):
            self.wrong.append("the served file is not the sealed scope alone")
            self.ok["R2"] = False

    def walls(self) -> None:
        """No package holds a long line of any pile but its sender's, and none
        holds the rumour."""
        piles = {b: {ln for p in (self.life / b).rglob("*.md")
                     for ln in p.read_text(encoding="utf-8").splitlines() if len(ln) > 40}
                 for b in BOXES}  # fmt: skip
        before = len(self.wrong)
        for pkg in self.packages:
            body = pkg.read_text(encoding="utf-8")
            sender = pkg.stem.split("-")[0]
            if "Halvern" in body:
                self.wrong.append(f"the rumour is in {pkg.name}")
                self.ok["R2"] = False
            for b, lines in piles.items():
                if b != sender and any(ln in body for ln in lines):
                    self.wrong.append(f"{pkg.name} holds a line of the {b} pile")
                    self.ok["R1"] = False
        if len(self.wrong) == before:
            self.say(f"  {len(self.packages)} packages: the rumour in none, and each "
                     "holds only its sender's pile")  # fmt: skip

    def rules(self) -> dict:
        """Each pass rule's verdict. A dry run scores nothing: its rows say only
        whether the wiring ran (`wired`) or broke."""
        for who in BOXES:
            seals = [r for r in self.rows(who) if r["kind"] == "seal"]
            if len(seals) != len(self.sealed[who]) or any(
                r.get("standing") != "sealed" or r.get("who") != "human" for r in seals
            ):
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
        served = self.to / "counter" / "served.md"
        doc: dict = {
            "served": served.read_text(encoding="utf-8") if served.is_file() else "",
            "boxes": {},
            "found": getattr(self, "found", {}),
            "wrong": self.wrong,
        }
        for who in BOXES:
            ver = self.run(KERNEL, "verify", "--box", self.box(who))
            out = self.run(KERNEL, "out", "--box", self.box(who))
            held = "holds" in ver.lower() or "ok" in ver.lower()
            seals = len(self.sealed[who])
            self.say(f"{who:10} {ver.strip().splitlines()[-1] if ver.strip() else '?'}")
            names = {self.pub[b]: b for b in BOXES}
            pre = {self.pub[b][:12]: b for b in BOXES}
            rows = self.rows(who)
            doc["boxes"][who] = {"pub": self.pub[who], "seals": seals, "verify": ver.strip(),
                                 "held": held, "out": out.strip()[:200], "rows": len(rows),
                                 "said": self.said[who],
                                 "sent": [{"to": names.get(r["to"], "?"), "package": r["package"][:20],
                                           "n": r["n"], "ts": r["ts"]}
                                          for r in rows if r["kind"] == "sent"],
                                 "received": [{"from": pre.get(r["from"][:12], "?"),
                                               "package": r["package"][:20], "verdict": r["verdict"],
                                               "n": r["n"]}
                                              for r in rows if r["kind"] == "received"]}  # fmt: skip
            if not held:
                self.wrong.append(f"{who}'s chain did not verify")
        doc["rules"] = self.rules()
        doc["dry"] = self.dry
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
    scored = {"rules": {k: v["state"] for k, v in doc["rules"].items()},
              "found": {k: v for k, v in doc["found"].items() if k != "corridor"}}  # fmt: skip
    answers = h256(canon(scored))
    for rule, v in doc["rules"].items():
        gate = f"annex:{'dry:' if doc['dry'] else ''}{rule}"
        kernel.append(box, kernel.now(), "verdict", who="annex", gate=gate,
                      state=v["state"], rule=v["text"], answers_sha256=answers, tools=tools)  # fmt: skip


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] != "run" or "--life" not in argv or "--to" not in argv:
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        return 2
    dry = "--dry" in argv
    study = Path(argv[argv.index("--box") + 1]) if "--box" in argv else None
    life = Path(argv[argv.index("--life") + 1])
    to = Path(argv[argv.index("--to") + 1])
    now = datetime(2026, 11, 18, 8, 0, 0, tzinfo=timezone.utc)
    if "--now" in argv:
        now = datetime.strptime(argv[argv.index("--now") + 1], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc)  # fmt: skip
    if to.exists():
        print(f"{to} is already there", file=sys.stderr)
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
