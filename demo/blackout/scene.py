"""scene.py: the SEC stack, signed by Legal and Compliance, in every box.

    python demo/blackout/scene.py run --life DIR --to DIR [--now TS]

DIR for --life is what make_life.py wrote: one folder per box. Each gets a box,
a seal key and an identity under --to, which must not be there yet; the piles
are copied there first, so the scene can edit a file without touching the repo.

1. Eight boxes, one a person's own, over its own pile.
2. Compliance runs `fixity` over its own papers (2026-10-20), the first check
   there is, and on 10-26 Ruth edits the quiz key.
3. Legal seals a stack (the SEC check) and sends it to Compliance. Compliance
   receives it and signs it too, by passing it on to each of the other six boxes
   in a layer of its own: the stack arrives with two signatures, and a layer
   nobody can change without breaking both.
4. Each receiver checks the pin of every add-on the stack runs, seals the stack
   themselves (their claim names the package) and runs it over their own box.
   The files it reads never travel. The auditor declines it: an auditor runs no
   one's tools.
5. What the stack found, box by box: `fixity` says the quiz key was edited,
   with no word of why; `first-mention` says the shipments figure first
   appears in Investor Relations' box on 10-27, and in every other box on
   11-05, the day of the filing. `contradictions` finds nothing anywhere: it
   leaves two figures written on different days alone, as a plan changed.
6. Every box is verified, and each record holds only its own seals.

A first slice: the sealed answers, the join across boxes that shows who sold,
the attestation and Audit's report come after. It writes a transcript to
standard output and scene.json under --to. Exit 0 when the scene plays as told,
1 when a step went otherwise.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from kernel import h256  # noqa: E402

KERNEL = ROOT / "kernel.py"
STACK = ROOT / "adapters/stdlib/stack/stack.py"
SHARE = ROOT / "adapters/stdlib/share/share.py"
BOXES = ["trainee", "compliance", "legal", "ir", "floor", "plan", "steward", "audit"]
#: who gets the stack from the two who sign it, and what each does with it
RECEIVERS = ["trainee", "ir", "floor", "plan", "steward", "audit"]
DECLINES = {"audit"}

#: the SEC check: (pool, add-on): what a box's papers say about themselves
LATER = "2026-10-30T11:00:00Z"  # the clock fixity reads, so the stack says the same thing twice
#: (pool, add-on, its arguments after --box {box})
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


class Scene:
    def __init__(self, life: Path, to: Path, now: datetime):
        self.life, self.to, self.now = life, to, now
        self.pub: dict[str, str] = {}
        self.ids: dict[str, Path] = {}
        self.wrong: list[str] = []
        self.sealed: dict[str, list[str]] = {b: [] for b in BOXES}
        self.packages: list[Path] = []
        self.ran: dict[str, dict] = {}

    def at(self, ts: str) -> None:
        self.now = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )

    def ts(self) -> str:
        from datetime import timedelta

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

    def setup(self) -> None:
        self.to.mkdir()
        shutil.copytree(self.life, self.to / "_pile")
        for who in BOXES:
            (self.to / who).mkdir()
            self.run(KERNEL, "init", "--box", self.box(who), "--pile", self.pile(who),
                     "--key", self.to / who / "key", "--now", self.ts())  # fmt: skip
            self.ids[who] = self.to / who / "id"
            self.pub[who] = self.run(SHARE, "id", "--to", self.ids[who]).strip()
            self.say(f"{who:11} box made, identity {self.pub[who][:12]}…")

    def fixity(self, who: str) -> str:
        out = self.run(ROOT / "adapters/stdlib/fixity/fixity.py", "--box", self.box(who),
                       "--now", self.ts(), want=(0, 42))  # fmt: skip
        return out.strip()

    def keep(self, who: str, text: str, claim: str) -> str:
        """A stack is sealed like an answer that cites nothing: the owner's act,
        played through the kernel's own `seal`."""
        self.run(KERNEL, "bite", "--box", self.box(who), STACK_WORDS, "--now", self.ts(),
                 want=(0, 42))  # fmt: skip
        sug = self.to / who / "suggestion.jsonl"
        sug.write_text(json.dumps({"path": f"stacks/{STACK_NAME}.md", "data": text,
                                   "cites": [], "claim": claim}) + "\n")  # fmt: skip
        out = self.run(KERNEL, "propose", "--box", self.box(who), "--file", sug,
                       "--now", self.ts(), want=(42,))  # fmt: skip
        sug.unlink()
        subj = out.split()[1] if out.startswith("pass") else ""
        self.run(KERNEL, "seal", "--box", self.box(who), subj, "--now", self.ts())
        self.sealed[who].append(subj)
        return subj

    def share(self, cmd: str, who: str, *argv: str, want=(0,)) -> str:
        return self.run(SHARE, cmd, "--box", self.box(who), "--id", self.ids[who], *argv,
                        "--now", self.ts(), want=want)  # fmt: skip

    def decline(self, who: str, text: str, why: str) -> str:
        self.run(KERNEL, "bite", "--box", self.box(who), STACK_WORDS, "--now", self.ts(),
                 want=(0, 42))  # fmt: skip
        sug = self.to / who / "suggestion.jsonl"
        sug.write_text(json.dumps({"path": f"stacks/{STACK_NAME}.md", "data": text,
                                   "cites": [], "claim": why}) + "\n")  # fmt: skip
        out = self.run(KERNEL, "propose", "--box", self.box(who), "--file", sug,
                       "--now", self.ts(), want=(42,))  # fmt: skip
        sug.unlink()
        subj = out.split()[1] if out.startswith("pass") else ""
        said = self.run(
            KERNEL, "decline", "--box", self.box(who), subj, "--now", self.ts()
        )
        return said.strip()

    def run_stack(self, who: str) -> subprocess.CompletedProcess:
        kept = self.box(who) / "written" / "stacks" / f"{STACK_NAME}.md"
        return subprocess.run([sys.executable, str(STACK), "--box", str(self.box(who)),
                               "--stack", str(kept)], capture_output=True, text=True)  # fmt: skip

    def play(self) -> dict:
        self.say("── 1. eight boxes, each over its own papers")
        self.at("2026-10-20T07:00:00Z")
        self.setup()

        self.say("\n── 2. the quiz key, checked once, then edited")
        first = self.fixity("compliance")
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
        got = self.share("receive", "compliance", "--package", legal_pkg)
        self.say("  compliance receives it:")
        for line in got.splitlines():
            self.say(f"    {line}")
        for who in RECEIVERS:
            pkg = self.to / f"sec-check-compliance-to-{who}.pkg"
            self.share("forward", "compliance", "--package", legal_pkg, "--for",
                       self.pub[who], "--to", pkg, "--note",
                       "Signed by Legal and by me")  # fmt: skip
            self.packages.append(pkg)
        self.say(
            f"  compliance passes it on, in a layer of its own, to {len(RECEIVERS)} boxes"
        )

        self.say(
            "\n── 4. each box checks the pins, takes it or declines it, and runs it"
        )
        # Compliance seals it itself, to run it over its own papers
        self.keep("compliance", text, f"taken from {legal_pkg.name}, every pin checked")
        self.ran["compliance"] = self.report("compliance", "compliance's own box", None)
        for who in RECEIVERS:
            pkg = self.to / f"sec-check-compliance-to-{who}.pkg"
            got = self.share("receive", who, "--package", pkg)
            layers = got.count("└ from ")
            doc = innermost(json.loads(pkg.read_text(encoding="utf-8")))
            data = doc["answers"][0]["data"]
            same = all(h256(script(s).read_text(encoding="utf-8")) == h
                       for s, h in pins(data).items()) and len(pins(data)) == len(STACK_STEPS)  # fmt: skip
            self.say(
                f"  {who:10} receives it: {layers + 1} signatures, every pin "
                f"{'the same code here' if same else 'NOT the same code here'}"
            )
            if layers != 1:
                self.wrong.append(f"{who} did not see two signatures: {layers + 1}")
            if who in DECLINES or not same:
                said = self.decline(
                    who, data, "offered by two others; an auditor runs no party's tools"
                )
                self.say(f"  {who:10} declines it: {said.split(';')[-1].strip()[:70]}")
                self.ran[who] = {"taken": False}
                continue
            self.keep(who, data, f"taken from {pkg.name}, every pin checked")
            self.ran[who] = self.report(who, who, pkg.name)

        self.say("\n── 5. what the stack found, and what it did not")
        self.found()
        self.say("\n── 6. every chain")
        return self.summary()

    def found(self) -> None:
        edited = [ln for ln in self.ran["compliance"]["flagged"] if "quiz-key" in ln]
        self.say(f"  fixity, in compliance's box: {edited[0] if edited else 'nothing'}")
        self.say("  fixity in every other box: nothing flagged")
        self.say(f"  first-mention, in ir's box: the figure first appears "
                 f"{self.ran['ir']['first']}; in every other box, {self.ran['trainee']['first']}")  # fmt: skip
        if not edited:
            self.wrong.append("fixity did not say the quiz key was edited")
        for who, r in self.ran.items():
            if r.get("taken") and who != "compliance" and r["flagged"]:
                self.wrong.append(
                    f"{who}'s box flagged something it should not: {r['flagged']}"
                )
        if self.ran["ir"]["first"] != "2026-10-27":
            self.wrong.append("the figure did not first appear in ir's box on 10-27")
        for who in ("trainee", "floor", "plan", "steward"):
            if self.ran[who]["first"] != "2026-11-05":
                self.wrong.append(f"{who}'s box saw the figure before the filing")
        self.say("  contradictions found nothing anywhere: it leaves two figures written on\n"
                 "  different days alone, as a plan changed, and picks neither")  # fmt: skip

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
        return {
            "taken": True,
            "exit": ran.returncode,
            "flagged": flagged,
            "first": first,
            "package": pkg,
        }

    def summary(self) -> dict:
        doc: dict = {"boxes": {}, "ran": self.ran, "wrong": self.wrong}
        for who in BOXES:
            ver = self.run(KERNEL, "verify", "--box", self.box(who))
            rows = [json.loads(x) for x in
                    (self.box(who) / "record.jsonl").read_text().splitlines()]  # fmt: skip
            held = "holds" in ver.lower()
            self.say(f"{who:11} {ver.strip().splitlines()[-1] if ver.strip() else '?'}")
            doc["boxes"][who] = {"pub": self.pub[who], "held": held, "rows": len(rows),
                                 "seals": len(self.sealed[who])}  # fmt: skip
            if not held:
                self.wrong.append(f"{who}'s chain did not verify")
        return doc


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2]))
    if (argv[:1] != ["run"] or len(argv) % 2 != 1
            or not {"--life", "--to"} <= opts.keys() <= {"--life", "--to", "--now"}):  # fmt: skip
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        return 2
    life, to = Path(opts["--life"]), Path(opts["--to"])
    if to.exists() or not all((life / b).is_dir() for b in BOXES):
        print(
            "refused: --to must be new, and --life what make_life.py wrote",
            file=sys.stderr,
        )
        return 2
    scene = Scene(life, to, datetime(2026, 10, 20, 7, tzinfo=timezone.utc))
    doc = scene.play()
    (to / "scene.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    for w in scene.wrong:
        print(f"WRONG: {w}")
    return 1 if scene.wrong else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
