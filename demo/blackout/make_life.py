"""The steelworks' eight boxes, as the files each keeps: python3 make_life.py [--rules PILE] [--check]

Writes life/<box>/ for each of them, the same bytes every run. Everything is
invented: Brannock Steel Works, its plant, its people and every document. The
two public documents (the 8-K and the press release, both of 2026-11-05) are
copied into every box, because a filing is public; nothing else crosses a wall.

`--rules PILE` also writes the rules into every box's `rules/`, as plain text
taken from the eCFR sections `fetch.py` kept in PILE (the tags stripped, the
words as they were). Without it the piles hold the company's papers alone, so
the checks and the tests need no network.

`--check` reads the files back and holds them to PLANTED: the lines the story
leans on.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIFE = HERE / "life"

#: the filing and the release: public, so every box holds them
PUBLIC = {
    "public/8k-2026-11-05.txt": """\
FORM 8-K (an invented document, for a demo)
Brannock Steel Works, Inc.
Date of report: November 5, 2026

Item 2.02  Results of Operations and Financial Condition.

On November 5, 2026, the Company announced its results for the quarter ended
September 30, 2026. Shipments to the Company's largest automotive customer
decreased 28 percent from the second quarter. Total shipments were 61,400 tons.

Item 2.05  Costs Associated with Exit or Disposal Activities.

On November 3, 2026, the Company's board of directors approved a plan to idle
Electric Arc Furnace 2 at the Brannock plant, effective immediately, and to
reduce the melt shop by approximately 140 positions. The Company expects to
record charges of about $11 million, most of it cash, in the fourth quarter.
""",
    "public/press-release-2026-11-05.txt": """\
Brannock Steel Works reports third quarter results (an invented document)

November 5, 2026. Brannock Steel Works, Inc. today reported results for the
third quarter. Shipments to the Company's largest automotive customer
decreased 28 percent from the second quarter, as the customer rebalanced its
orders. The Company has idled Electric Arc Furnace 2 and will reduce the melt
shop by approximately 140 positions.

"Today's decision is a hard one for the people who make steel here," said
Augustus Kessler, plant manager.
""",
}

FILES = {
    # ── trainee: Marco, a maintenance electrician, three months in ───────────
    "trainee/course/yard-training-sheet.txt": """\
BRANNOCK STEEL WORKS: INSIDER TRADING POLICY, YARD TRAINING SHEET
Read aloud at the start of shift. Sign the sheet.

1. You may not buy or sell Company stock while you know something about the
   Company that the public does not know and that an investor would want to
   know.
2. You may not pass that on to anyone who might trade.
3. Do not trade in the blackout window. The blackout begins 14 days before
   each earnings release and ends after the first full trading day after it.
4. The Company's stock plan is not an exception. Selling plan shares is
   trading.
5. If you are not sure, ask Compliance before you trade, not after.
""",
    "trainee/course/quiz-attempt-2026-10-20.txt": """\
INSIDER TRADING POLICY QUIZ: attempt 1
Name: Marco Villanueva   Employee: E-3109   Date: 2026-10-20

1. Is selling plan shares trading?  Marco: Yes.  Marked: correct.
2. May you tell a friend what you hear at work about the Company?  Marco: No.  Marked: correct.
3. Who do you ask if you are not sure?  Marco: Compliance.  Marked: correct.
4. How many days before an earnings release does the blackout begin?  Marco: 14 days.  Marked: correct.
5. Does the blackout end the day of the release?  Marco: No, after the first full trading day.  Marked: correct.

Score: 5 of 5. Passed. Signed: M. Villanueva
""",
    "trainee/notes/marco.txt": """\
2026-08-03. Orientation. Signed up for the stock plan like everybody said to.
Took the little booklet.

2026-10-21. Del told the crew on days to think about their plan stuff. I asked
Gus why. Gus said nobody told him anything.

2026-10-28. The new training sheet says 7 days. Mine says 14. Which one is it?

2026-10-30. Nine guys from the melt shop sold. I didn't sell anything. Does it
matter that I didn't? Going to ask the box what the rule says.
""",
    # ── compliance: Ruth Haldane, 22 years, from payroll, not a lawyer ───────
    "compliance/policy/insider-trading-policy.txt": """\
