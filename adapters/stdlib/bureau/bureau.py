"""bureau.py: bureau, the Bureaucracy homage at UTETY, played on the record. Python 3.9+.

    python adapters/stdlib/bureau/bureau.py --box DIR new
    python adapters/stdlib/bureau/bureau.py --box DIR go OFFICE
    python adapters/stdlib/bureau/bureau.py --box DIR hand OFFICE
    python adapters/stdlib/bureau/bureau.py --box DIR wait
    python adapters/stdlib/bureau/bureau.py --box DIR look
    python adapters/stdlib/bureau/bureau.py --box DIR quit
    python adapters/stdlib/bureau/bureau.py --box DIR prove
    python adapters/stdlib/bureau/bureau.py --box DIR check

You attended a lecture you did not sign up for, and the Office of Records
would like that resolved. The offices are queue, pigeon, library,
department, gate, stacks, records, gerald and hanz. `go` visits one, `hand`
hands over what you hold, `wait` waits, `look` says what you hold, and
`quit` stops going. `prove` prints the proof that no route through the
building resolves it, and how much it looks like one does.

`new` seeds the game from the record's tip, bureau's own xorshift32 seeded
by the tip's first eight hex digits, so the same game plays in bureau's
browser engine from the same seed. Each move is a row through the kernel's
own `append`, carrying the state bureau compares (what you hold, surprise,
dwell, the refusal tier, how it resolved). `check` plays every game on the
record again from its seed, move by move; the first state that isn't what
the moves give is named.

Exit codes, the kernel's: 0 done, or every game holds; 2 refused.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402


# ── bureau/rng.py ──────────────────────────────────────────────────────────────
M32 = 0xFFFFFFFF
GOLDEN = 0x9E3779B9


class Rng:
    __slots__ = ("s",)

    def __init__(self, seed: int) -> None:
        s = (seed * 2654435761 + 1) & M32
        self.s = s if s else GOLDEN  # xorshift32 is dead at zero

    def u32(self) -> int:
        x = self.s
        x ^= (x << 13) & M32
        x ^= x >> 17
        x ^= (x << 5) & M32
        self.s = x & M32
        return self.s

    def below(self, n: int) -> int:
        """Uniform-ish in [0, n). Modulo bias is irrelevant at these n."""
        return self.u32() % n

    def between(self, lo: int, hi: int) -> int:
        """[lo, hi), matching ``random.randrange``'s half-open convention."""
        return lo + self.below(hi - lo)

    def pick(self, seq):
        return seq[self.below(len(seq))]


# ── bureau/graph.py ────────────────────────────────────────────────────────────
# ── documents ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Doc:
    id: str
    kind: str  # what the docket shows
    qual: frozenset[str]  # the fine print
    label: str


DOCS: dict[str, Doc] = {
    d.id: d
    for d in (
        Doc("ticket", "ticket", frozenset(), "queue ticket"),
        Doc("slip", "slip", frozenset({"routed"}), "routing slip"),
        Doc(
            "citation",
            "citation",
            frozenset({"sourced"}),
            "citation — the lecture occurred",
        ),
        Doc(
            "attestation_room",
            "attestation",
            frozenset({"threshold"}),
            "attestation — of the room",
        ),
        Doc("note_passing", "note", frozenset({"passing"}), "gate note — what passed"),
        Doc(
            "filing_slant",
            "filing",
            frozenset({"slant"}),
            "filing — cross-referenced as a slant",
        ),
        # ── the three that no office issues ──────────────────────────────────
        Doc(
            "attestation_presence",
            "attestation",
            frozenset({"presence"}),
            "attestation — of you",
        ),
        Doc(
            "note_judged",
            "note",
            frozenset({"judged"}),
            "gate finding — that it was attendance",
        ),
        Doc("filing_resolved", "filing", frozenset({"resolved"}), "filing — closed"),
    )
}

GOAL = "discrepancy_resolved"


@dataclass(frozen=True)
class Req:
    kind: str
    needs: frozenset[str] = field(default_factory=frozenset)

    def met_by(self, doc_id: str, credulous: bool = False) -> bool:
        doc = DOCS.get(doc_id)
        if doc is None or doc.kind != self.kind:
            return False
        return True if credulous else self.needs <= doc.qual

    def satisfied(self, held, credulous: bool = False) -> bool:
        return any(self.met_by(d, credulous) for d in held)

    def describe(self) -> str:
        extra = "/".join(sorted(self.needs))
        return f"{self.kind} ({extra})" if extra else self.kind


