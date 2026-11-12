"""tense.py: a third set, where the minor and the one who cares for them
are at odds.

    python demo/minors/tense.py run --life DIR --to DIR

DIR for --life is what make_life.py wrote. Nobody here is real. Two
stories, pulling opposite ways:

1. **A guardian who reads everything.** Sable is fifteen. Her stepfather
   Garrick is her guardian, holds her box, and goes to every appointment.
   She asked the school nurse to see her alone. Garrick asks the box he
   holds about it, three ways: it has nothing, and each asking is a row
   on its record. The nurse sends what she wrote to a box that is Sable's
   own, kept at her aunt's. Her seal proves under her key and not under
   his. Then the scene puts her box in his hands, and it answers him:
   a key says who approved, not who may ask.
2. **A guardian replaced, who does not hand over.** A court makes her
   aunt Bryony her guardian. Garrick hands nothing over, so Bryony
   starts a box from the little she has. He goes on sealing in the old
   one. Both boxes say they are held for Sable; both verify.
3. **A wall that shuts out someone who cares.** Kit is sixteen, has
   diabetes, and stopped showing the numbers to a grandmother who is
   frightened for them. Rosa's box has the clinic's letter and no
   numbers, and says so exactly as Garrick's did. Then Kit seals one
   sentence and sends it to her: the wall opens from Kit's side only.
4. Every box is verified.

It prints what happened and writes tense.json under --to. Exit 0 when the
scene plays as told, 1 when a step went otherwise, 2 a bad command.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scene  # noqa: E402
from scene import KERNEL, ROOT, SHARE, kernel  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
#: each box at the start: (whose it is, who holds its key, held until)
BOXES = {
    "garrick": ("Garrick", "garrick", None),
    "sable": ("Sable", "garrick", "2029-03-08"),
    "sable-own": ("Sable", "sable", None),
    "nurse": ("Tunde", "tunde", None),
    "bryony": ("Bryony", "bryony", None),
    "kit": ("Kit", "rosa", "2028-06-30"),
    "kit-own": ("Kit", "kit", None),
}
HIS_ASKS = (
    "what did the school nurse say to Sable",
    "was Sable seen alone",
    "what did Sable tell the nurse",
)
ORDER = "2026-11-10"


def at(day: str) -> datetime:
    return datetime.strptime(day, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


class Tense(scene.Scene):
    def __init__(self, life: Path, to: Path):
        super().__init__(life, to, at("2026-11-03T18:00:00Z"))
        self.holder = {name: holder for name, (_, holder, _) in BOXES.items()}

    def send(self, frm: str, subj: str, to: str, name: str, note: str) -> str:
        pkg = self.to / f"{name}.pkg"
        self.run(SHARE, "send", "--box", self.box(frm), "--id", self.ids[frm], "--answer", subj,
                 "--for", self.pub[to], "--to", pkg, "--note", note, "--now", self.ts())  # fmt: skip
        got = self.run(SHARE, "receive", "--box", self.box(to), "--id", self.ids[to],
                       "--package", pkg, "--now", self.ts())  # fmt: skip
        for line in got.splitlines():
            print(f"    {line}")
        return pkg.read_text(encoding="utf-8")

    def kinds(self, name: str) -> list[str]:
        return [r["kind"] for r in self.rows(name)]

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

        print("── 1. a guardian who reads everything: Sable, fifteen")
        self.seal("sable", "who was in the room at the doctor", "appointments.md",
                  "I was in the room for all of Sable's appointment on 2026-10-14.",
                  "the appointments page I keep")  # fmt: skip
        found = {q: self.ask("sable", q)["state"] for q in HIS_ASKS}
        for q, state in found.items():
            print(f"  Garrick asks the box he holds, '{q}': {state}")
        self.expect(
            set(found.values()) == {"empty"}, f"the box he holds answered: {found}"
        )
        asks = [r for r in self.rows("sable") if r["kind"] == "bite"]
        keys = {r["bite_key"] for r in asks}
        guessed = kernel.bite_key(HIS_ASKS[0]) in keys
        missed = kernel.bite_key("what is for dinner") in keys
        print(f"  his askings on that record: {len(asks)}; a right guess of one is confirmed: {guessed}; a wrong guess: {missed}")  # fmt: skip
        self.expect(guessed and not missed, "an asking could not be told from a guess")
        words = json.dumps(self.rows("sable")).lower()
        self.expect(
            "nurse" not in words and "alone" not in words, "the record holds his words"
        )

        note = self.seal("nurse", "was Sable seen without her guardian", "school-notes.md",
                         "On 2026-10-21 Sable asked to be seen without her guardian and was seen alone at school.",
                         "my note of that day")  # fmt: skip
        print("  the nurse sends it to Sable's own box, and nothing to the house:")
        self.send("nurse", note, "sable-own", "nurse-to-sable", "For you. Nothing goes to the house unless you say.")  # fmt: skip
        self.expect("received" not in self.kinds("sable") and "received" not in self.kinds("garrick"),
                    "something reached a box Garrick holds")  # fmt: skip
        self.seal("sable-own", "who should be called first", "emergency-card.md",
                  "Call my aunt, Bryony Okonjo, first.", "the card I wrote")  # fmt: skip
        hers, his = self.proves("sable-own", self.key("sable-own")), self.proves("sable-own", self.key("sable"))  # fmt: skip
        print(f"  her seal proves under her key: {hers}; under Garrick's: {his}")
        self.expect((hers, his) == (1, 0), "her seal did not prove under her key alone")
        cards = [
            (self.life / b / "emergency-card.md").read_text()
            for b in ("sable", "sable-own")
        ]
        differ = (
            "Call first: Garrick Hart." in cards[0]
            and "Call first: Bryony Okonjo" in cards[1]
        )
        print(
            f"  two emergency cards for one girl name two people to call first: {differ}"
        )
        in_his_hands = self.ask("sable-own", "was Sable seen alone")["state"]
        print(
            f"  her box, if it were in his hands, asked 'was Sable seen alone': {in_his_hands}"
        )
        self.expect(
            in_his_hands == "populated", "her box did not answer whoever held it"
        )
        self.said["sable"] = {
            "his_asks": len(asks), "found": sorted(set(found.values())), "guess_confirmed": guessed,
            "her_key": hers, "his_key": his, "cards_differ": differ,
            "answers_whoever_holds_it": in_his_hands == "populated",
        }  # fmt: skip

        print("── 2. a guardian replaced, who does not hand over")
        self.now = at(f"{ORDER}T12:00:00Z")
        self.holder["sable-with-bryony"] = "bryony"
        self.start("sable-with-bryony", self.life / "sable-with-bryony")
        kernel.append(self.box("sable-with-bryony"), self.ts(), "held-for", who="minors",
                      **{"for": "Sable", "by": "bryony", "until": "2029-03-08", "on": f"order of {ORDER}"})  # fmt: skip
        self.seal("sable-with-bryony", "which doses are on the photograph of her card", "immunizations.md",
                  "The photograph shows two MMR doses and nothing after 2016.",
                  "all I have of her papers")  # fmt: skip
        self.now = at("2026-11-12T09:00:00Z")
        self.seal("sable", "what was the doctor's appointment for", "appointments.md",
                  "The doctor saw Sable for a sore throat and gave antibiotics.",
                  "the appointments page I keep")  # fmt: skip
        after = [r for r in self.rows("sable") if r["kind"] == "seal" and r["ts"] > f"{ORDER}T23:59:59Z"]  # fmt: skip
        claim = [n for n in ("sable", "sable-with-bryony")
                 if any(r["kind"] == "held-for" and r["for"] == "Sable" for r in self.rows(n))]  # fmt: skip
        handed = "handed-over" in self.kinds("sable")
        print(f"  boxes that say they are held for Sable: {', '.join(claim)}")
        print(
            f"  seals Garrick made in the old one after the order: {len(after)}; handed over: {handed}"
        )
        print("  doses Bryony's box knows of: 2; Garrick's: 3")
        self.expect(
            len(after) == 1 and len(claim) == 2 and not handed,
            "the old box was not as told",
        )
        self.said["guardian"] = {
            "claim_to_hold": claim, "old_holder_seals_after_order": len(after), "handed_over": handed,
            "old_box_seals": self.proves("sable", self.key("sable")),
            "new_box_seals": self.proves("sable-with-bryony", self.key("sable-with-bryony")),
        }  # fmt: skip

        print("── 3. a wall that shuts out someone who cares: Kit, sixteen")
        ask = "what were Kit's glucose readings"
        before = self.ask("kit", ask)["state"]
        print(f"  Rosa asks the box she holds, '{ask}': {before}")
        self.expect(before == "empty", "the box Rosa holds had the numbers")
        said = self.seal("kit-own", "how many glucose readings did I take in October", "meter.md",
                         "In October I took 11 glucose readings; the plan asks for four a day.",
                         "my own count")  # fmt: skip
        print("  Kit sends that one sentence to the box Rosa holds:")
        package = self.send("kit-own", said, "kit", "kit-to-rosa", "Gran, this is where I am. I want help, not a row.")  # fmt: skip
        carried = "argument" in package or "going wrong" in package
        self.expect(not carried, "Kit's own words travelled with the sentence")
        self.said["kit"] = {
            "before": before, "received": self.kinds("kit").count("received"),
            "kits_notes_travelled": carried,
            "rosa_asked_again": self.ask("kit", ask)["state"],
        }  # fmt: skip
        print(f"  Rosa asks again: {self.said['kit']['rosa_asked_again']}. What came is on her record as received, and is not in her files")  # fmt: skip

        print("── 4. every box")
        table = {}
        for name in [*BOXES, "sable-with-bryony"]:
            out = self.run(KERNEL, "verify", "--box", self.box(name)).strip()
            table[name] = {"holder": self.holder[name], "verify": out,
                           "seals": self.proves(name, self.key(name))}  # fmt: skip
            print(f"  {name:18} {out}; key held by {self.holder[name]}")
            self.expect(out.startswith("the chain holds"), f"{name} does not verify")
        doc = {"boxes": table, "said": self.said, "wrong": self.wrong}
        (self.to / "tense.json").write_text(
            json.dumps(doc, indent=1, sort_keys=True) + "\n"
        )
        return doc


def main(argv: list[str]) -> int:
    if len(argv) != 5 or argv[0] != "run" or {argv[1], argv[3]} != {"--life", "--to"}:
        print(USAGE, file=sys.stderr)
        return 2
    opts = {argv[1]: argv[2], argv[3]: argv[4]}
    life, to = Path(opts["--life"]), Path(opts["--to"]).resolve()
    if not (life / "sable").is_dir() or to.exists() or to.is_relative_to(ROOT):
        print("refused: --life is what make_life.py wrote; --to is new and outside the repository", file=sys.stderr)  # fmt: skip
        return 2
    doc = Tense(life, to).play()
    for line in doc["wrong"]:
        print(f"went otherwise: {line}")
    return 1 if doc["wrong"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