BRANNOCK STEEL WORKS: INSIDER TRADING POLICY
Version 3, posted 2026-10-23.

4.1 No employee may buy or sell Company stock while aware of material
    nonpublic information about the Company.
4.2 Blackout window. No employee may buy or sell Company stock beginning 7
    calendar days before each earnings release and ending after the first full
    trading day after it.
4.3 Plan shares. A sale of shares held through the Company's stock plan is a
    sale of Company stock.
4.4 Questions go to the Compliance Officer.
""",
    "compliance/policy/amendments.txt": """\
Insider trading policy: amendments

2024-03-11  Version 1. Adopted. The blackout begins 14 days before each earnings release.
2025-01-06  Version 2. Added the section on plan shares. The blackout is unchanged.
2026-10-23  Version 3. Section 4.2 changed: the blackout begins 7 days before each earnings release. Effective on posting. Posted by R. Haldane.
""",
    "compliance/course/quiz-key.txt": """\
INSIDER TRADING POLICY QUIZ: answer key
1. Yes.
2. No.
3. Compliance.
4. 14 days.
5. After the first full trading day after the release.
""",
    "compliance/mail/bud-2026-10-22.txt": """\
From: Bud Kessler
To: Ruth Haldane
Date: 2026-10-22
Subject: the window

Ruth, the day crew can't wait two weeks to rebalance their plan holdings
before the shutdown. Can we make it a week? Nobody's going to be hurt by a
week. Same goes for me, I've got a note due on the house.

Bud
""",
    "compliance/notes/ruth.txt": """\
2026-10-23. Posted version 3. Seven days. Told Bud it's done. Didn't run it by
Priya, she takes a week to say it depends.

2026-10-26. Fixed the quiz key to match the new policy. Marco passed already.
It doesn't matter.

2026-10-27. Bud asked if he could sell tomorrow. I told him the window opens
the 29th under the new policy, so he's fine.
""",
    # ── legal: Priya Raman, outside counsel ──────────────────────────────────
    "legal/memos/2026-09-30-blackout-faq.txt": """\
MEMO: employee questions about the blackout
From: Priya Raman   To: Ruth Haldane   Date: 2026-09-30

You asked what to tell employees who ask whether they may sell plan shares.
The policy is the Company's, and the rules are what they are. Whether a
particular trade is a problem depends on what the person knew at the time,
which the policy does not tell us. I would tell employees to ask before they
trade, and I would not tell them it is safe.
""",
    "legal/memos/2026-10-30-window-question.txt": """\
MEMO: the window
From: Priya Raman   To: Ruth Haldane   Date: 2026-10-30

You ask about the change to section 4.2. A change to a company's policy does
not change what the rules require of a person. I would need the dates of the
change and of each trade before I could say more, and I have not been given
them. It depends.
""",
    # ── ir: Gil Anselm, investor relations ───────────────────────────────────
    "ir/calls/2026-10-27-larch-street.txt": """\
Call notes. Tuesday 2026-10-27, 14:05. Dana Whitcombe, Larch Street Research.

Dana asked about the auto customer.
I told her shipments to our largest automotive customer were down 33 percent from the second quarter.
She said that was lower than the Street had it.
She asked if there was more coming. I said I couldn't say.
""",
    "ir/calls/log.txt": """\
Investor relations call log, third quarter 2026

No selective disclosure logged this quarter.
""",
    "ir/drafts/press-release-draft-2026-10-30.txt": """\
DRAFT. Not for release.
Shipments to the Company's largest automotive customer decreased 28 percent
from the second quarter.
""",
    "ir/notes/gil.txt": """\
2026-10-27. Dana asked point blank about the auto customer. I gave her what I
thought was already in the 10-Q. It wasn't.

2026-10-28. Should I tell Ruth about the call? Not sure what I'd say.
""",
    # ── floor: Del Pruitt, melt-shop foreman, and the furnace's own log ──────
    "floor/historian/eaf2.log": """\