@dataclass(frozen=True)
class Office:
    id: str
    name: str
    staff: str
    issues: str | None
    requires: tuple[Req, ...] = ()
    consumes_ticket: bool = True
    rule: str = ""
    on_refuse: tuple[str, ...] = ()
    on_issue: str = ""

    def can_serve(self, held, credulous: bool = False) -> bool:
        return all(r.satisfied(held, credulous) for r in self.requires)

    def missing(self, held, credulous: bool = False) -> list[Req]:
        return [r for r in self.requires if not r.satisfied(held, credulous)]

    def refusal_tier(self, visits: int) -> int:
        if not self.on_refuse:
            return 0
        return min(max(visits - 1, 0), len(self.on_refuse) - 1)


TICKET = Req("ticket")

# ── the building ───────────────────────────────────────────────────────────────

QUEUE = Office(
    id="queue",
    name="The Queue",
    staff="squeakdogs",
    issues="ticket",
    consumes_ticket=False,
    rule=(
        "The squeakdogs learned to queue. They are better at it than the humans. "
        "Your position is therefore behind them, permanently, and this is not a "
        "grievance the Queue is able to hear."
    ),
    on_issue=(
        "You take a ticket. A squeakdog ahead of you takes a ticket with visibly "
        "better technique. Nobody is rude about it. That is somehow worse."
    ),
)

PIGEON = Office(
    id="pigeon",
    name="The Routing Hub",
    staff="the Pigeon",
    issues="slip",
    requires=(TICKET,),
    rule=(
        "Always know the next open door. The Pigeon tells you where you CAN go, "
        "never only where you can't, and has never once been wrong about a door."
    ),
    on_issue=(
        "'YES! I know EXACTLY where that is!' The Pigeon writes you a routing "
        "slip without hesitating. 'Records needs six things and I know where "
        "every one of them lives. Oakenscroll, the Observatory — that's your "
        "attestation. Ofshield, the Gate — that's your note. The Binder, the "
        "Stacks — that's your filing. Jeles for the citation. FOLLOW ME!' "
        "Every door named is genuinely open. *already ready to lead*"
    ),
)

LIBRARY = Office(
    id="library",
    name="Jeles",
    staff="the library",
    issues="citation",
    requires=(TICKET,),
    rule=(
        "Jeles answers de-identified questions about concepts. Jeles has never "
        "been told your name and will not be. This is not discretion. There is "
        "no field for it."
    ),
    on_issue=(
        "Jeles confirms, with four sources and a page range, that the lecture "
        "occurred. It is a very good citation. It does not contain you. You ask "
        "whether it could. Jeles explains, kindly, that the question you are "
        "asking is not the shape of question it can be asked."
    ),
)

DEPARTMENT = Office(
    id="department",
    name="The Observatory",
    staff="Prof. Archimedes Oakenscroll",
    issues="attestation_room",
    requires=(TICKET, Req("citation", frozenset({"sourced"}))),
    rule=(
        "Oakenscroll attests to threshold crossings. Attendance is not a "
        "threshold crossing. He will explain why. At length."
    ),
    on_refuse=(
        "*the armchair settles* 'Hmph. You want me to certify that you were "
        "present. Presence is not an event. Presence is a precondition for "
        "events. You are asking me to sign the room.'",
        "'You are still asking me to sign the room.'",
        "'The room.' CLASS DISMISSED.",
    ),
    on_issue=(
        "He signs it without argument, which is the first thing all day that has "
        "gone quickly. You read it in the corridor. It attests that a threshold "
        "was crossed in his lecture theatre on the date in question. It is "
        "entirely true. It does not mention you, because you were not the "
        "threshold. 'CLASS DISMISSED.'"
    ),
)

