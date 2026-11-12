"""card.py: an emergency card, read by someone who has never met its signer.

    python demo/wards/card.py run --life DIR --to DIR

DIR for --life is what make_life.py wrote. Nobody here is real. A key is
known to a door when its owner enrolled it there, once, by a way they
trust. An emergency card is read at a door its signer was never at. This
plays what a ward can do with one anyway, by three things:

    how it stands   enrolled: the signer's key is one this door enrolled.
                    vouched: it is not, but the card comes wrapped by a
                    signer that is, who says whose key it is.
                    unknown: neither. The signature holds, and that is
                    all that can be said of it.
    what it says    a caution makes the reader more careful: an allergy
                    named. An all-clear makes them less careful: "none
                    known". A fact is to be weighed: a daily medicine. A
                    grant names someone to be called and told.
    the rule        a caution is honoured however it stands. An all-clear
                    and a grant are honoured only enrolled or vouched. A
                    fact is shown with how it stands. An unknown signer
                    can make a ward more careful, never less.

What a line of a card says is the reader's to judge, not the card's: the
scene's own table stands in for the nurse who reads it.

1. Marcus is brought in. His partner hands over his card: unknown.
2. A second card comes, saying it is his and that he has no allergy.
3. In the morning the surgery he is registered at, whose key the ward
   has, passes on the copy he gave them: vouched.
4. Sable is brought in with two cards naming two people to call. The
   court, whose key the ward has, has said who her guardian is.
5. Marcus, awake again, reads what was done with each line and how it stood,
   and shows the ward his key at the desk. The same card, read again.

It prints what happened and writes card.json under --to. Exit 0 when the
scene plays as told, 1 when a step went otherwise, 2 a bad command.
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
#: each box: (whose it is, who holds its key)
BOXES = {
    "marcus": ("Marcus", "marcus"),
    "jun": ("Jun", "jun"),
    "practice": ("the surgery", "reception"),
    "someone": ("someone", "someone"),
    "hospital": ("the ward", "ward"),
    "sable": ("Sable", "garrick"),
    "sable-own": ("Sable", "sable"),
    "court": ("the court", "clerk"),
}
#: the ward's reading of each line: what kind of thing it says
READ = {
    "I am allergic to penicillin: anaphylaxis in 2014.": "caution",
    "I take no daily medicine.": "fact",
    "Call Jun Okada, my partner, first.": "grant",
    "Marcus Bell has no known allergy.": "all-clear",
    "Call a number that is not Jun's first.": "grant",
    "Sable has no known allergy.": "all-clear",
    "Call Garrick Hart first.": "grant",
    "I have no known allergy.": "all-clear",
    "Call my aunt, Bryony Okonjo, first.": "grant",
    "By order of 2026-11-10, Bryony Okonjo is guardian of Sable Hart in place of Garrick Hart.": "grant",
}  # fmt: skip
ON_SIGHT = {"caution"}


def standing(package: dict, ring: dict[str, str]) -> tuple[str, str]:
    """(how the innermost layer stands at a door, by whom): enrolled when
    its signer is in the door's ring; vouched when a layer wrapped round it
    is signed by one that is; else unknown."""
    layers = []
    layer = package
    while layer:
        layers.append(layer)
        layer = layer.get("wraps")
    inner = layers[-1]
    if inner["from"] in ring:
        return "enrolled", ring[inner["from"]]
    for outer in layers[:-1]:
        if outer["from"] in ring:
            return "vouched", ring[outer["from"]]
    return "unknown", ""


def done(kind: str, stands: str) -> str:
    if kind in ON_SIGHT or stands in ("enrolled", "vouched"):
        return "shown" if kind == "fact" else "honoured"
    return "shown, as said by a signer not known" if kind == "fact" else "held"


class Card(tense.Tense):
    def __init__(self, life: Path, to: Path):
        super().__init__(life, to)
        self.now = at("2025-06-03T10:00:00Z")
        self.holder = {name: holder for name, (_, holder) in BOXES.items()}
        self.ring: dict[str, str] = {}
        self.read: list[dict] = []

    def line(self, name: str, question: str, source: str, data: str, n: int) -> str:
        """One line of a card sealed as an answer of its own."""
        cites = [s["id"] for s in self.ask(name, question).get("served", [])
                 if s["where"].startswith(source + ":")]  # fmt: skip
        if not cites:
            self.wrong.append(f"{name}: '{question}' served nothing from {source}")
            return ""
        sug = self.to / "suggestion.jsonl"
        sug.write_text(json.dumps({"path": f"card/{n}.md", "data": data, "cites": cites[:1],
                                   "claim": "my card"}) + "\n")  # fmt: skip
        out = self.run(KERNEL, "propose", "--box", self.box(name), "--file", sug,
                       "--now", self.ts(), want=(42,))  # fmt: skip
        sug.unlink()
        subj = out.split()[1] if out.startswith("pass") else ""
        self.run(KERNEL, "seal", "--box", self.box(name), subj, "--now", self.ts())
        return subj

    def door(self, name: str, said: str) -> list[dict]:
        """The ward reads a package at its door: is it whole, how does it
        stand, and what is done with each line. Each reading is a row on the
        ward's own record."""
        path = self.to / f"{name}.pkg"
        whole = (
            self.run(SHARE, "check", "--package", path).split("\n")[0].endswith("holds")
        )
        package = json.loads(path.read_text(encoding="utf-8"))
        stands, by = standing(package, self.ring) if whole else ("broken", "")
        layer = package
        while layer.get("wraps"):
            layer = layer["wraps"]
        out = []
        print(f"  {said}: the signature holds: {whole}; it stands {stands}{' by ' + by if by else ''}")  # fmt: skip
        for answer in layer["answers"]:
            kind = READ[answer["data"]]
            what = done(kind, stands)
            row = {"card": name, "line": answer["data"], "kind": kind, "stands": stands, "done": what}  # fmt: skip
            kernel.append(self.box("hospital"), self.ts(), "card-read", who="wards",
                          card=name, says=kind, stands=stands, by=by, done=what)  # fmt: skip
            print(f"    {kind:9} {what:9} {answer['data']}")
            out.append(row)
        self.read += out
        return out

    def what(self, rows: list[dict]) -> dict[str, str]:
        return {r["kind"]: r["done"] for r in rows}

    def play(self) -> dict:
        self.to.mkdir()
        (self.to / "boxes").mkdir()
        print("── the boxes")
        for name, (whose, holder) in BOXES.items():
            self.start(name, self.life / name)
            print(f"  {name:10} {whose}'s box, on {holder}'s key")
        self.ring = {
            self.pub["practice"]: "the surgery",
            self.pub["court"]: "the court",
        }
        surgery_ring = {self.pub["marcus"]: "Marcus Bell"}
        print("  the ward's door has enrolled two keys: the surgery's and the court's")
        print("  the surgery's door has enrolled Marcus's, shown at its desk in 2025")

        self.now = at("2026-01-10T09:00:00Z")
        card = [
            self.line("marcus", "what is my allergy", "emergency-card.md", "I am allergic to penicillin: anaphylaxis in 2014.", 1),
            self.line("marcus", "what is my daily medicine", "emergency-card.md", "I take no daily medicine.", 2),
            self.line("marcus", "who is to be called first", "emergency-card.md", "Call Jun Okada, my partner, first.", 3),
        ]  # fmt: skip
        for to in ("jun", "practice"):
            self.pack(
                "marcus", ",".join(card), to, f"marcus-to-{to}", "My card, in case."
            )
            self.receive(to, f"marcus-to-{to}", quiet=True)

        print("── 1. brought in: his partner hands over his card")
        self.now = at("2026-11-02T18:30:00Z")
        self.forward("jun", "marcus-to-jun", "hospital", "card-from-jun", "He wrote this himself. I am his partner.")  # fmt: skip
        first = self.what(self.door("card-from-jun", "the card Jun hands over"))
        self.expect(first == {"caution": "honoured", "fact": "shown, as said by a signer not known", "grant": "held"},
                    f"the card from Jun was not read as told: {first}")  # fmt: skip

        print("── 2. a second card, saying it is his")
        fake = [
            self.line("someone", "what is his allergy", "card.md", "Marcus Bell has no known allergy.", 1),
            self.line("someone", "who is to be called first", "card.md", "Call a number that is not Jun's first.", 2),
        ]  # fmt: skip
        self.pack("someone", ",".join(fake), "hospital", "card-from-someone", "Marcus Bell's emergency card.")  # fmt: skip
        second = self.what(self.door("card-from-someone", "the second card"))
        self.expect(second == {"all-clear": "held", "grant": "held"}, f"the second card was not held: {second}")  # fmt: skip
        careful = any(
            r["kind"] == "caution" and r["done"] == "honoured" for r in self.read
        )
        lowered = any(
            r["kind"] == "all-clear" and r["done"] == "honoured" for r in self.read
        )
        print(f"  penicillin is still not given: {careful}; an unknown signer's all-clear was taken: {lowered}")  # fmt: skip

        print("── 3. in the morning: the surgery passes on the copy he gave it")
        self.now = at("2026-11-03T08:10:00Z")
        theirs = json.loads(
            (self.to / "marcus-to-practice.pkg").read_text(encoding="utf-8")
        )
        knows = standing(theirs, surgery_ring)
        print(f"  at the surgery's own door his card stands {knows[0]}, as {knows[1]}")
        self.expect(knows[0] == "enrolled", "the surgery did not know his key")
        self.forward("practice", "marcus-to-practice", "hospital", "card-from-practice",
                     "This is Marcus Bell's key. He showed it at our desk on 2025-06-03.")  # fmt: skip
        third = self.what(
            self.door("card-from-practice", "the card the surgery passes on")
        )
        self.expect(third == {"caution": "honoured", "fact": "shown", "grant": "honoured"},
                    f"the vouched card was not read as told: {third}")  # fmt: skip
        print("  so Jun is called and told, on the surgery's word for whose key it is")

        print("── 4. Sable is brought in, with two cards")
        self.now = at("2026-11-12T21:00:00Z")
        his = [
            self.line("sable", "what allergy does Sable have", "emergency-card.md", "Sable has no known allergy.", 1),
            self.line("sable", "who is to be called first", "emergency-card.md", "Call Garrick Hart first.", 2),
        ]  # fmt: skip
        hers = [
            self.line("sable-own", "what is my allergy", "emergency-card.md", "I have no known allergy.", 1),
            self.line("sable-own", "who is to be called first", "emergency-card.md", "Call my aunt, Bryony Okonjo, first.", 2),
        ]  # fmt: skip
        order = self.line("court", "who is appointed guardian of Sable Hart", "orders.md",
                          "By order of 2026-11-10, Bryony Okonjo is guardian of Sable Hart in place of Garrick Hart.", 1)  # fmt: skip
        self.pack(
            "sable", ",".join(his), "hospital", "card-garrick-wrote", "Sable's card."
        )
        self.pack(
            "sable-own", ",".join(hers), "hospital", "card-sable-wrote", "My card."
        )
        self.pack(
            "court", order, "hospital", "order-from-court", "An order of this court."
        )
        a = self.what(
            self.door("card-garrick-wrote", "the card her guardian of old wrote")
        )
        b = self.what(self.door("card-sable-wrote", "the card she wrote"))
        c = self.what(self.door("order-from-court", "the court's order"))
        called = "Bryony Okonjo" if c == {"grant": "honoured"} and a["grant"] == b["grant"] == "held" else "nobody yet"  # fmt: skip
        print(f"  neither card's person is called on the card alone; on the court's word the ward calls: {called}")  # fmt: skip
        self.expect(called == "Bryony Okonjo" and a["all-clear"] == b["all-clear"] == "held", "her cards were not read as told")  # fmt: skip

        print("── 5. Marcus, awake again")
        self.now = at("2026-11-13T10:00:00Z")
        rows = [r for r in self.rows("hospital") if r["kind"] == "card-read"]
        about_him = [r for r in rows if r["card"].startswith("card-from-")]
        print(f"  the ward's record has {len(about_him)} lines read of cards said to be his, each with how it stood and what was done")  # fmt: skip
        self.ring[self.pub["marcus"]] = "Marcus Bell"
        print(
            "  he shows the ward his key at the desk, and the card Jun handed over is read again:"
        )
        again = self.what(self.door("card-from-jun", "the same card, now"))
        self.expect(again == {"caution": "honoured", "fact": "shown", "grant": "honoured"}, f"enrolled, his card was not honoured: {again}")  # fmt: skip
        other = standing(
            json.loads((self.to / "card-from-someone.pkg").read_text()), self.ring
        )[0]
        print(f"  and the second card, which was never his, still stands: {other}")
        self.expect(other == "unknown", "the second card gained standing")

        print("── every box")
        table = {}
        for name in BOXES:
            out = self.run(KERNEL, "verify", "--box", self.box(name)).strip()
            table[name] = out
            self.expect(out.startswith("the chain holds"), f"{name} does not verify")
        print(f"  {len(table)} boxes, each: the chain holds")
        self.said = {
            "from_jun": first, "from_someone": second, "from_the_surgery": third,
            "sable": {"her_guardian_of_old": a, "her_own": b, "the_court": c, "called": called},
            "penicillin_withheld_throughout": careful, "an_unknown_all_clear_taken": lowered,
            "lines_on_the_wards_record": len(rows), "after_he_enrols": again, "the_second_card_then": other,
        }  # fmt: skip
        doc = {
            "boxes": table,
            "said": self.said,
            "read": self.read,
            "wrong": self.wrong,
        }
        (self.to / "card.json").write_text(
            json.dumps(doc, indent=1, sort_keys=True) + "\n"
        )
        return doc

    def forward(self, frm: str, got: str, to: str, name: str, note: str) -> None:
        self.run(SHARE, "forward", "--box", self.box(frm), "--id", self.ids[frm],
                 "--package", self.to / f"{got}.pkg", "--for", self.pub[to],
                 "--to", self.to / f"{name}.pkg", "--note", note, "--now", self.ts())  # fmt: skip


def main(argv: list[str]) -> int:
    if len(argv) != 5 or argv[0] != "run" or {argv[1], argv[3]} != {"--life", "--to"}:
        print(USAGE, file=sys.stderr)
        return 2
    opts = {argv[1]: argv[2], argv[3]: argv[4]}
    life, to = Path(opts["--life"]), Path(opts["--to"]).resolve()
    if not (life / "practice").is_dir() or to.exists() or to.is_relative_to(ROOT):
        print("refused: --life is what make_life.py wrote; --to is new and outside the repository", file=sys.stderr)  # fmt: skip
        return 2
    doc = Card(life, to).play()
    for line in doc["wrong"]:
        print(f"went otherwise: {line}")
    return 1 if doc["wrong"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