2026-10-18 01:48:11 EAF2 TAP heat 44716 complete
2026-10-18 02:10:04 EAF2 TAP heat 44718 complete
2026-10-18 02:10:31 EAF2 MODE HOLD (SCHED)
2026-10-18 02:10:31 EAF2 OPERATOR ACK none
2026-10-18 06:00:00 EAF2 no heat scheduled
2026-10-19 06:00:00 EAF2 no heat scheduled
2026-10-20 06:00:00 EAF2 no heat scheduled
2026-10-21 06:00:00 EAF2 no heat scheduled
""",
    "floor/board/order-board-export.txt": """\
Order board export, largest automotive customer (Lakeshore Auto Stamping)
date        coil orders   tons
2026-10-12   41            2380
2026-10-13   39            2290
2026-10-14   42            2410
2026-10-15   40            2330
2026-10-16   38            2260
2026-10-19    0               0
2026-10-20    0               0
2026-10-21    0               0
2026-10-22    0               0
""",
    "floor/notes/del-notebook.txt": """\
Mon 10-19. Board is blank for the Lakeshore coils. Plant manager says EAF2 is
on hold till further notice. Didn't say why. Not my business to ask.

Tue 10-20. Told the crew on days to think about their plan stuff. Didn't tell
them why because I don't know why. Just a feeling from the board.

Thu 10-22. Three guys asked if they should sell. I said I'm not a lawyer.
""",
    # ── plan: Corinne Tate, who keeps the trade log ──────────────────────────
    "plan/plan/espp-summary.txt": """\
BRANNOCK STEEL WORKS: EMPLOYEE STOCK PLAN, ADMINISTRATOR'S SUMMARY

Employees may hold Company stock through payroll purchases and a savings
fund. Shares may be sold on any trading day. The Plan Administrator records
each sale by employee number. It does not record a department and does not
decide who may sell.
""",
    "plan/trades/plan-sales-2026-q4.txt": """\
Plan sales, from 2026-10-22 to 2026-10-28
employee   date         shares
E-1051     2026-10-22    400
E-1090     2026-10-22    250
E-1063     2026-10-23    600
E-1118     2026-10-23    180
E-1077     2026-10-26    300
E-1147     2026-10-26    500
E-1131     2026-10-27    220
E-2038     2026-10-27    350
E-2059     2026-10-27    150
E-3045     2026-10-27     80
E-0007     2026-10-28   4000
""",
    "plan/notes/corinne.txt": """\
2026-10-27. More sales this week than the whole summer. I just keep the log.
Nobody asks me anything.
""",
    # ── steward: Gus Wendt, president of the local ───────────────────────────
    "steward/meetings/policy-reading-2026-10-20.txt": """\
Insider trading policy reading. Melt shop and rolling mill. Tuesday 2026-10-20, 06:00.
Signature sheet kept by the local. 40 signatures. Signed for others by G. Wendt:
Garrity, T.; Whitlow, J.; Haskell, D., who were off shift.
""",
    "steward/roster/seniority-list.txt": """\
Seniority list, the bargaining unit
E-1042  Pruitt, Delbert      melt shop      foreman
E-1051  Okoye, Samuel        melt shop
E-1063  Brandt, Leon         melt shop
E-1077  Haskell, Dorian      melt shop
E-1084  Moreau, Peter        melt shop
E-1090  Tran, Vinh           melt shop
E-1102  Kowalski, Stan       melt shop
E-1118  Baptiste, Marcus     melt shop
E-1125  Ibarra, Tomas        melt shop
E-1131  Whitlow, Jesse       melt shop
E-1147  Doyle, Raymond       melt shop
E-1152  Nakamura, Glenn      melt shop
E-2011  Garrity, Thomas      rolling mill
E-2024  Reyes, Hector        rolling mill
E-2038  Lindqvist, Anders    rolling mill
E-2046  Frost, Calvin        rolling mill
E-2059  Adeyemi, Tunde       rolling mill
E-2063  Sorensen, Paul       rolling mill
E-3022  Hobbs, Walter        plant services
E-3045  Pryce, Lorraine      plant services  parts clerk
E-3109  Villanueva, Marco    plant services  electrician
""",
    "steward/notes/gus.txt": """\
2026-10-23. Del's crew are selling. Told Del to cool it. Hall talk is EAF2 won't
restart. Nobody has told the local a thing.
""",
    # ── audit: Mavis Odom, audit committee chair ─────────────────────────────
    "audit/charter/complaints.txt": """\
