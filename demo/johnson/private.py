"""private.py: one count over four folders, where the one who asks learns the
total and nothing else. jobs.py's last scene, stacked: wasm, dp, secure-sum.

    python demo/johnson/private.py run --life DIR --to DIR [--epsilon E] [--now TS]

DIR for --life is what make_life.py wrote. Needs wasm's, dp's and
secure-sum's installs (Wasmtime, OpenDP, shamirs). The scene:

1. Ines writes the job once, as WebAssembly: count/count.wasm.b64, built from
   count/src/main.rs, counting what jobs.py's shell job counts (lines naming
   Johnson; lines dated March or April 2026). She seals it and sends it to
   Walt, Aurelie, Tamsin and Harold, with the round: their four keys in that
   order, and a threshold of 3.
2. Each takes it to their door (kart take) and seals it; wasm runs it over
   their own folder, read-only, held to numbers. The tools are the module's
   hash, the same on every machine.
3. Each noises the two numbers with dp (epsilon 1 by default) and seals the
   noisy ones, not the true ones.
4. Each splits the noisy numbers with secure-sum into four shares, seals
   them, and sends each straight to its person; Ines carries none.
5. Each combines the three shares they got with their own, seals the sum
   and sends it to Ines.
6. Ines puts the four sums together, any three of which would do, the
   fourth checking them, and seals the total: everyone's noisy count added
   up. She holds four sums and not one person's number, true or noisy.

It writes a transcript to standard output and private.json under --to.
Exit 0 when the scene plays as told, 1 when a step went otherwise.
"""

from __future__ import annotations

import base64
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from jobs import NAMES, PEOPLE, ROOT, SHARE, Jobs  # noqa: E402

WASM = ROOT / "adapters" / "deps" / "wasm" / "wasm.py"
DP = ROOT / "adapters" / "deps" / "dp" / "dp.py"
SUM = ROOT / "adapters" / "deps" / "secure-sum" / "secure_sum.py"
MODULE = HERE / "count" / "count.wasm.b64"  # the module's bytes, as base64 text
ASKED = ["walt", "aurelie", "tamsin", "harold"]
THRESHOLD = 3


