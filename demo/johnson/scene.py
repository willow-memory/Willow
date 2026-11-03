"""scene.py: the Johnson report, passed from one person's willow to the next.

    python demo/johnson/scene.py run --life DIR --to DIR [--now TS]

DIR for --life is what make_life.py wrote: one folder per person. Each gets a
box of their own, a seal key and an identity under --to, which must not be
there yet. Then the scene:

1. Ines asks her own files four questions and seals her answers: the
   person's act, played here as bernadette's stack test plays it, through
   the kernel's own `seal`.
2. Walt asks for the report. She packs the four for Walt's key (share send).
3. Walt receives it and forwards it to Aurelie at the insurer; Aurelie to
   Tamsin, its counsel; Tamsin to Harold, the mediator. Each hop is a row on
   both people's chains, and each forward a layer the next can't change.
4. A copy edited on the way to Tamsin ($2,140 made $21,400) is refused
   where it lands, and the refusal is on her chain; the true copy holds.
5. Ines finds her report gave the wrong day for the call. She seals the
   right answer and sends a new report that replaces the first. At each hop
   `receive` says who the old one went to next, and the correction follows.
   Walt's laptop is replaced on the way: Walt rotates to a new key, signed by
   the old, and Aurelie sees the new key as Walt's, not a stranger's.
6. Ines rewrites a copy of her record: her wrong answer's seal backdated
   and every row after it re-hashed, so her own `verify` still says it
   holds. Each of the others holds her record to the packages they kept
   (share witness): the real one holds, the rewritten one doesn't.
7. Every box is verified, and nobody's record holds a seal but their own.

It writes a transcript to standard output and scene.json under --to: each
person's public key, rows and what they sent and received, and the packages.
Exit 0 when the scene plays as told, 1 when a step went otherwise.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kernel import canon, h256  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
KERNEL = ROOT / "kernel.py"
SHARE = ROOT / "adapters" / "stdlib" / "share" / "share.py"
PEOPLE = ["ines", "walt", "aurelie", "tamsin", "harold"]
NAMES = {"ines": "Ines", "walt": "Walt", "aurelie": "Aurelie", "tamsin": "Tamsin",
         "harold": "Harold"}  # fmt: skip

#: Ines's questions, and the answers she writes from what each one serves:
#: (question, the file its cite comes from, the answer, why)
ASKED = [
    ("what storm damage was on the north slope", "johnson/site-visit.md",
     "The storm of 2026-03-03 lifted eleven ridge tiles on the north slope and cracked four.",
     "my site visit of 2026-03-09"),
    ("when did Della Johnson report the leak", "johnson/calls.md",
     "Della Johnson reported the leak on 2026-03-04.",
     "the call log"),
    ("was any work done on the north slope before", "johnson/prior-work.md",
     "No: the only earlier roof work, in 2024, was on the south slope.",
     "the 2024 invoice and her photos agree"),
    ("how much is the roofer's quote", "johnson/quote.md",
     "Hartwell Roofing quotes $2,140, of which $380 is the ceiling.",
     "the quote itself"),
]  # fmt: skip
#: the packages each person kept, by name: each one holds Ines's signed layer
KEPT = {"walt": ["report", "report-v2"],
        "aurelie": ["walt-to-aurelie", "walt-to-aurelie-v2"],
        "tamsin": ["aurelie-to-tamsin", "aurelie-to-tamsin-v2"],
        "harold": ["tamsin-to-harold", "tamsin-to-harold-v2"]}  # fmt: skip
#: what the call log says, which her first report got wrong, and how she asks
#: again: the first question's words would serve her sealed answer
AGAIN = "what day did Della Johnson call to report the leak"
RIGHT = (
    "Della Johnson reported the leak on 2026-03-06, the day after she first saw water."
)


class Scene:
    def __init__(self, life: Path, to: Path, now: datetime):
        self.life, self.to, self.now = life, to, now
        self.pub: dict[str, str] = {}
        self.ids: dict[str, Path] = {}
        self.wrong: list[str] = []
        self.packages: dict[str, str] = {}

    def ts(self) -> str:
        self.now += timedelta(minutes=1)
        return self.now.strftime("%Y-%m-%dT%H:%M:%SZ")

    def run(self, *argv: str, want: tuple[int, ...] = (0,)) -> str:
        got = subprocess.run([sys.executable, *map(str, argv)], capture_output=True,
                             text=True, stdin=subprocess.DEVNULL)  # fmt: skip
        if got.returncode not in want:
            self.wrong.append(f"{Path(str(argv[0])).name} {argv[1]}: exit {got.returncode}"
                              f" {got.stderr.strip()}")  # fmt: skip
        return got.stdout

    def say(self, text: str = "") -> None:
        print(text)

    def box(self, who: str) -> Path:
        return self.to / who / "box"

    def share(self, cmd: str, who: str, *argv: str, want=(0,)) -> str:
        args = ["--box", self.box(who), "--id", self.ids[who], *argv]
        return self.run(SHARE, cmd, *args, "--now", self.ts(), want=want)

    # ── the acts ───────────────────────────────────────────────────────────
    def setup(self) -> None:
        self.to.mkdir()
        for who in PEOPLE:
            (self.to / who).mkdir()
            self.run(KERNEL, "init", "--box", self.box(who), "--pile", self.life / who,
                     "--key", self.to / who / "key", "--now", self.ts())  # fmt: skip
            self.ids[who] = self.to / who / "id"
            self.pub[who] = self.run(SHARE, "id", "--to", self.ids[who]).strip()
            self.say(f"{NAMES[who]:8} box made, identity {self.pub[who][:12]}…")

    def seal(self, question: str, source: str, data: str, claim: str) -> str:
        """Ines asks, writes her answer from what was served, and seals it."""
        bite = json.loads(self.run(KERNEL, "bite", "--box", self.box("ines"), question,
                                   "--now", self.ts(), want=(0, 42)))  # fmt: skip
        cites = [
            s["id"]
            for s in bite.get("served", [])
            if s["where"].startswith(source + ":")
        ]
        if not cites:
            self.wrong.append(f"'{question}' served nothing from {source}")
            return ""
        prop = {"path": f"johnson/{len(self.packages)}-{cites[0][:8]}.md", "data": data,
                "cites": cites[:1], "claim": claim}  # fmt: skip
        sug = self.to / "ines" / "suggestion.jsonl"
        sug.write_text(json.dumps(prop) + "\n")
        out = self.run(KERNEL, "propose", "--box", self.box("ines"), "--file", sug,
                       "--now", self.ts(), want=(42,))  # fmt: skip
        sug.unlink()
        subj = out.split()[1] if out.startswith("pass") else ""
        self.run(KERNEL, "seal", "--box", self.box("ines"), subj, "--now", self.ts())
        self.say(f"  sealed: {data}")
        return subj

    def send(
        self, subjects: list[str], name: str, note: str, replaces: str | None = None
    ) -> str:
        rep = ["--replaces", self.packages[replaces]] if replaces else []
        out = self.share("send", "ines", "--answer", ",".join(subjects), "--for",
                         self.pub["walt"], "--to", self.to / f"{name}.pkg", "--note", note, *rep)  # fmt: skip
        return self.packed(name, out)

    def forward(self, who: str, got: str, to_whom: str, name: str, note: str,
                replaces: str | None = None) -> str:  # fmt: skip
        rep = ["--replaces", self.packages[replaces]] if replaces else []
        out = self.share("forward", who, "--package", self.to / f"{got}.pkg", "--for",
                         self.pub[to_whom], "--to", self.to / f"{name}.pkg", "--note", note, *rep)  # fmt: skip
        return self.packed(name, out)

    def packed(self, name: str, out: str) -> str:
        pid = out.split()[1] if out.startswith("packed ") else ""
        self.packages[name] = pid
        self.say(f"  packed {name}: {pid[:20]}…")
        return pid

    def receive(self, who: str, name: str, want=(0,)) -> str:
        out = self.share(
            "receive", who, "--package", self.to / f"{name}.pkg", want=want
        )
        self.say(f"{NAMES[who]} receives {name}:")
        for line in out.splitlines():
            self.say(f"  {line}")
        return out

    def play(self) -> dict:
        self.say("── the boxes")
        self.setup()

        self.say("\n── 1. Ines seals her answers")
        subjects = [self.seal(*a) for a in ASKED]

        self.say("\n── 2. Walt calls: send me the report on the Johnson case")
        self.send(subjects, "report", "Johnson report, as asked")

        self.say("\n── 3. it goes on, one hop at a time")
        self.receive("walt", "report")
        self.forward(
            "walt", "report", "aurelie", "walt-to-aurelie", "Reviewed, approved"
        )
        self.receive("aurelie", "walt-to-aurelie")
        self.forward("aurelie", "walt-to-aurelie", "tamsin", "aurelie-to-tamsin",
                     "For the file")  # fmt: skip

        self.say("\n── 4. a copy edited on the way")
        good = self.to / "aurelie-to-tamsin.pkg"
        edited = good.read_text(encoding="utf-8").replace("$2,140", "$21,400")
        if edited == good.read_text(encoding="utf-8"):
            self.wrong.append("the edit found no $2,140 to change")
        (self.to / "edited.pkg").write_text(edited, encoding="utf-8")
        bad = self.receive("tamsin", "edited", want=(42,))
        if " broken" not in bad.splitlines()[0]:
            self.wrong.append("the edited copy wasn't refused as broken")
        self.receive("tamsin", "aurelie-to-tamsin")
        self.forward(
            "tamsin", "aurelie-to-tamsin", "harold", "tamsin-to-harold", "Exhibit 4"
        )
        last = self.receive("harold", "tamsin-to-harold")
        if last.count("└ from ") != 3:
            self.wrong.append("Harold doesn't see four layers")

        self.say("\n── 5. the correction follows the same path")
        # the same words would serve her sealed answer first, as the kernel
        # promises, and a sealed answer can't be declined: she asks it anew
        right = self.seal(AGAIN, ASKED[1][1], RIGHT, "the call log, read again")
        self.send([subjects[0], right, *subjects[2:]], "report-v2",
                  "Corrected: the leak was reported on 2026-03-06", replaces="report")  # fmt: skip
        hops = [("walt", "report-v2", "aurelie", "walt-to-aurelie-v2", "walt-to-aurelie"),
                ("aurelie", "walt-to-aurelie-v2", "tamsin", "aurelie-to-tamsin-v2", "aurelie-to-tamsin"),
                ("tamsin", "aurelie-to-tamsin-v2", "harold", "tamsin-to-harold-v2", "tamsin-to-harold")]  # fmt: skip
        for who, got, nxt, name, old in hops:
            said = self.receive(who, got)
            if f"--replaces {self.packages[old]}" not in said:
                self.wrong.append(f"{NAMES[who]} wasn't told where the old one went")
            if (
                who == "aurelie"
                and f"first as {self.pub['walt'][:12]}…, rotated since" not in said
            ):
                self.wrong.append("Aurelie didn't see Walt's new key as Walt's")
            if who == "walt":
                self.rotate("walt", "the laptop was replaced")
            self.forward(who, got, nxt, name, "Replaces what I sent you", replaces=old)
        final = self.receive("harold", "tamsin-to-harold-v2")
        if "you received at row" not in final or RIGHT not in final:
            self.wrong.append("Harold doesn't hold the correction against the old one")

        self.say("\n── 6. the people as witnesses")
        self.witnesses()

        self.say("\n── 7. every chain")
        return self.summary()

    def rotate(self, who: str, why: str) -> None:
        """A new identity, signed by the old one: never a silent swap."""
        new = self.to / who / "id-2"
        key = self.run(SHARE, "rotate", "--box", self.box(who), "--id", self.ids[who],
                       "--to", new, "--now", self.ts()).strip()  # fmt: skip
        self.say(
            f"{NAMES[who]} rotates their key ({why}): {self.pub[who][:12]}… to {key[:12]}…"
        )
        self.ids[who], self.rotated = new, {who: (self.pub[who], key)}

    def witnesses(self) -> None:
        """Each person holds Ines's record to the packages they kept, then to
        a copy of it she rewrote: her first wrong answer's seal backdated and
        every row after it re-hashed, which her own verify can't see."""
        real = self.box("ines")
        fake = self.to / "ines-rewritten"
        shutil.copytree(real, fake)
        rows = [json.loads(x) for x in (fake / "record.jsonl").read_text().splitlines()]
        n = [r["n"] for r in rows if r["kind"] == "seal"][1]  # the 2026-03-04 answer
        rows[n]["ts"] = "2026-03-06T11:00:00Z"
        for i in range(n, len(rows)):
            rows[i]["prev"] = rows[i - 1]["hash"]
            body = {k: v for k, v in rows[i].items() if k != "hash"}
            rows[i]["hash"] = h256(canon(body))
        (fake / "record.jsonl").write_text("".join(canon(r) + "\n" for r in rows))
        said = self.run(KERNEL, "verify", "--box", fake).strip()
        self.say(f"Ines's rewritten copy, by her own verify: {said}")
        if not said.startswith("the chain holds"):
            self.wrong.append("the rewritten copy didn't fool verify")
        self.witness = {}
        for who, kept in KEPT.items():
            pkgs = ",".join(str(self.to / f"{k}.pkg") for k in kept)
            out = {}
            for name, box, want in (("real", real, 0), ("rewritten", fake, 42)):
                got = self.run(
                    SHARE, "witness", "--box", box, "--package", pkgs, want=(want,)
                )
                out[name] = [line.split()[0] for line in got.splitlines()]
                self.say(f"{NAMES[who]:8} on the {name} record:")
                for line in got.splitlines():
                    self.say(f"  {line}")
            if set(out["real"]) != {"holds"} or set(out["rewritten"]) != {"rewritten"}:
                self.wrong.append(
                    f"{NAMES[who]}'s packages didn't tell the two records apart"
                )
            self.witness[who] = out

    def summary(self) -> dict:
        people = {}
        for who in PEOPLE:
            said = self.run(KERNEL, "verify", "--box", self.box(who)).strip()
            rows = [json.loads(line) for line in
                    (self.box(who) / "record.jsonl").read_text().splitlines()]  # fmt: skip
            seals = [r["n"] for r in rows if r["kind"] == "seal"]
            if who != "ines" and seals:
                self.wrong.append(f"{NAMES[who]}'s record holds a seal")
            people[who] = {
                "key": self.pub[who], "verify": said, "rows": len(rows), "seals": len(seals),
                "sent": [r["package"] for r in rows if r["kind"] == "sent"],
                "received": [[r["package"], r["verdict"]] for r in rows
                             if r["kind"] == "received"],
            }  # fmt: skip
            self.say(f"{NAMES[who]:8} {said}")
        doc = {"people": people, "packages": self.packages,
               "witness": getattr(self, "witness", {}), "wrong": self.wrong}  # fmt: skip
        (self.to / "scene.json").write_text(json.dumps(doc, indent=1) + "\n")
        return doc


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2]))
    if (argv[:1] != ["run"] or len(argv) % 2 != 1 or len(opts) != len(argv[1:]) // 2
            or not {"--life", "--to"} <= opts.keys() <= {"--life", "--to", "--now"}):  # fmt: skip
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    life, to = Path(opts["--life"]), Path(opts["--to"])
    if to.exists() or not all((life / who).is_dir() for who in PEOPLE):
        print(
            "refused: --to must be new, and --life what make_life.py wrote",
            file=sys.stderr,
        )
        return 2
    now = datetime.strptime(
        opts.get("--now", "2026-03-12T14:30:00Z"), "%Y-%m-%dT%H:%M:%SZ"
    )
    doc = Scene(life, to, now.replace(tzinfo=timezone.utc)).play()
    for w in doc["wrong"]:
        print(f"WRONG  {w}")
    return 1 if doc["wrong"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
