"""fourteen.py: Leo four years on, with a box of his own beside the one
held for him across two houses.

    python demo/wards/fourteen.py run --life DIR --to DIR

DIR for --life is what make_life.py wrote. Nobody here is real. At ten
Leo had one box, held by his mother, and his father added to it by
sending. At fourteen:

1. **He is the only one who has all of it.** His mother Dana still holds
   his box. His father Ravi still keeps his own notes. Each sends Leo's
   own box what they know of his preventer inhaler, and they do not
   agree: one says purple, one puff; the other brown, two. Neither
   parent's box holds the other's word. His does.
2. **He is seen alone, and decides what goes where.** He has counted how
   often he needs his reliever at each house, and why. The asthma nurse
   sees him alone and sends her note to his box only. He seals two
   things: the plan, which he sends to his father, and the count, which
   he sends to the box his mother holds. The count never reaches his
   father.
3. **He can already hold them to it.** Each parent's record is held to
   what that parent sent him, four years before any handover.
4. Every box is verified.

It prints what happened and writes fourteen.json under --to. Exit 0 when
the scene plays as told, 1 when a step went otherwise, 2 a bad command.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tense  # noqa: E402
from scene import KERNEL, ROOT, SHARE, kernel  # noqa: E402
from tense import at  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
#: each box: (whose it is, who holds its key, held until)
BOXES = {
    "leo-at-fourteen": ("Leo", "dana", "2034-02-11"),
    "ravi-later": ("Ravi", "ravi", None),
    "leo-own": ("Leo", "leo", None),
    "asthma-nurse": ("the asthma nurse", "nurse", None),
}


class Fourteen(tense.Tense):
    def __init__(self, life: Path, to: Path):
        super().__init__(life, to)
        self.now = at("2030-10-19T10:00:00Z")
        self.holder = {name: holder for name, (_, holder, _) in BOXES.items()}

    def got(self, name: str) -> dict[str, int]:
        """{who it came from: how many packages}, as a box's record has it."""
        who = {pub: box for box, pub in self.pub.items()}
        out: dict[str, int] = {}
        for r in self.rows(name):
            if r["kind"] == "received" and r.get("verdict") == "good":
                out[who[r["from"]]] = out.get(who[r["from"]], 0) + 1
        return out

    def text(self, name: str) -> str:
        return (self.to / f"{name}.pkg").read_text(encoding="utf-8")

    def play(self) -> dict:
        self.to.mkdir()
        (self.to / "boxes").mkdir()
        print("── the boxes")
        for name, (whose, holder, until) in BOXES.items():
            self.start(name, self.life / name)
            if until:
                kernel.append(self.box(name), self.ts(), "held-for", who="wards",
                              **{"for": whose, "by": holder, "until": until})  # fmt: skip
            held = (
                f"held by {holder} until {until}" if until else f"on {holder}'s own key"
            )
            print(f"  {name:16} {whose}'s box, {held}")

        print("── 1. the only one who has all of it")
        hers = self.seal("leo-at-fourteen", "which preventer inhaler is Leo on", "asthma.md",
                         "Since the review of 2030-09-02 Leo is on the purple inhaler, one puff morning and night.",
                         "the review I took him to")  # fmt: skip
        his = self.seal("ravi-later", "which inhaler does Leo take at mine", "leo.md",
                        "At mine Leo takes the brown inhaler, two puffs morning and night; nobody has told me of a change.",
                        "what I have always given him")  # fmt: skip
        self.pack("leo-at-fourteen", hers, "leo-own", "dana-to-leo", "For your own box, now you have one.")  # fmt: skip
        self.pack(
            "ravi-later", his, "leo-own", "ravi-to-leo", "So you have it from me too."
        )
        print("  each parent sends Leo's own box what they know:")
        self.receive("leo-own", "dana-to-leo", quiet=True)
        self.receive("leo-own", "ravi-to-leo", quiet=True)
        differ = "purple inhaler, one puff" in self.text("dana-to-leo") and "brown inhaler, two puffs" in self.text("ravi-to-leo")  # fmt: skip
        across = self.got("leo-at-fourteen").get("ravi-later", 0) + self.got("ravi-later").get("leo-at-fourteen", 0)  # fmt: skip
        print(f"  the two disagree about his preventer: {differ}; packages either parent's box has from the other: {across}")  # fmt: skip
        self.expect(differ and across == 0, "the disagreement was not his alone to see")

        print("── 2. seen alone, and deciding what goes where")
        self.now = at("2030-10-21T16:00:00Z")
        note = self.seal("asthma-nurse", "what is the plan for Leo's preventer", "notes.md",
                         "The plan stands: the purple preventer, one puff morning and night, at both homes.",
                         "the review, and seeing him today")  # fmt: skip
        self.pack("asthma-nurse", note, "leo-own", "nurse-to-leo", "For you. The count stays with you unless you send it.")  # fmt: skip
        print("  the nurse sends her note to his box, and to neither house:")
        self.receive("leo-own", "nurse-to-leo")
        plan = self.seal("leo-own", "what is the plan for my inhaler at both houses", "mine.md",
                         "The plan is the purple inhaler, one puff morning and night, at both houses.",
                         "the asthma nurse told me on 2030-10-21")  # fmt: skip
        count = self.seal("leo-own", "how many times did I need the blue inhaler", "mine.md",
                          "This month I needed the blue inhaler nine times at Mum's and once at Dad's.",
                          "I counted")  # fmt: skip
        self.pack("leo-own", plan, "ravi-later", "leo-to-ravi", "Dad, it changed in September. This is the plan now.")  # fmt: skip
        self.pack("leo-own", count, "leo-at-fourteen", "leo-to-dana", "Mum, this is why I keep needing it at ours.")  # fmt: skip
        print(
            "  Leo sends the plan to his father, and the count to the box his mother holds:"
        )
        self.receive("ravi-later", "leo-to-ravi", quiet=True)
        self.receive("leo-at-fourteen", "leo-to-dana", quiet=True)
        to_dad = self.text("leo-to-ravi")
        leaked = "nine times" in to_dad or "Kieran" in to_dad
        reached_house = any("received" in self.kinds(b) and "asthma-nurse" in self.got(b) for b in ("leo-at-fourteen", "ravi-later"))  # fmt: skip
        has = {name: self.got(name) for name in BOXES}
        print(f"  the count reached his father: {leaked}; the nurse's note reached either house: {reached_house}")  # fmt: skip
        for name in ("leo-own", "leo-at-fourteen", "ravi-later"):
            said = (
                ", ".join(f"{n} from {w}" for w, n in sorted(has[name].items()))
                or "nothing"
            )
            print(f"  {name:16} has taken in: {said}")
        self.expect(
            not leaked and not reached_house, "something went where he did not send it"
        )
        self.expect(has["leo-own"] == {"leo-at-fourteen": 1, "ravi-later": 1, "asthma-nurse": 1}, "his box does not hold all three")  # fmt: skip
        own, mums = self.proves("leo-own", self.key("leo-own")), self.proves("leo-own", self.key("leo-at-fourteen"))  # fmt: skip
        self.expect(
            (own, mums) == (2, 0), "his seals did not prove under his key alone"
        )

        print("── 3. he can already hold them to it")
        held = {}
        for who, name in (
            ("leo-at-fourteen", "dana-to-leo"),
            ("ravi-later", "ravi-to-leo"),
        ):
            held[who] = self.run(SHARE, "witness", "--box", self.box(who), "--package",
                                 self.to / f"{name}.pkg").split()[0]  # fmt: skip
            print(
                f"  the record {self.holder[who]} keeps, held to what was sent him: {held[who]}"
            )
        self.expect(set(held.values()) == {"holds"}, "a parent's record did not hold to what was sent")  # fmt: skip
        self.said = {
            "parents_disagree": differ, "either_parent_has_the_others_word": across,
            "count_reached_father": leaked, "nurse_reached_a_house": reached_house,
            "taken_in": has, "his_seals_under_his_key": own, "under_his_mothers": mums,
            "parents_records_hold": held,
        }  # fmt: skip

        print("── 4. every box")
        table = {}
        for name in BOXES:
            out = self.run(KERNEL, "verify", "--box", self.box(name)).strip()
            table[name] = {"holder": self.holder[name], "verify": out}
            print(f"  {name:16} {out}; key held by {self.holder[name]}")
            self.expect(out.startswith("the chain holds"), f"{name} does not verify")
        doc = {"boxes": table, "said": self.said, "wrong": self.wrong}
        (self.to / "fourteen.json").write_text(
            json.dumps(doc, indent=1, sort_keys=True) + "\n"
        )
        return doc


def main(argv: list[str]) -> int:
    if len(argv) != 5 or argv[0] != "run" or {argv[1], argv[3]} != {"--life", "--to"}:
        print(USAGE, file=sys.stderr)
        return 2
    opts = {argv[1]: argv[2], argv[3]: argv[4]}
    life, to = Path(opts["--life"]), Path(opts["--to"]).resolve()
    if not (life / "leo-own").is_dir() or to.exists() or to.is_relative_to(ROOT):
        print("refused: --life is what make_life.py wrote; --to is new and outside the repository", file=sys.stderr)  # fmt: skip
        return 2
    doc = Fourteen(life, to).play()
    for line in doc["wrong"]:
        print(f"went otherwise: {line}")
    return 1 if doc["wrong"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