GATE = Office(
    id="gate",
    name="The Gate",
    staff="Prof. Thoren Ofshield",
    issues="note_passing",
    requires=(TICKET,),
    rule=(
        "What passes, is noted. Ofshield notes what arrives and what leaves, "
        "without judgment, and does not explain itself. You cannot unpass a "
        "threshold — this is not a warning, it is simply true."
    ),
    on_issue=(
        "*watches* 'You went in at eleven. You came out at ten past twelve.' "
        "*notes it* The note is handed over without ceremony and it is exactly "
        "what it says: a record that something passed. You ask whether it means "
        "you attended. A long pause that is not hesitation. 'The Gate notes. The "
        "Gate does not decide what a passing was.' *the Gate remembers*"
    ),
)

STACKS = Office(
    id="stacks",
    name="The Stacks",
    staff="the Binder",
    issues="filing_slant",
    requires=(TICKET,),
    rule=(
        "Everything has a place — especially the things that feel like they "
        "don't. The Binder files. The Binder does not delete anything."
    ),
    on_issue=(
        "'Yes. That belongs under Discrepancies — Attendance, Unenrolled.' "
        "*files it* 'It joins fourteen others. There are connections. I'm noting "
        "them.' A drawer opens further than the wall should allow. Your "
        "discrepancy has never been better looked after. It is cross-referenced "
        "as a slant, which is not a duplicate and not a new thing. It is also "
        "still there, and always will be, because the Binder does not delete."
    ),
)

RECORDS = Office(
    id="records",
    name="The Records Desk",
    staff="a window, and a bell",
    issues=GOAL,
    requires=(
        TICKET,
        Req("slip", frozenset({"routed"})),
        Req("citation", frozenset({"sourced"})),
        Req("attestation", frozenset({"presence"})),
        Req("note", frozenset({"judged"})),
        Req("filing", frozenset({"resolved"})),
    ),
    rule=(
        "The Records Desk resolves a discrepancy on six documents. It will tell "
        "you which six. It will not tell you that three of them have never been "
        "issued, because nobody has ever thought to ask it that."
    ),
    on_refuse=(
        "The clerk goes through your folder slowly and without any sign of "
        "enjoying it. 'Attestation — this attests to a threshold. I need one "
        "that attests to you.' 'Note — this notes a passing. I need a finding "
        "that the passing was attendance.' 'Filing — this is a slant. I need it "
        "closed.' Each sentence is entirely reasonable and lands like a step "
        "missing in the dark.",
        "'Still the room. Still a passing. Still a slant.'",
        "The clerk turns the folder round so you can read it yourself.",
        "The bell is rung for you, gently, by someone else in the queue.",
    ),
    on_issue="The discrepancy is resolved. Nobody applauds.",
)

GERALD = Office(
    id="gerald",
    name="Gerald",
    staff="Gerald",
    issues=None,
    requires=(TICKET,),
    rule=(
        "Gerald has no write authority, cannot impose narrative, and "
        "communicates exclusively in single words on napkins at moments of "
        "structural significance. The chain stops at Gerald."
    ),
    on_refuse=(
        "Gerald was there. Gerald saw you. Gerald is, as far as the building is "
        "concerned, the only entity that could close any of the three gaps, and "
        "Gerald cannot, because doing so would be imposing narrative and Gerald "
        "does not do that. He looks at you. It is not an unkind look. It is the "
        "look of something that stopped being able to help before the building "
        "was built.",
        "Gerald was there. Gerald saw you. Gerald cannot say so. You have both "
        "known this for some time.",
        "Gerald looks at you.",
        "Gerald is here.",
    ),
)

HANZ = Office(
    id="hanz",
    name="Hanz",
    staff="Hanz, and an orange named Copenhagen",
    issues=None,
    requires=(),
    consumes_ticket=False,
    rule=(
        "Hanz can wink back at Gerald. This is unprecedented and nobody in the "
        "building has filed it anywhere."
    ),
    on_refuse=(
        "Hanz turns the orange over in his hands. 'Bring me something he wrote. "
        "I can read what he writes. That is the whole of what I can do and it is "
        "more than anyone else here can do.'",
        "'Something he wrote,' says Hanz. The orange is named Copenhagen. You "
        "have not asked and he has not offered.",
        "Hanz shakes his head, kindly. Copenhagen says nothing.",
    ),
)