class Private(Jobs):
    def __init__(self, life: Path, to: Path, now: datetime, epsilon: float):
        super().__init__(life, to, now)
        self.epsilon = epsilon

    def tool(self, script: Path, cmd: str, who: str, *argv, ident=True, want=(42,)):
        idf = ["--id", self.to / who / "id"] if ident else []
        return self.run(script, cmd, "--box", self.box(who), *idf, *argv, "--now",
                        self.ts(), want=want)  # fmt: skip

    def sent(self, frm: str, subj: str, to: str, name: str) -> Path:
        pkg = self.to / f"{name}.pkg"
        self.share("send", frm, "--answer", subj, "--for", self.pub[to], "--to", pkg)
        self.share("receive", to, "--package", pkg)
        return pkg

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
        among = ",".join(self.pub[w] for w in ASKED)
        print("── 1. Ines writes the job once, as WebAssembly")
        text = "wasm:" + "".join(MODULE.read_text().split())
        job = self.seal_own("ines", "job count johnson and spring as wasm", {
            "path": "jobs/count.wasm", "data": text, "cites": [],
            "claim": "two counts a folder, as count/src/main.rs: Johnson lines, spring 2026 lines"})  # fmt: skip
        print(
            f"  count.wasm, {len(base64.b64decode(text[5:]))} bytes; the round: {len(ASKED)} keys, threshold {THRESHOLD}"
        )
        shares: dict[str, list[str]] = {w: [] for w in ASKED}
        self.doc.update(true={}, noisy={}, tools=set())
        for who in ASKED:
            pkg = self.sent("ines", job, who, f"job-{who}")
            out = self.kart(
                "take", who, "--package", pkg, "--words", "ines asks a count, privately"
            )
            taken = out.split()[1] if out.startswith("taken") else ""
            self.kernel(who, "seal", taken)
            out = self.tool(WASM, "run", who, "--job", taken, "--to", self.to / f"{who}.txt",
                            "--shape", "numbers", ident=False)  # fmt: skip
            result = next(
                (x.split()[1] for x in out.splitlines() if x.startswith("result")), ""
            )
            ran = [json.loads(x) for x in (self.box(who) / "record.jsonl").read_text().splitlines()
                   if '"kind":"ran"' in x][-1]  # fmt: skip
            self.doc["tools"].add(json.dumps(ran["tools"]))
            self.doc["true"][who] = (self.to / f"{who}.txt").read_text().split()
            out = self.tool(DP, "noise", who, "--result", result, "--epsilon", str(self.epsilon),
                            ident=False)  # fmt: skip
            noisy = next(
                (x.split()[1] for x in out.splitlines() if x.startswith("noisy")), ""
            )
            self.kernel(who, "seal", noisy)
            prop = json.loads(
                (self.box(who) / "proposals" / f"{noisy[9:]}.json").read_text()
            )
            self.doc["noisy"][who] = prop["data"].split()
            out = self.tool(SUM, "split", who, "--result", noisy, "--among", among,
                            "--threshold", str(THRESHOLD))  # fmt: skip
            subjs = [
                x.split()[1] for x in out.splitlines() if x.strip().startswith("share ")
            ]
            for subj, to in zip(subjs, [w for w in ASKED if w != who]):
                self.kernel(who, "seal", subj)
                shares[to].append(str(self.sent(who, subj, to, f"share-{who}-{to}")))
            print(f"  {NAMES[who]:8} ran it (wasm), true {' '.join(self.doc['true'][who])}, "
                  f"sealed noisy {' '.join(self.doc['noisy'][who])}, split into {len(subjs) + 1}")  # fmt: skip
        print("\n── 5. each adds the shares they hold, and sends Ines the sum")
        sums = []
        for who in ASKED:
            out = self.tool(SUM, "combine", who, "--package", ",".join(shares[who]))
            subj = next(
                (x.split()[1] for x in out.splitlines() if x.startswith("sum")), ""
            )
            self.kernel(who, "seal", subj)
            sums.append(str(self.sent(who, subj, "ines", f"sum-{who}")))
        print(
            f"  {len(sums)} sums sent; {sum(map(len, shares.values()))} shares went person to person"
        )
        print("\n── 6. Ines puts them together")
        out = self.tool(SUM, "total", "ines", "--among", among, "--package", ",".join(sums),
                        ident=False)  # fmt: skip
        line = next(
            (x for x in out.splitlines() if "total " in x and "folders" in x), ""
        )
        subj = out.splitlines()[-1].split()[1] if out.startswith("  ") else ""
        self.kernel("ines", "seal", subj)
        total = line.split()[1:3]
        print(f"  {line.strip()}")
        true = [sum(int(self.doc["true"][w][k]) for w in ASKED) for k in range(2)]
        noisy = [sum(int(self.doc["noisy"][w][k]) for w in ASKED) for k in range(2)]
        print(
            f"  the true total is {true[0]} {true[1]}; the noisy one, {total[0]} {total[1]}"
        )
        if list(map(int, total)) != noisy:
            self.wrong.append(
                f"the total {total} isn't the noisy numbers added up, {noisy}"
            )
        if len(self.doc["tools"]) != 1:
            self.wrong.append(
                f"the module ran on {len(self.doc['tools'])} sets of tools"
            )
        held = "".join(p.read_text() for p in self.to.glob("*.pkg")
                       if p.name.startswith(("sum-", "job-")))  # fmt: skip
        ines = [
            json.loads(x)
            for x in (self.box("ines") / "record.jsonl").read_text().splitlines()
        ]
        got = [r for r in ines if r["kind"] == "received"]
        if len(got) != len(ASKED):
            self.wrong.append(
                f"Ines received {len(got)} packages, not {len(ASKED)} sums"
            )
        self.doc.update(total=total, true_total=true, noisy_total=noisy,
                        tools=sorted(self.doc["tools"]), ines_received=len(got),
                        package_chars=len(held))  # fmt: skip
        print("\n── every chain")
        for who in PEOPLE:
            said = self.run(
                ROOT / "kernel.py", "verify", "--box", self.box(who)
            ).strip()
            print(f"  {NAMES[who]:8} {said}")
            if not said.startswith("the chain holds"):
                self.wrong.append(f"{who}'s chain: {said}")
        spent = (
            self.run(DP, "spent", "--box", self.box("walt")).strip().splitlines()[-1]
        )
        print(f"  Walt's dp spent: {spent}")
        self.doc["wrong"] = self.wrong
        (self.to / "private.json").write_text(json.dumps(self.doc, indent=1) + "\n")
        return self.doc


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2]))
    allowed = {"--life", "--to", "--now", "--epsilon"}
    if (argv[:1] != ["run"] or len(argv) % 2 != 1 or len(opts) != len(argv[1:]) // 2
            or not {"--life", "--to"} <= opts.keys() <= allowed):  # fmt: skip
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
    doc = Private(life, to, now, float(opts.get("--epsilon", "1"))).play()
    for w in doc["wrong"]:
        print(f"WRONG  {w}")
    return 1 if doc["wrong"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
