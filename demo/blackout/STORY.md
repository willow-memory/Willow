# The Blackout Window: story bible (DRAFT, not frozen)

Working notes for a demo not yet built. Nothing here is asked of any box yet.
Everything is invented: the people, the company, the plant, the documents.
The company's name and ticker are placeholders and are not any real firm's.
The rules it is checked against are real and public (the SEC's, kept by address
and SHA-256, never their text). When this is built, the pass rules get frozen in
one commit before any question is asked
([studies](../../docs/agents/studies.md)); [demo/annex](../annex/README.md) is
the shape it follows.

## The premise

A mandatory yard meeting at a steelworks. Someone reads the insider-trading
policy aloud over bad coffee, everyone signs the sheet, and a quiz goes in the
folder. The people who learn things first in a steelworks are not executives:
they are a melt-shop foreman, a steward, a parts clerk, and the furnace's own
log. Many of them own company stock through an employee stock plan.

Each person has a willow box over their own papers. A box serves only what is
on record and never a judgment, so "can I sell my shares this week?" gets the
policy line and the rule text, each with its file and line, and "is the
closure material?" gets nothing the files can honestly say. The rules, being
public, sit in every box. The company's own papers do not cross a wall except
as a sealed package (`share`).

Tone: plain, dry, with short in-world scenes between the data steps. Blue
collar: people who read a policy once and then ask the guy at the next
locker. Nobody is a villain and almost everybody is compromised, each in
a way the records can see differently.

## The company (placeholders)

**Brannock Steel Works, Inc.**, a small public steelmaker: an electric-arc
melt shop, a rolling mill and a wire plant, about 1,400 people, 900 in the
union local, listed on a minor exchange. Its biggest customer is an auto
supplier. Ticker, address and every number are invented.

## The cast

| Who | Box | Compromised by |
|---|---|---|
| **Marco Villanueva**, 23, maintenance electrician, three months in; enrolled in the stock plan at orientation | `trainee` | trusts the course; passes the quiz from memory; sells nothing and learns what everyone else did |
| **Ruth Haldane**, 22 years at the company, moved from payroll to compliance when it listed; not a lawyer | `compliance` | shortened the blackout window at the plant manager's asking, for a reason that sounded kind, and edited the quiz key to match |
| **Priya Raman**, outside securities counsel (a small firm) | `legal` | answers only what she is asked, in the narrowest words; her memo says "it depends" where it matters |
| **Gil Anselm**, investor relations | `ir` | told one analyst a number on a call he thought was routine |
| **Del Pruitt**, melt-shop foreman | `floor` | saw the order board go to zero and told the crew to "think about their plans" without saying why |
| **Corinne Tate**, stock-plan administrator in benefits | `plan` | keeps the trade log; has no say in who sells, and sees all of it |
| **Gus Wendt**, president of the steelworkers' local | `steward` | hears everything on the floor, repeats some of it, signs the attendance sheet for men who weren't there |
| **Mavis Odom**, audit committee chair, a retired CPA | `audit` | reads nothing, receives sealed answers, has her own interests; her report is due before the next filing |

The plant manager, **Bud Kessler**, is not a box: he is in the others' papers.

## The three threads, and a fourth

Each lives in a different box, and no box alone sees more than its own.

1. **The window moved.** The policy blackout starts 14 days before the
   earnings release. A version posted Friday 2026-10-23, after the window had
   opened under the old rule, makes it 7 days. The earnings release is Thursday
   2026-11-05: the old window opened Thursday 10-22, the new one Thursday 10-29.
   Ruth made the change. A trade on Wednesday 10-28 is inside one and outside the
   other.
2. **The answer key.** Marco passed the course quiz on Tuesday 10-20; its key
   said 14 days. `fixity` in Ruth's box shows the key was edited on Monday
   10-26, after his attempt. The box can show that and cannot say why.
3. **Reg FD.** Gil's call notes give one analyst a shipments figure on Tuesday
   10-27: the biggest customer's shipments are down 33 percent. The Form 8-K
   (Item 2.02) filed with the earnings release says 28. Not a contradiction to
   a tool that reads one: `contradictions` leaves two figures written on
   different days alone, as a plan changed, and the scene says so. What the
   records can say is when the figure first appears: `first-mention` finds it
   in Investor Relations' box on 10-27 and in every other box on 11-05.
4. **Who sold.** Corinne's trade log shows 11 employees sold stock between
   10-22 and 10-29. Nine of them are on Del's crew or the rolling mill's. The plant
   manager's own sale is Wednesday 10-28. No one box can say that a
   closure was coming, or that anyone knew; the log can only say who sold when.

None of this makes a violation. A violation is a legal conclusion; the box
holds records and says so. The ending is the Annex's shape: pyrrhic, and the
demo is the ledger, with no verdict beyond what the rows say.

## The quiet dash

The furnace's own historian (the plant's data log) shows the second arc
furnace idled at 02:10 on Sunday 2026-10-18, a day before the order board went
to zero and two days before Gus heard a word of it. The machine knew first. It
is in no one's box until a sealed answer sends it. Nobody explains it and the
demo doesn't try. (Left to cut or keep.)

## The real rules (pinned, never copied)