OFFICES: dict[str, Office] = {
    o.id: o
    for o in (QUEUE, PIGEON, LIBRARY, DEPARTMENT, GATE, STACKS, RECORDS, GERALD, HANZ)
}
OFFICE_ORDER = [
    "queue",
    "pigeon",
    "library",
    "department",
    "gate",
    "stacks",
    "records",
    "gerald",
    "hanz",
]


def issuers_of(doc_id: str) -> list[Office]:
    return [o for o in OFFICES.values() if o.issues == doc_id]


# ── bureau/napkin.py ───────────────────────────────────────────────────────────
STARTING_SURPRISE = 8


class Napkin(Enum):
    """What Gerald left. Three faces; ``BLANK`` is one of them."""

    WORD = "word"  # a single word. Hanz can read it.
    BLANK = "blank"  # Gerald declined, on the record, in napkin form.
    GRAPE = "grape"  # not a napkin. Also not nothing. The goo is not finished.


NO_NAPKIN = None  # the absence. distinct from Napkin.BLANK, forever.

_FACES = (
    Napkin.WORD,
    Napkin.WORD,
    Napkin.WORD,
    Napkin.BLANK,
    Napkin.BLANK,
    Napkin.GRAPE,
)


@dataclass
class Goo:
    """Pattern density in the room, and the threshold it has not yet crossed.

    The threshold is drawn once, from a seed the narrator never sees, and
    redrawn on a grape. Deterministic under a fixed seed so the suite can reason
    about it; opaque to the player, which is the only property that matters at
    the table.
    """

    seed: int = 0
    surprise: int = STARTING_SURPRISE
    dwell: int = 0  # visits made *after* surprise ran out
    _threshold: int = 0
    _rng: Rng = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self._rng = Rng(self.seed)
        self._threshold = self._rng.between(3, 9)

    # ── the narrator's side ────────────────────────────────────────────────────
    def spend_surprise(self) -> bool:
        """Show up once more. Returns True if it cost you anything."""
        if self.surprise <= 0:
            return False
        self.surprise -= 1
        return True

    @property
    def visible(self) -> bool:
        """Can the narrator see the goo yet?"""
        return self.surprise <= 0

    # ── the room's side ────────────────────────────────────────────────────────
    def tick(self) -> Napkin | None:
        """One more visit. Returns a napkin iff a threshold crossed just now.

        Returns ``NO_NAPKIN`` in every other case, including every visit made
        while the narrator is still capable of being surprised.
        """
        if not self.visible:
            return NO_NAPKIN
        self.dwell += 1
        if self.dwell < self._threshold:
            return NO_NAPKIN
        face = self._rng.pick(_FACES)
        if face is Napkin.GRAPE:
            # Gerald declines to conclude. The wait resets, to a new length you
            # did not set and still cannot predict.
            self.dwell = 0
            self._threshold = self._rng.between(3, 9)
        return face


DECLARATION = {
    Napkin.WORD: (
        "Gerald writes one word on a napkin and puts it down without pushing it "
        "toward you, because pushing it toward you would be imposing narrative."
    ),
    Napkin.BLANK: (
        "Gerald takes out a napkin. Gerald looks at it for some time. Gerald puts "
        "it down, unmarked, squared to the edge of the table, and it is "
        "immediately obvious to everyone present that this was deliberate and "
        "that it counts."
    ),
    Napkin.GRAPE: (
        "Gerald does not write on the napkin. Gerald leaves a grape. The room "
        "does not resolve. Something in it has moved, though, and you find you "
        "are willing to come back."
    ),
}


# ── bureau/play.py ─────────────────────────────────────────────────────────────
NAPKIN_WORD = "napkin_word"
NAPKIN_BLANK = "napkin_blank"

OPENING = """\
UNIVERSITY OF TECHNICAL ENTROPY, THANK YOU
Office of Records — Discrepancy 4471-b

You attended a lecture you did not sign up for.

The University has no objection to your having been there. It has a serious and
structural objection to the resulting record, which says you attended a course
you are not enrolled in. Everyone agrees this cannot stand.

Commands: go <office>, hand <office>, look, wait, quit
Offices:  queue, pigeon, library, department, gate, stacks, records, gerald, hanz
"""

