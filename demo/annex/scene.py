"""scene.py: the first beats of integration day, in eight boxes that never touch.

    python demo/annex/scene.py run --life DIR --to DIR [--now TS]

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
9. Counterintel, asked, seals the one innocent line about its review log and
   sends it to Oversight. Later its chain is rewritten: the seal backdated to
   before the day, every row after it re-hashed, so its own `verify` still says
   the chain holds. Oversight holds each chain to the packages it kept
   (`share witness`): every chain holds but one, and that one is `rewritten`.
10. Counterintel seals a scope for an assistant (`approved-only`): the one file
    a model may read holds the review line, and the rumour is not in it.
11. No package holds a line of another box's pile, the rumour is in no
    package or served file, and every chain verifies with only its owner's
    seals on it. The inspector's report is due at close of day, and is outside
    every chain.

`annex_os.py` puts a fictional terminal over what this writes. Still to play:
the planner's log. It writes a transcript to standard
output and scene.json under --to. Exit 0 when the scene plays as told, 1 when a
step went otherwise.
"""

from __future__ import annotations

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
from kernel import canon, h256  # noqa: E402

KERNEL = ROOT / "kernel.py"
STACK = ROOT / "adapters" / "stdlib" / "stack" / "stack.py"
APPROVED = ROOT / "adapters" / "stdlib" / "approved-only" / "approved_only.py"
SHARE = ROOT / "adapters" / "stdlib" / "share" / "share.py"
BOXES = ["intake", "vask", "karst", "lumen", "program", "counter", "oversight", "prior"]

#: the question both Vask and Counterintel are asked, word for word
HALVERN = "what is known about the Halvern chief executive"
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


class Scene:
    def __init__(self, life: Path, to: Path, now: datetime):
        self.life, self.to, self.now = life, to, now
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
        if verdicts != {"rewritten"}:
            self.wrong.append("the witness did not name the rewritten chain")
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
                                  HALVERN, "--now", self.ts()], capture_output=True,
                                 text=True)  # fmt: skip
            doc = json.loads(got.stdout)
            asked[who] = (got.returncode, doc)
            self.say(f"  {who:8} exit {got.returncode}, {len(doc['served'])} served")
        if asked["vask"][0] != 42 or asked["vask"][1]["served"]:
            self.wrong.append("Vask's box answered about the Halvern executive")
        if not asked["counter"][1]["served"]:
            self.wrong.append("Counterintel's box did not serve its own summary")

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
        edited = text.replace("cannot tell two programs", "can tell two programs")
        if edited == text:
            self.wrong.append("the edit found nothing to change")
        (self.to / "edited.pkg").write_text(edited, encoding="utf-8")
        bad = self.receive("oversight", self.to / "edited.pkg", want=(42,))
        if " broken" not in (bad.splitlines() or [""])[0]:
            self.wrong.append("the edited copy wasn't refused as broken")

        self.say("\n── 6. each box's own stack, over its own pile")
        self.own_stacks()

        self.say("\n── 7. the clash and the clocks arrive at Oversight")
        self.clash()

        self.say("\n── 8. the spec asks for everything, of everyone")
        self.asked()

        self.say("\n── 9. the rewrite, and the witness")
        self.found = self.witness()

        self.say("\n── 10. the one file an assistant may read")
        self.briefing()

        self.say("\n── 11. what crossed, and what did not")
        self.walls()
        return self.summary()

    def briefing(self) -> None:
        """The one file an assistant may read: only a scope its owner sealed."""
        who = "counter"
        self.run(KERNEL, "bite", "--box", self.box(who), "what was marked hold, not for release",
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
        if "review" not in text or "Halvern" in text or "affairs" in text:
            self.wrong.append("the served file is not the sealed scope alone")

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
            for b, lines in piles.items():
                if b != sender and any(ln in body for ln in lines):
                    self.wrong.append(f"{pkg.name} holds a line of the {b} pile")
        if len(self.wrong) == before:
            self.say(f"  {len(self.packages)} packages: the rumour in none, and each "
                     "holds only its sender's pile")  # fmt: skip

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
        return doc


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] != "run" or "--life" not in argv or "--to" not in argv:
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        return 2
    life = Path(argv[argv.index("--life") + 1])
    to = Path(argv[argv.index("--to") + 1])
    now = datetime(2026, 11, 18, 8, 0, 0, tzinfo=timezone.utc)
    if "--now" in argv:
        now = datetime.strptime(argv[argv.index("--now") + 1], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc)  # fmt: skip
    if to.exists():
        print(f"{to} is already there", file=sys.stderr)
        return 2
    scene = Scene(life, to, now)
    doc = scene.play()
    (to / "scene.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    for w in scene.wrong:
        print(f"WRONG: {w}")
    return 1 if scene.wrong else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
