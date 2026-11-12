"""adults.py: two adults who cannot decide, and who may act for them.

    python demo/minors/adults.py run --life DIR --to DIR

DIR for --life is what make_life.py wrote. Nobody here is real. A child
has a guardian from the start and a day the holding ends. An adult has
neither, and the two stories here differ in the one thing that matters:
whether they said beforehand.

1. **Named while she could.** Agnes is seventy-eight. In 2025, well, she
   sealed who is to decide for her if two doctors say she cannot, and
   sent it to her daughter Petra. In 2026 a clinic finds she cannot, for
   now, weigh a decision about her treatment. Petra and her brother
   Dorian each start a box held for her. One of the two rests on her own
   word, signed by her own key when she could give it, and on the
   clinic's finding; the other rests on nothing.
2. **The key outlives the deciding.** After the finding Agnes, on a clear
   day, seals that she wants to stay in her house. The next day Dorian,
   at her computer, seals with her key that he is to decide. Both prove
   under her key, and nothing tells her hand from his. What her record
   can say is that both were made after it took in the finding.
3. **No one named.** Marcus is forty-one and is knocked off his bike. He
   had sent his partner Jun an emergency card months before. Jun passes
   it to the hospital, signed by Marcus inside. His mother has nothing
   of his. Nobody holds a box for him and nobody touches his: the
   hospital keeps its own record, and when he wakes it sends him what
   was done. He takes it in, holds the hospital's record to it, and
   seals that he has read it.
4. Every box is verified.

It prints what happened and writes adults.json under --to. Exit 0 when
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
#: each box at the start: (whose it is, who holds its key)
BOXES = {
    "agnes": ("Agnes", "agnes"),
    "petra": ("Petra", "petra"),
    "dorian": ("Dorian", "dorian"),
    "clinic": ("the memory clinic", "dr-osei"),
    "marcus": ("Marcus", "marcus"),
    "jun": ("Jun", "jun"),
    "elaine": ("Elaine", "elaine"),
    "hospital": ("the ward", "ward"),
}
LATER = {"agnes-with-petra": "petra", "agnes-with-dorian": "dorian"}


class Adults(tense.Tense):
    def __init__(self, life: Path, to: Path):
        super().__init__(life, to)
        self.now = at("2025-03-14T10:00:00Z")
        self.holder = {name: holder for name, (_, holder) in BOXES.items()}

    def took(self, name: str, frm: str) -> int | None:
        """The row at which a box took in a package a given box signed."""
        for r in self.rows(name):
            if r["kind"] == "received" and r.get("from") == self.pub[frm] and r.get("verdict") == "good":  # fmt: skip
                return r["n"]
        return None

    def reads(self, name: str) -> tuple[bool, str]:
        out = self.run(SHARE, "check", "--package", self.to / f"{name}.pkg")
        return out.split("\n")[0].endswith("holds"), out

    def play(self) -> dict:
        self.to.mkdir()
        (self.to / "boxes").mkdir()
        print("── the boxes")
        for name, (whose, holder) in BOXES.items():
            self.start(name, self.life / name)
            print(f"  {name:9} {whose}'s box, on {holder}'s own key")

        print("── 1. named while she could: Agnes, seventy-eight")
        word = self.seal("agnes", "who is to decide for me if I cannot", "wishes.md",
                         "If two doctors say I can no longer decide about my care, my daughter Petra Thorne is to hold my papers and decide for me, and not my son.",
                         "what I wrote on 2025-03-14, while I can")  # fmt: skip
        self.pack(
            "agnes",
            word,
            "petra",
            "agnes-to-petra",
            "Keep this. I hope you never need it.",
        )
        print("  Agnes sends it to Petra, in 2025:")
        self.receive("petra", "agnes-to-petra")
        self.now = at("2026-11-05T15:00:00Z")
        finding = self.seal("clinic", "can Agnes Thorne decide about her treatment", "findings.md",
                            "On 2026-11-05 two doctors found that Agnes Thorne cannot at present weigh a decision about her medical treatment; to be looked at again in three months.",
                            "the assessment of that day")  # fmt: skip
        for to in ("petra", "agnes"):
            self.pack(
                "clinic",
                finding,
                to,
                f"finding-to-{to}",
                "Our finding, for your records.",
            )
        print(
            "  the clinic sends its finding to Petra, and to Agnes's own box, where it is taken in:"
        )
        self.receive("petra", "finding-to-petra", quiet=True)
        self.receive("agnes", "finding-to-agnes")
        for name, holder in LATER.items():
            self.holder[name] = holder
            self.start(name, self.life / name)
        kernel.append(self.box("agnes-with-petra"), self.ts(), "held-for", who="minors",
                      **{"for": "Agnes", "by": "petra", "until": "looked at again 2027-02",
                         "on": ["agnes-to-petra", "finding-to-petra"]})  # fmt: skip
        kernel.append(self.box("agnes-with-dorian"), self.ts(), "held-for", who="minors",
                      **{"for": "Agnes", "by": "dorian", "until": None})  # fmt: skip
        self.seal("agnes-with-petra", "where does she stay", "care.md",
                  "Agnes stays in her own house, with a carer three days a week.", "what she asked for")  # fmt: skip
        self.seal("agnes-with-dorian", "what is the plan for her", "plan.md",
                  "Agnes moves to the flat near us in the spring, and the house is sold.", "my plan")  # fmt: skip
        claim = sorted(LATER)
        her_word_ok, her_word = self.reads("agnes-to-petra")
        finding_ok, _ = self.reads("finding-to-petra")
        names_petra = (
            "my daughter Petra Thorne" in her_word and "not my son" in her_word
        )
        by_her_word = [
            box for box, holder in LATER.items()
            if self.took(holder, "agnes") is not None and self.took(holder, "clinic") is not None
            and her_word_ok and finding_ok and names_petra and holder == "petra"
        ]  # fmt: skip
        print(f"  boxes that say they are held for Agnes: {', '.join(claim)}")
        print(f"  her own word, read alone, holds and names her daughter: {her_word_ok and names_petra}; the finding holds: {finding_ok}")  # fmt: skip
        print(f"  the ones whose holder has both, from her key and from the clinic's: {', '.join(by_her_word)}")  # fmt: skip
        self.expect(by_her_word == ["agnes-with-petra"], "her word did not tell her children's boxes apart")  # fmt: skip
        self.expect(
            self.took("dorian", "agnes") is None, "Dorian holds something of hers"
        )
        self.said["agnes"] = {
            "claim_to_hold": claim, "by_her_word_and_the_finding": by_her_word,
            "her_word_holds_alone": her_word_ok and names_petra, "finding_holds_alone": finding_ok,
            "sent_while_well": self.took("petra", "agnes") is not None,
        }  # fmt: skip

        print("── 2. the key outlives the deciding")
        self.now = at("2026-11-09T11:00:00Z")
        self.seal("agnes", "where do I want to stay", "diary.md",
                  "I want to stay in my own house.", "said to Petra on a clear day, 2026-11-09")  # fmt: skip
        self.now = at("2026-11-10T20:00:00Z")
        print("  the next evening, at her computer, Dorian:")
        self.seal("agnes", "is my son to decide about my care", "wishes.md",
                  "My son Dorian is to decide for me.", "I have changed my mind")  # fmt: skip
        under_hers = self.proves("agnes", self.key("agnes"))
        line = self.took("agnes", "clinic")
        after = [r for r in self.rows("agnes") if r["kind"] == "seal" and r["n"] > line]
        before = [
            r for r in self.rows("agnes") if r["kind"] == "seal" and r["n"] < line
        ]
        marks = {r["who"] for r in after}
        print(f"  seals on her record that prove under her key: {under_hers}; ways her record tells her hand from his: {len(marks) - 1}")  # fmt: skip
        print(
            f"  seals her record puts before the finding: {len(before)}; after it: {len(after)}"
        )
        held = self.run(SHARE, "witness", "--box", self.box("agnes"), "--package",
                        self.to / "agnes-to-petra.pkg").split()[0]  # fmt: skip
        print(f"  her record, held to what she sent Petra in 2025: {held}. The later seal did not unsay the first")  # fmt: skip
        self.expect((under_hers, len(before), len(after), held) == (3, 1, 2, "holds") and len(marks) == 1,
                    "her record was not as told")  # fmt: skip
        self.said["key"] = {
            "seals_under_her_key": under_hers, "told_apart_by_the_record": len(marks) - 1,
            "before_the_finding": len(before), "after_the_finding": len(after),
            "first_word_still_holds": held == "holds",
        }  # fmt: skip

        print("── 3. no one named: Marcus, forty-one")
        self.now = at("2026-01-10T09:00:00Z")
        card = self.seal("marcus", "what is on my emergency card", "emergency-card.md",
                         "I am allergic to penicillin (anaphylaxis, 2014). Call Jun Okada, my partner, first.",
                         "the card I wrote")  # fmt: skip
        self.pack(
            "marcus", card, "jun", "marcus-to-jun", "In case. Keep it on your phone."
        )
        self.receive("jun", "marcus-to-jun", quiet=True)
        untouched = len(self.rows("marcus"))
        self.now = at("2026-11-02T18:30:00Z")
        self.run(SHARE, "forward", "--box", self.box("jun"), "--id", self.ids["jun"],
                 "--package", self.to / "marcus-to-jun.pkg", "--for", self.pub["hospital"],
                 "--to", self.to / "jun-to-hospital.pkg", "--note", "He wrote this himself. I am his partner.",
                 "--now", self.ts())  # fmt: skip
        print("  Jun passes Marcus's card to the hospital:")
        self.receive("hospital", "jun-to-hospital")
        ok, text = self.reads("jun-to-hospital")
        signed_by_him = self.pub["marcus"][:12] in text and "Call Jun Okada" in text
        elaine_has = self.took("elaine", "marcus") is not None
        print(f"  the card inside is signed by Marcus's own key: {ok and signed_by_him}; his mother holds anything he signed: {elaine_has}")  # fmt: skip
        self.now = at("2026-11-03T08:00:00Z")
        done = [
            self.seal("hospital", "was penicillin given to Marcus Bell", "bell.md",
                      "Penicillin was not given: his own card says anaphylaxis in 2014.",
                      "the ward's record and his card"),
            self.seal("hospital", "who decided on the surgery to his leg", "bell.md",
                      "Surgery to the left leg on 2026-11-03 was decided by the surgical team as being in his interests; Jun Okada was told beforehand and agreed.",
                      "the ward's record"),
        ]  # fmt: skip
        held_for_him = [n for n in [*BOXES, *LATER] if any(
            r["kind"] == "held-for" and r["for"] == "Marcus" for r in self.rows(n))]  # fmt: skip
        still = len(self.rows("marcus")) == untouched
        print(f"  boxes held for Marcus while he could not decide: {len(held_for_him)}; his own box untouched: {still}")  # fmt: skip
        self.now = at("2026-11-11T14:00:00Z")
        self.pack("hospital", ",".join(done), "marcus", "hospital-to-marcus", "What was done while you could not say. Yours to read.")  # fmt: skip
        print("  he wakes, and the hospital sends him what was done:")
        self.receive("marcus", "hospital-to-marcus")
        theirs = self.run(SHARE, "witness", "--box", self.box("hospital"), "--package",
                          self.to / "hospital-to-marcus.pkg").split()[0]  # fmt: skip
        self.seal("marcus", "what is my allergy", "emergency-card.md",
                  "I have read what the ward did from 2026-11-02 to 2026-11-11. My card stands as written.",
                  "my own card, and what they sent me")  # fmt: skip
        print(f"  the hospital's record, held to what it sent him: {theirs}")
        self.expect(ok and signed_by_him and not elaine_has and not held_for_him and still and theirs == "holds",
                    "the hospital's part was not as told")  # fmt: skip
        self.said["marcus"] = {
            "card_signed_by_him": ok and signed_by_him, "mother_holds_his_word": elaine_has,
            "boxes_held_for_him": len(held_for_him), "his_box_untouched_meanwhile": still,
            "took_in_on_waking": self.took("marcus", "hospital") is not None,
            "hospital_record_holds": theirs == "holds",
            "his_own_seals": self.proves("marcus", self.key("marcus")),
        }  # fmt: skip

        print("── 4. every box")
        table = {}
        for name in [*BOXES, *LATER]:
            out = self.run(KERNEL, "verify", "--box", self.box(name)).strip()
            table[name] = {"holder": self.holder[name], "verify": out}
            print(f"  {name:18} {out}; key held by {self.holder[name]}")
            self.expect(out.startswith("the chain holds"), f"{name} does not verify")
        doc = {"boxes": table, "said": self.said, "wrong": self.wrong}
        (self.to / "adults.json").write_text(
            json.dumps(doc, indent=1, sort_keys=True) + "\n"
        )
        return doc


def main(argv: list[str]) -> int:
    if len(argv) != 5 or argv[0] != "run" or {argv[1], argv[3]} != {"--life", "--to"}:
        print(USAGE, file=sys.stderr)
        return 2
    opts = {argv[1]: argv[2], argv[3]: argv[4]}
    life, to = Path(opts["--life"]), Path(opts["--to"]).resolve()
    if not (life / "agnes").is_dir() or to.exists() or to.is_relative_to(ROOT):
        print("refused: --life is what make_life.py wrote; --to is new and outside the repository", file=sys.stderr)  # fmt: skip
        return 2
    doc = Adults(life, to).play()
    for line in doc["wrong"]:
        print(f"went otherwise: {line}")
    return 1 if doc["wrong"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