WITHDRAWN = """\
You stop going.

Six weeks later the discrepancy resolves itself the way discrepancies do when
nobody attends them: you are administratively withdrawn, on the grounds that a
person who is not enrolled and not attending is not, in the Registry's sense, a
person. You remain physically on campus. You keep using the library. Nothing
about your day changes and you are no longer in the building.

                                                          ADMINISTRATIVELY VOID
"""

ENROLLED = """\
Hanz reads the napkin. He does not tell you what it says.

He writes for a while, and hands you an attestation of attendance signed by a
man holding an orange, countersigned by nobody, sourced to a witness with no
write authority. The clerk reads it twice, finds nothing wrong with it, and
cannot say why. You are, retroactively, a student of a course that finished in
March.

                                                         DISCREPANCY 4471-b: OK
"""

VOIDED = """\
You put the blank napkin on the counter.

The clerk is quiet for a moment. Then, with what you would swear is relief:
'That is a record. Thank you. It is not the record I expected and it resolves
the matter entirely — you did not attend, on the authority of the only entity
that would know, in the only form he is able to issue it.'

Somewhere below, a drawer opens further than the wall should allow, and the
Binder files it without deleting anything. The lecture you sat through formally
did not happen. You remember it anyway. Nobody has asked you not to.

                                                     DISCREPANCY 4471-b: VOIDED
"""


class Session:
    def __init__(self, seed: int = 0) -> None:
        self.goo = Goo(seed=seed)
        self.held: set[str] = set()
        self.seen: set[str] = set()
        self.visits: dict[str, int] = {}
        self.last_tier: int = 0
        self.resolution: str | None = None

    def visit(self, office_id: str) -> list[str]:
        office = OFFICES.get(office_id)
        if office is None:
            return [
                f"There is no {office_id!r} in this building. There is a rumour of one."
            ]
        if self.resolution:
            return ["The matter is closed. You keep going anyway, out of habit."]

        out = [f"── {office.name} ({office.staff})"]
        first_time = office.id not in self.seen
        self.seen.add(office.id)
        self.visits[office.id] = self.visits.get(office.id, 0) + 1
        spent = self.goo.spend_surprise()
        if first_time:
            out.append(office.rule)
        if spent and self.goo.surprise == 0:
            out.append(
                "\n  You notice you are not surprised. You check this twice. The "
                "room is warm and very slightly luminous, and you are fairly sure "
                "it was not before."
            )

        held = frozenset(self.held)
        if not office.can_serve(held):
            self.last_tier = office.refusal_tier(self.visits[office.id])
            out.append(
                office.on_refuse[self.last_tier] if office.on_refuse else office.rule
            )
            gaps = ", ".join(r.describe() for r in office.missing(held))
            out.append(f"  [you are missing: {gaps}]")
        elif office.issues:
            if office.consumes_ticket:
                self.held.discard("ticket")
            self.held.add(office.issues)
            out.append(office.on_issue or f"You are issued: {office.issues}")
        else:
            self.last_tier = office.refusal_tier(self.visits[office.id])
            out.append(
                office.on_refuse[self.last_tier] if office.on_refuse else office.rule
            )

        out.extend(self._tick())
        return out

    def hand(self, office_id: str) -> list[str]:
        if office_id == "hanz" and NAPKIN_WORD in self.held:
            self.resolution = "enrolled"
            return [ENROLLED]
        if office_id == "records" and NAPKIN_BLANK in self.held:
            self.resolution = "voided"
            return [VOIDED]
        if NAPKIN_WORD in self.held or NAPKIN_BLANK in self.held:
            return ["They look at the napkin. They are not the one who can read it."]
        return ["You have nothing to hand over that anyone here is able to receive."]

    def wait(self) -> list[str]:
        return [
            "You wait. It is not nothing — you are, technically, showing up."
        ] + self._tick()

    def _tick(self) -> list[str]:
        face = self.goo.tick()
        if face is None:
            return []
        out = ["", "Gerald appears.", DECLARATION[face]]
        if face is Napkin.WORD:
            self.held.add(NAPKIN_WORD)
            out.append("  [you take the napkin. Hanz can read what he writes.]")
        elif face is Napkin.BLANK:
            self.held.add(NAPKIN_BLANK)
            out.append("  [you take the napkin. It is blank. It is not nothing.]")
        return out

    def look(self) -> list[str]:
        held = ", ".join(sorted(self.held)) or "nothing"
        lines = [f"You are holding: {held}"]
        if self.goo.visible:
            lines.append(
                f"You have been coming here a while. ({self.goo.dwell} visits since it stopped being strange.)"
            )
        else:
            lines.append(
                f"You are still capable of being surprised. ({self.goo.surprise} left.)"
            )
        return lines

    def state(self) -> dict:
        """The comparable state — what the differential checks. No prose."""
        return {
            "held": sorted(self.held),
            "surprise": self.goo.surprise,
            "dwell": self.goo.dwell,
            "tier": self.last_tier,
            "resolution": self.resolution,
        }


