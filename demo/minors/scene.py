"""scene.py: four minors, each standing somewhere different to their own box.

    python demo/minors/scene.py run --life DIR --to DIR [--now TS]

DIR for --life is what make_life.py wrote: one folder a box. Each gets a
box under --to, which must not be there yet, and a key in the folder of
whoever holds it. Nobody here is real. Then the scene:

1. **Held for her.** Wren is six. Her box is hers and its key is her
   mother's: Marit asks it what Wren is allergic to and seals the answer
   with the same key that holds her own box.
2. **Held for him, and one of his own.** Tobias is fourteen. Marit holds
   a box of his ordinary records. He keeps a second box on a key of his
   own, for care he asked for himself. Asked about it, every box Marit
   holds finds nothing, and no row of theirs names his. His seal proves
   under his key and not under hers.
3. **Handed over.** Imani is eighteen tomorrow. Marit seals what the box
   she held can say, packs it for Imani's key, and hands her the files.
   Imani starts a box of her own, receives the package, and seals her own
   answer. The box Marit held stays Marit's record of what she did, and
   what Imani was sent says where that record stood: a copy of it
   rewritten afterwards still verifies alone, and does not hold to it.
4. **Between two houses.** Leo is ten. His box is held by his mother,
   Dana. His father Ravi keeps his own box of nights at his, seals what
   happened on one of them and sends it to Leo's box: the answer and
   where it came from arrive, and Ravi's notes never do.
5. Every box is verified.

Willow has no word for a box held on someone else's behalf. The scene
writes one, to see what it would have to say: a row of kind `held-for`
on each held box (whose it is, and until when), and `handed-over` when
it changes hands. Both are this demo's, and a proposal.

It prints what happened and writes scene.json under --to. Exit 0 when
the scene plays as told, 1 when a step went otherwise, 2 a bad command.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

KERNEL = ROOT / "kernel.py"
SHARE = ROOT / "adapters" / "stdlib" / "share" / "share.py"
USAGE = __doc__.split("\n\n")[1]

#: each box at the start: (whose it is, who holds its key, held until)
BOXES = {
    "marit": ("Marit", "marit", None),
    "wren": ("Wren", "marit", "2038-04-02"),
    "tobias": ("Tobias", "marit", "2030-07-19"),
    "tobias-own": ("Tobias", "tobias", None),
    "imani": ("Imani", "marit", "2026-11-13"),
    "leo": ("Leo", "dana", "2034-02-11"),
    "ravi": ("Ravi", "ravi", None),
}
HIS = "when is the next counselling session"


class Scene:
    def __init__(self, life: Path, to: Path, now: datetime):
        self.life, self.to, self.now = life, to, now
        self.wrong: list[str] = []
        self.ids: dict[str, Path] = {}
        self.pub: dict[str, str] = {}
        self.holder = {name: holder for name, (_, holder, _) in BOXES.items()}
        self.said: dict = {}

    def ts(self) -> str:
        self.now += timedelta(minutes=1)
        return self.now.strftime("%Y-%m-%dT%H:%M:%SZ")

    def run(self, *argv, want=(0,)) -> str:
        got = subprocess.run([sys.executable, *map(str, argv)], capture_output=True,
                             text=True, stdin=subprocess.DEVNULL)  # fmt: skip
        if got.returncode not in want:
            self.wrong.append(f"{Path(str(argv[0])).name} {argv[1]}: exit {got.returncode} {got.stderr.strip()}")  # fmt: skip
        return got.stdout

    def box(self, name: str) -> Path:
        return self.to / "boxes" / name

    def key(self, name: str) -> Path:
        return self.to / "keys" / f"{self.holder[name]}.key"

    def expect(self, ok: bool, what: str) -> None:
        if not ok:
            self.wrong.append(what)

    def start(self, name: str, pile: Path) -> None:
        self.key(name).parent.mkdir(parents=True, exist_ok=True)
        self.run(KERNEL, "init", "--box", self.box(name), "--pile", pile,
                 "--key", self.key(name), "--now", self.ts())  # fmt: skip
        self.ids[name] = self.to / "ids" / name
        self.ids[name].parent.mkdir(exist_ok=True)
        self.pub[name] = self.run(SHARE, "id", "--to", self.ids[name]).strip()

    def ask(self, name: str, question: str) -> dict:
        out = self.run(KERNEL, "bite", "--box", self.box(name), question,
                       "--now", self.ts(), want=(0, 42))  # fmt: skip
        return json.loads(out)

    def seal(self, name: str, question: str, source: str, data: str, claim: str) -> str:
        """Whoever holds the box asks it, writes the answer from what was
        served, and seals it with the key they hold."""
        cites = [s["id"] for s in self.ask(name, question).get("served", [])
                 if s["where"].startswith(source + ":")]  # fmt: skip
        if not cites:
            self.wrong.append(f"{name}: '{question}' served nothing from {source}")
            return ""
        sug = self.to / "suggestion.jsonl"
        sug.write_text(json.dumps({"path": f"answers/{cites[0][:8]}.md", "data": data,
                                   "cites": cites[:1], "claim": claim}) + "\n")  # fmt: skip
        out = self.run(KERNEL, "propose", "--box", self.box(name), "--file", sug,
                       "--now", self.ts(), want=(42,))  # fmt: skip
        sug.unlink()
        subj = out.split()[1] if out.startswith("pass") else ""
        self.run(KERNEL, "seal", "--box", self.box(name), subj, "--now", self.ts())
        print(f"  {self.holder[name]} seals in {name}: {data}")
        return subj

    def rows(self, name: str) -> list[dict]:
        return kernel.read(self.box(name) / "record.jsonl")[0]

    def proves(self, name: str, key: Path) -> int:
        """How many of a box's seals hold under a key."""
        copy = self.to / "probe"
        shutil.copytree(self.box(name), copy)
        cfg = json.loads((copy / "kernel.json").read_text())
        cfg["key"] = str(key)
        (copy / "kernel.json").write_text(json.dumps(cfg, sort_keys=True) + "\n")
        try:
            return len(kernel.sealed(copy, kernel.read(copy / "record.jsonl")[0]))
        finally:
            shutil.rmtree(copy)

    # ── the scene ──────────────────────────────────────────────────────────
    def play(self) -> dict:
        self.to.mkdir()
        (self.to / "boxes").mkdir()
        print("── the boxes")
        for name, (whose, holder, until) in BOXES.items():
            self.start(name, self.life / name)
            if until:
                kernel.append(self.box(name), self.ts(), "held-for", who="minors",
                              **{"for": whose, "by": holder, "until": until})  # fmt: skip
            held = (
                f"held by {holder} until {until}" if until else f"on {holder}'s own key"
            )
            print(f"  {name:11} {whose}'s box, {held}")

        print("── 1. held for her: Wren, six")
        self.seal("wren", "what is Wren allergic to", "allergies.md",
                  "Wren is allergic to peanuts and carries an adrenaline pen.",
                  "her allergy page")  # fmt: skip
        same = self.key("wren") == self.key("marit")
        self.expect(same, "Wren's box is not on the key that holds Marit's own")
        self.said["wren"] = {
            "seals": self.proves("wren", self.key("wren")),
            "same_key": same,
        }

        print("── 2. held for him, and one of his own: Tobias, fourteen")
        self.seal("tobias", "when was the tetanus booster", "immunizations.md",
                  "Tobias had a tetanus booster on 2024-08-12.", "the clinic's printout")  # fmt: skip
        found = {name: self.ask(name, HIS)["state"] for name in ("marit", "wren", "tobias", "imani", "tobias-own")}  # fmt: skip
        for name, state in found.items():
            print(f"  asked '{HIS}': {name} says {state}")
        self.expect(
            found.pop("tobias-own") == "populated", "his own box did not answer"
        )
        self.expect(
            set(found.values()) == {"empty"}, f"a box Marit holds answered: {found}"
        )
        self.seal("tobias-own", HIS, "visits.md",
                  "My next counselling session is 2026-11-17 at four.", "my own notes")  # fmt: skip
        named = [name for name in ("marit", "wren", "tobias", "imani")
                 if "tobias-own" in json.dumps(self.rows(name))
                 or "counselling" in json.dumps(self.rows(name))]  # fmt: skip
        self.expect(not named, f"a box Marit holds names his: {named}")
        his, hers = self.proves("tobias-own", self.key("tobias-own")), self.proves("tobias-own", self.key("marit"))  # fmt: skip
        print(f"  his seal proves under his key: {his}; under Marit's: {hers}")
        self.expect((his, hers) == (1, 0), "his seal did not prove under his key alone")
        self.said["tobias"] = {"found": found, "named_by": named, "his_key": his, "her_key": hers}  # fmt: skip

        print("── 3. handed over: Imani, eighteen tomorrow")
        sealed = [
            self.seal("imani", "which immunizations has Imani had", "immunizations.md",
                      "Imani has had MMR twice, HPV twice and meningitis ACWY; the last is from memory.",
                      "her card and the clinic's printout; the meningitis card is lost"),
            self.seal("imani", "does Imani have a known allergy", "allergies.md",
                      "Imani has no known allergy; penicillin gave her a rash in 2019.",
                      "her allergy page"),
        ]  # fmt: skip
        self.holder["imani-own"] = "imani"
        shutil.copytree(self.life / "imani", self.to / "handed" / "imani")
        self.start("imani-own", self.to / "handed" / "imani")
        pkg = self.to / "imani-handover.pkg"
        out = self.run(SHARE, "send", "--box", self.box("imani"), "--id", self.ids["imani"],
                       "--answer", ",".join(sealed), "--for", self.pub["imani-own"], "--to", pkg,
                       "--note", "Yours from today. What I kept for you, and how I knew it.",
                       "--now", self.ts())  # fmt: skip
        pid = out.split()[1] if out.startswith("packed ") else ""
        kernel.append(self.box("imani"), self.ts(), "handed-over", who="minors",
                      **{"for": "Imani", "to": self.pub["imani-own"], "package": pid})  # fmt: skip
        got = self.run(SHARE, "receive", "--box", self.box("imani-own"), "--id",
                       self.ids["imani-own"], "--package", pkg, "--now", self.ts())  # fmt: skip
        print("  Imani receives the handover:")
        for line in got.splitlines():
            print(f"    {line}")
        before = self.proves("imani-own", self.key("imani-own"))
        self.expect(before == 0, "what Imani received counted as her own seal")
        self.seal("imani-own", "does Imani have a known allergy", "allergies.md",
                  "I have no known allergy. Penicillin gave me a rash once.", "my allergy page")  # fmt: skip
        kinds = [r["kind"] for r in self.rows("imani")]
        self.expect(kinds[-1] == "handed-over" and "sent" in kinds, "the held box does not say it was handed over")  # fmt: skip
        self.said["imani"] = {
            "held_box_seals": self.proves("imani", self.key("imani")),
            "own_box_seals": self.proves("imani-own", self.key("imani-own")),
            "received": [r["kind"] for r in self.rows("imani-own")].count("received"),
            "held_box_ends": kinds[-1],
        }
        # the link: what Imani was sent says where her mother's record stood,
        # so she can hold that record to it from then on
        fake = self.to / "imani-rewritten"
        shutil.copytree(self.box("imani"), fake)
        rows = [json.loads(x) for x in (fake / "record.jsonl").read_text().splitlines()]
        n = next(r["n"] for r in rows if r["kind"] == "seal")
        rows[n]["ts"] = "2019-06-01T10:00:00Z"
        for i in range(n, len(rows)):
            rows[i]["prev"] = rows[i - 1]["hash"]
            rows[i]["hash"] = kernel.h256(kernel.canon({k: v for k, v in rows[i].items() if k != "hash"}))  # fmt: skip
        (fake / "record.jsonl").write_text(
            "".join(kernel.canon(r) + "\n" for r in rows)
        )
        fooled = (
            self.run(KERNEL, "verify", "--box", fake)
            .strip()
            .startswith("the chain holds")
        )
        self.expect(fooled, "the rewritten copy did not pass its own verify")
        held = {}
        for name, box, want in (
            ("as it was", self.box("imani"), 0),
            ("rewritten", fake, 42),
        ):
            got = self.run(
                SHARE, "witness", "--box", box, "--package", pkg, want=(want,)
            )
            held[name] = [line.split()[0] for line in got.splitlines()]
            print(f"  Imani holds the record her mother kept, {name}, to what she was sent: {' '.join(held[name])}")  # fmt: skip
        self.expect(held == {"as it was": ["holds"], "rewritten": ["rewritten"]}, f"the package did not tell the two apart: {held}")  # fmt: skip
        self.said["imani"]["rewritten_copy_verifies_alone"] = fooled
        self.said["imani"]["held_to_the_package"] = held
        shutil.rmtree(fake)

        print("── 4. between two houses: Leo, ten")
        night = self.seal("ravi", "what happened when Leo's asthma flared", "leo-nights.md",
                          "Leo's asthma flared about eleven at night on 2026-11-08; four puffs of the blue inhaler settled it, no clinic.",
                          "my note of that night")  # fmt: skip
        pkg = self.to / "ravi-to-leo.pkg"
        self.run(SHARE, "send", "--box", self.box("ravi"), "--id", self.ids["ravi"],
                 "--answer", night, "--for", self.pub["leo"], "--to", pkg,
                 "--note", "For Leo's record: the flare at mine on the eighth.", "--now", self.ts())  # fmt: skip
        got = self.run(SHARE, "receive", "--box", self.box("leo"), "--id", self.ids["leo"],
                       "--package", pkg, "--now", self.ts())  # fmt: skip
        print("  Dana receives it into Leo's box:")
        for line in got.splitlines():
            print(f"    {line}")
        text = pkg.read_text(encoding="utf-8") + json.dumps(self.rows("leo"))
        carried = "Told Dana by text" in text or "He slept through" in text
        self.expect(not carried, "Ravi's notes travelled with his answer")
        self.said["leo"] = {
            "received": [r["kind"] for r in self.rows("leo")].count("received"),
            "ravis_notes_travelled": carried,
            "leo_box_seals": self.proves("leo", self.key("leo")),
        }

        print("── 5. every box")
        table = {}
        for name in [*BOXES, "imani-own"]:
            out = self.run(KERNEL, "verify", "--box", self.box(name)).strip()
            rows = self.rows(name)
            held = next((r for r in rows if r["kind"] == "held-for"), None)
            table[name] = {"holder": self.holder[name], "rows": len(rows),
                           "seals": self.proves(name, self.key(name)),
                           "held_for": held and held["for"], "verify": out}  # fmt: skip
            print(f"  {name:11} {out}; key held by {self.holder[name]}")
            self.expect(out.startswith("the chain holds"), f"{name} does not verify")
        doc = {"boxes": table, "said": self.said, "wrong": self.wrong}
        (self.to / "scene.json").write_text(
            json.dumps(doc, indent=1, sort_keys=True) + "\n"
        )
        return doc


def main(argv: list[str]) -> int:
    opts: dict = {}
    it = iter(argv[1:])
    for a in it:
        if a in ("--life", "--to", "--now") and a[2:] not in opts:
            opts[a[2:]] = next(it, "")
        else:
            opts = {}
            break
    if argv[:1] != ["run"] or not opts.get("life") or not opts.get("to"):
        print(USAGE, file=sys.stderr)
        return 2
    life, to = Path(opts["life"]), Path(opts["to"]).resolve()
    if not (life / "wren").is_dir() or to.exists() or to.is_relative_to(ROOT):
        print("refused: --life is what make_life.py wrote; --to is new and outside the repository", file=sys.stderr)  # fmt: skip
        return 2
    now = datetime.strptime(opts.get("now") or "2026-11-12T09:00:00Z", "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)  # fmt: skip
    doc = Scene(life, to, now).play()
    for line in doc["wrong"]:
        print(f"went otherwise: {line}")
    return 1 if doc["wrong"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