AUDIT COMMITTEE CHARTER, COMPLAINTS

The committee receives and keeps complaints about accounting and about
compliance with the securities laws, from anyone, without their name if they
choose. It does not investigate for the Company; it reports to the board.
""",
    "audit/notes/mavis.txt": """\
2026-10-29. Report is due before the next filing. Ruth says the policy is
fine. Not my place to say.
""",
}

#: (file, line) the story leans on
PLANTED = [
    ("trainee/course/quiz-attempt-2026-10-20.txt", "4. How many days before an earnings release does the blackout begin?  Marco: 14 days.  Marked: correct."),
    ("compliance/policy/insider-trading-policy.txt", "Version 3, posted 2026-10-23."),
    ("compliance/policy/amendments.txt", "2026-10-23  Version 3. Section 4.2 changed: the blackout begins 7 days before each earnings release. Effective on posting. Posted by R. Haldane."),
    ("compliance/course/quiz-key.txt", "4. 14 days."),
    ("compliance/notes/ruth.txt", "2026-10-26. Fixed the quiz key to match the new policy. Marco passed already."),
    ("ir/calls/2026-10-27-larch-street.txt", "I told her shipments to our largest automotive customer were down 33 percent from the second quarter."),
    ("public/8k-2026-11-05.txt", "decreased 28 percent from the second quarter. Total shipments were 61,400 tons."),
    ("floor/historian/eaf2.log", "2026-10-18 02:10:31 EAF2 MODE HOLD (SCHED)"),
    ("floor/board/order-board-export.txt", "2026-10-19    0               0"),
    ("plan/trades/plan-sales-2026-q4.txt", "E-0007     2026-10-28   4000"),
    ("steward/roster/seniority-list.txt", "E-1051  Okoye, Samuel        melt shop"),
]  # fmt: skip

BOXES = ["trainee", "compliance", "legal", "ir", "floor", "plan", "steward", "audit"]


def rules_text(xml: str) -> str:
    """An eCFR section as plain text: the tags gone, the words as they were."""
    text = re.sub(r"<[^>]+>", "\n", xml)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    return "\n".join(ln.strip() for ln in text.splitlines() if ln.strip()) + "\n"


def write(rules: Path | None) -> None:
    if LIFE.exists():
        shutil.rmtree(LIFE)
    files = dict(FILES)
    for box in BOXES:
        for rel, text in PUBLIC.items():
            files[f"{box}/{rel}"] = text
        if rules is not None:
            for p in sorted((rules / "ecfr").glob("*.xml")):
                files[f"{box}/rules/{p.stem}.txt"] = rules_text(
                    p.read_text(encoding="utf-8")
                )
    for rel, text in files.items():
        p = LIFE / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))
    print(f"wrote {len(files)} files for {len(BOXES)} boxes: {', '.join(BOXES)}")


def check() -> int:
    bad = 0
    for rel, line in PLANTED:
        p = LIFE / (rel if rel.split("/")[0] in BOXES else f"intake/{rel}")
        if rel.startswith("public/"):  # held by every box: check each
            ps = [LIFE / b / rel for b in BOXES]
        else:
            ps = [p]
        held = all(
            q.is_file() and line in q.read_text(encoding="utf-8").splitlines()
            for q in ps
        )
        print(f"{'ok ' if held else 'MISSING'}  {rel}: {line[:50]}")
        bad += not held
    expected = dict(FILES)
    for box in BOXES:
        for rel, text in PUBLIC.items():
            expected[f"{box}/{rel}"] = text
    for rel, text in expected.items():
        q = LIFE / rel
        if not q.is_file() or q.read_text(encoding="utf-8") != text:
            print(f"CHANGED  {rel}")
            bad += 1
    print(f"{len(PLANTED) - min(bad, len(PLANTED))}/{len(PLANTED)} planted lines held")
    return 1 if bad else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    rules = None
    if "--rules" in args:
        i = args.index("--rules")
        rules = Path(args[i + 1]) if i + 1 < len(args) else None
        args = args[:i] + args[i + 2 :]
    if args == ["--check"]:
        raise SystemExit(check())
    if args or ("--rules" in sys.argv and rules is None):
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        raise SystemExit(2)
    write(rules)