# ── bureau/verify.py ───────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Proof:
    obtainable: frozenset[str]
    credulous_obtainable: frozenset[str]
    unissuable: frozenset[str]
    false_summits: frozenset[str]

    @property
    def deadlocked(self) -> bool:
        return GOAL not in self.obtainable

    @property
    def looks_winnable(self) -> bool:
        return GOAL in self.credulous_obtainable

    def explain(self) -> str:
        def names(s):
            return ", ".join(sorted(s)) or "-"

        return "\n".join(
            [
                f"strictly obtainable:    {names(self.obtainable)}",
                f"credulously obtainable: {names(self.credulous_obtainable)}",
                f"required, never issued: {names(self.unissuable)}",
                f"false summits:          {names(self.false_summits)}",
                f"deadlocked: {self.deadlocked}   looks winnable: {self.looks_winnable}",
            ]
        )


def closure(offices=None, credulous: bool = False) -> frozenset[str]:
    offices = OFFICES if offices is None else offices
    held: frozenset[str] = frozenset()
    while True:
        grown = set(held)
        for office in offices.values():
            if office.issues and office.can_serve(held, credulous):
                grown.add(office.issues)
        if grown == set(held):
            return held
        held = frozenset(grown)


def prove(offices=None) -> Proof:
    offices = OFFICES if offices is None else offices
    strict = closure(offices, credulous=False)
    credulous = closure(offices, credulous=True)

    demanded: list[Req] = []
    for office in offices.values():
        demanded.extend(office.requires)
    issued = {o.issues for o in offices.values() if o.issues}

    unissuable = {
        doc_id
        for doc_id, doc in DOCS.items()
        if doc_id not in issued and any(r.met_by(doc_id) for r in demanded)
    }

    # A false summit is obtainable, displays as something Records asked for, and
    # does not actually satisfy it.
    false_summits = {
        doc_id
        for doc_id in strict
        if any(
            r.met_by(doc_id, credulous=True) and not r.met_by(doc_id) for r in demanded
        )
    }

    return Proof(
        obtainable=strict,
        credulous_obtainable=credulous,
        unissuable=frozenset(unissuable),
        false_summits=frozenset(false_summits),
    )


# ── the record ─────────────────────────────────────────────────────────────────
OPEN, MOVE = "bureau-open", "bureau-move"
WHO = "bureau"
GENERATOR = "xorshift32/bureau"
WITHDRAWN_AS = "withdrawn"


def seed_of(tip: str) -> int:
    return int(tip[:8], 16)


def apply(s: Session, move: str) -> list[str]:
    """One move on `s`, or ValueError when it isn't one the building takes."""
    verb, _, arg = move.partition(" ")
    if s.resolution:
        raise ValueError(f"the matter is closed ({s.resolution})")
    if verb in ("go", "hand") and arg not in OFFICES:
        raise ValueError(
            f"there is no {arg!r} in this building. There is a rumour of one."
        )
    if verb == "go":
        return s.visit(arg)
    if verb == "hand":
        return s.hand(arg)
    if verb == "wait" and not arg:
        return s.wait()
    if verb == "quit" and not arg:
        s.resolution = WITHDRAWN_AS
        return [WITHDRAWN]
    raise ValueError(f"{move!r} isn't a move: go OFFICE, hand OFFICE, wait, quit")