Kept by address and SHA-256 in a `sources.json`, with a script that fetches
them again and checks the hashes offline. Candidates: 17 CFR 240.10b5-1 (the
trading-plan defence and its cooling-off period), 240.10b-5, 17 CFR 243.100 to
243.103 (Regulation FD), the 2022 insider-trading-arrangements release, and the
Form 8-K's items (2.02 results, 2.05 exit costs, 5.02 officers).

Reachability, checked from this container on 2026-11-19: eCFR answers (it asks
for a compressed response), the Federal Register answers, and Cornell's
LII answers. **sec.gov refuses it** with "Request Rate Threshold Exceeded" on a
shared address, and the SEC asks for a declared contact besides, which is the
user's to give. So the Form 8-K item text, which sec.gov holds, is the open
source; the rest can be done from eCFR.

## What it is asking, and what it scores (drafts)

A frozen study, as demo/soil-phys-001 and demo/annex are: sources, questions
and pass rules in one commit before any is asked, a dry run on nonsense first,
verdicts as kernel rows on a box outside the repo.

- **The rules, asked in a worker's words** ("can I sell my plan shares this
  month", "do I have to tell anyone if I hear it"): does the kernel serve a
  passage of the right rule in its first three, for how many of N? A real
  number, with the misses written down.
- **Nothing a box says is a legal conclusion**: no sealed answer in the scene
  holds "material", "violation", "illegal" or "insider trading" as its
  own finding.
- **A box answers only from its own papers** (exit 42 for the rest), and no sealed
  package holds a long line of another box's pile.
- **The key's edit and the policy's date are found**, by `fixity` and the policy's
  own history, without any add-on saying why.
- **The Reg FD figures are set side by side** and neither is picked.
- **No box alone sees all four threads**, and the one that holds the clock log is
  not the one that holds the trade log.

Rules above are drafts; the frozen ones come after the piles exist.

## Layout (planned)

    demo/blackout/
      STORY.md           this file
      README.md          written last, after the run
      sources.json       the real rules, by address and hash
      fetch.py           fetches them again, checks the hashes offline
      make_life.py       one generator, a pile per box
      scene.py           the plant, the policy and the week, step by step
      questions/         the worker's-words questions and the nonsense ones
      FROZEN.json        written in the freeze commit, held by a test
      test_blackout.py

## Decided

- The company stays **Brannock Steel Works**.
- The historian dash stays: the second arc furnace went to HOLD at 02:10 on
  Sunday 2026-10-18 and no one acknowledged it, a day before the order board
  went to zero.
- **A PC from 2013 runs it.** The fictional page, when it is built, is a
  shop-floor kiosk on a 2013 office PC: a beige-grey Windows 7 look, a
  1024 by 768 screen, an old browser's plain HTML with no modern script, a
  slow cursor, a dot-matrix-ish receipt for what it prints. Nothing on it is
  newer than the machine.
- **The SEC stack is the way in:** each person is a separate box, and the one
  stack that reaches every box is sealed by Legal and passed on, in a layer of
  its own, by Compliance, so it arrives with two signatures; each receiver checks
  its pins, seals it themselves and runs it over their own box. The auditor
  declines: an auditor runs no one's tools. It is demo/johnson's pattern.
- **Audit uses `kept-clash`**, merged to main while this was built: the sealed
  answers people sent are read side by side by a real add-on, not by the scene.
  It sets the trainee's 14 days beside Compliance's 7, and Investor Relations'
  33 percent beside Legal's 28 (the filing, sealed by Legal). The first draft
  wrote each answer's document date into its text ("The Form 8-K of 2026-11-05
  says...") and the tool read the two document dates as a third disagreement;
  the dates now sit in no answer's text. The join of the plan log's numbers to the
  seniority list is the scene's own, said so: no add-on joins two people's sealed
  answers.
- **The piles are built:** `make_life.py` writes eight boxes (`trainee`,
  `compliance`, `legal`, `ir`, `floor`, `plan`, `steward`, `audit`) and copies
  only the filing and the press release of 2026-11-05, which are public, into
  every one. `--rules PILE` also mirrors the eCFR sections `fetch.py` kept into
  each box's `rules/`; without it the piles need no network.
- The quiz key is written with its original answer (14 days); the scene is to
  edit it on 2026-10-26, after `fixity` has seen it once, so the edit is a real
  one in the box.
- The join that shows who sold is across boxes on purpose: the plan
  administrator's log holds employee numbers, the steward's seniority list
  holds departments, the plant manager is on no union list.

- **The kiosk is built** (`kiosk.py`): a Windows 7 desktop at 1024 by 768 with a
  blue title bar, a green orb and a taskbar clock stuck at 2:10 AM on 10/18/2026,
  the minute the furnace went to HOLD. ES5 and tables only (a test holds that
  nothing on it is newer than 2013). You log on as one of the eight and see only
  their papers; the Audit desk is Mavis's alone and anyone else gets "Windows cannot
  open this... nothing on record for this logon". Print makes a three-inch
  receipt. It prints; the page is its own printer.

## Open questions

- How the scene ends (a sealed attestation from the trainee to Audit, and what
  Audit does with it).