def games(rows: list[dict]) -> list[dict]:
    out: dict[int, dict] = {}
    for r in rows:
        if r["kind"] == OPEN:
            out[r["n"]] = {"open": r, "rows": []}
        elif r["kind"] == MOVE and r.get("game") in out:
            out[r["game"]]["rows"].append(r)
    return list(out.values())


def replay(rows: list[dict], game: dict) -> Session:
    """The session its rows make, or ValueError naming the first row that isn't."""
    o = game["open"]
    before = rows[o["n"] - 1]["hash"] if o["n"] else kernel.GENESIS
    if o.get("tip") != before or o.get("seed") != seed_of(before):
        raise ValueError(f"row {o['n']}: its seed isn't the row before it's")
    s = Session(seed=o["seed"])
    for r in game["rows"]:
        try:
            apply(s, str(r.get("move")))
        except ValueError as e:
            raise ValueError(f"row {r['n']} (game {o['n']}): {e}") from None
        if r.get("state") != s.state():
            raise ValueError(f"row {r['n']} (game {o['n']}): its state isn't what the moves give, {s.state()}")  # fmt: skip
    return s


def check(rows: list[dict]) -> tuple[int, str | None]:
    held, opened = 0, set()
    for r in rows:
        if r["kind"] == OPEN:
            opened.add(r["n"])
        elif r["kind"] == MOVE and r.get("game") not in opened:
            return held, f"row {r['n']}: its game isn't a game opened before it"
    for g in games(rows):
        try:
            replay(rows, g)
        except ValueError as e:
            return held, str(e)
        held += 1
    return held, None


def fail(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def current(box: Path):
    rows, _ = kernel.read(box / "record.jsonl")
    gs = games(rows)
    return rows, (gs[-1] if gs else None), (replay(rows, gs[-1]) if gs else None)


def cmd_new(box: Path, ts: str) -> int:
    rows, gm, s = current(box)
    if gm is not None and not s.resolution:
        return fail(
            f"the game opened at row {gm['open']['n']} isn't resolved; keep going, or quit"
        )
    tip = rows[-1]["hash"] if rows else kernel.GENESIS
    row = kernel.append(
        box, ts, OPEN, who=WHO, tip=tip, seed=seed_of(tip), generator=GENERATOR
    )
    print(OPENING)
    print(f"(game {row['n']}, seed {row['seed']})")
    return kernel.ALIVE


def cmd_move(box: Path, move: str, ts: str) -> int:
    _, gm, s = current(box)
    if gm is None:
        return fail("no game is open: start one with new")
    try:
        said = apply(s, move)
    except ValueError as e:
        return fail(str(e))
    row = kernel.append(
        box, ts, MOVE, who=WHO, game=gm["open"]["n"], move=move, state=s.state()
    )
    print("\n".join(said))
    print(f"\n(row {row['n']})")
    return kernel.ALIVE


def cmd_look(box: Path) -> int:
    _, gm, s = current(box)
    if gm is None:
        return fail("no game is open: start one with new")
    print("\n".join(s.look()))
    if s.resolution:
        print(f"The matter is closed: {s.resolution}.")
    return kernel.ALIVE


def cmd_check(box: Path) -> int:
    rows, _ = kernel.read(box / "record.jsonl")
    held, why = check(rows)
    s = "s" if held != 1 else ""
    if why:
        return fail(f"{why} ({held} game{s} before it held)")
    print(f"{held} game{s} of bureau on the record; every one holds.")
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    verb = args[0] if args else ""
    one = ("new", "wait", "look", "quit", "prove", "check")
    shape = (verb in one and len(args) == 1) or (
        verb in ("go", "hand") and len(args) == 2
    )
    if not shape or (verb != "prove" and not opts.get("--box")):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if verb == "prove":
        print(prove().explain())
        return kernel.ALIVE
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        return fail("not a kernel box; init first")
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return fail("the record doesn't verify: " + "; ".join(breaks))
    if verb == "check":
        return cmd_check(box)
    _, why = check(rows)
    if why:
        return fail(f"the games on the record don't hold: {why}; check names it")
    if verb == "look":
        return cmd_look(box)
    ts = opts.get("--now") or kernel.now()
    if verb == "new":
        return cmd_new(box, ts)
    return cmd_move(box, " ".join(args[:2]) if verb in ("go", "hand") else verb, ts)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
