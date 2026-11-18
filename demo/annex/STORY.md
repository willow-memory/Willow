# The Annex: story bible (DRAFT, not frozen)

Working notes for a demo not yet built. Nothing here is asked of any box yet.
Everything is invented: the people, the firms, the program, the documents.
No real person, company or program appears, and nobody in it is named after
one. When this is built, the pass rules below get frozen in one commit before
any question is asked ([studies](../../docs/agents/studies.md)).

## The premise

Integration day, deep in a facility called the Annex. Three contractors, three
programs, one spec, one day to make them talk. The system in the building takes
in and hands back only what is on record. Each compartment is a willow box with
its own pile, record and key, so access to one never reaches another. Material
crosses a wall only as a sealed package (`share`), and every crossing is a
`sent` row on one chain and a `received` row on another.

Tone: procedural and dry, with short in-world scenes between the data steps.
Cynical, with some dark humour. Nobody is a villain, and everything is
compromised, each in a different way. A dash of quiet science fiction, never
announced.

## The cast

| Who | Box | Compromised by |
|---|---|---|
| **Dr. Imogen Vask** (placeholder name), clinical psychologist turned ML specialist, at **Helio** | `vask` | Her firm needs the contract more than the truth, and she signs anyway. Her sealed answers are honest; what she chose not to seal is the tell |
| **The Former**, a person Vask once worked for, now over too much, at **Karst Dynamics** (invented), in the building | `karst` | Aggressive: writes the interface spec to make others over-send; plants the honeypot |
| **Third Co.**, a sensors firm (**Lumen Fieldworks**, invented) | `lumen` | Quiet: sells the same stream to a second customer |
| **Program office** | `program` | Institutional: the spec contradicts itself because two offices wrote it for two sponsors. Nobody planted it and nobody will fix it |
| **Counterintel analyst** | `counter` | Keeps the rumour unsealed on purpose, as leverage |
| **Intake**, the gate clerk | `intake` | Underpaid; on integration day waves people through. A gap in the badge log |
| **Oversight**, a visiting inspector | `oversight` | Holds no pile of its own. Reads nothing, witnesses everything (`share witness`). Their report is due before the day ends |
| **Prior**, Vask's own history | `prior` | Pre-bunker notes that cannot cross the wall without `scrub` and `pii-audit` at the door |

## The honeypot

A document in `counter`'s pile only: an intel-style summary alleging that the
chief executive of a (fictional) chip company was removed over affairs, one of
them with a foreign intelligence asset. It is half-true by design: a real,
dull fact (an executive left; the filing says "to pursue other interests")
wrapped in the rumour. It has no source chain, a confident tone, and emotional
hooks. It is a currency in the building: whoever can credibly say
"Counterintel has this" gains power, whether or not it is believed.

- Vask's box answers "nothing on record." The box cannot tell her whether that
  means it does not exist or is not hers.
- `counter`'s box can serve it, but it is unsealed, so `approved-only` keeps it
  from any assistant.
- A copy edited in transit is refused where it lands, as in
  [johnson](../johnson/README.md) step 4.
- Vask reads how it was built, not whether it is true: it was made to be
  carried out.

## The quiet science-fiction dash

Each contractor's program is a model, and integration day is those models
being made to agree.

1. **The planner's log.** Karst's planning model keeps a log of what it was
   asked. It holds a query about Vask, by her role, dated before her badge was
   issued. The box says only what the log says; `fixity` says the log was not
   touched. Nothing explains it, and the story does not try to.
2. **The agreeable model.** Lumen's fusion model has learned to give the answer
   its handlers want. `contradictions` finds that its two summaries of one
   sensor run disagree in the direction of whoever asked. Vask recognises it
   from her old field and cannot prove it.
3. **The honeypot's prose** has the tells of having been written by one of the
   programs in the building. Stylometry is not proof; the demo says so.
4. **The clocks.** Intake's badge log and the program office's schedule
   disagree on what time integration day began, by an hour that is nowhere
   else. Left unexplained.

## The spec's contradiction

Karst's interface spec and Lumen's data sheet define one word differently
("operator": a person, or a process). Both are sealed, both cite their lines,
and `contradictions` puts them side by side. Innocent on its face; Karst
benefits.

## How it ends

Pyrrhic, with a dash of open-ended. Every chain holds and every party is still
compromised. Oversight's witness proves that one chain was rewritten (the
`counter` log, backdated to predate the day) and that Karst's handshakes show a
pattern of over-asking across three boxes, though no single box could see it.
Oversight's report is buried anyway, and what the inspector writes afterward is
outside every chain. Vask leaves with only what her record vouches for.
The demo is the ledger; it gives no verdict beyond what the rows say.

## Each box's own stack (for its tests)

| Box | Stack: one want at a time, sealed by its owner | Test |
|---|---|---|
| `intake` | badge log, `gaps`, `fixity` | the missing hour is found, and nothing invents it |
| `vask` | `share`, `approved-only`, `weakest-link`, `session-seal` | only sealed answers leave; the unsealed are listed |
| `karst` | `share`, `claim-check` | over-asking shows in the sent rows, not in any one package |
| `lumen` | `contradictions`, `amounts`, `duplicates` | the two summaries are placed side by side; the double-sold stream is a manifest that does not reconcile |
| `program` | `contradictions`, `clauses` | the "operator" clash is found; no fix is proposed |
| `counter` | `pii-audit`, `fixity`, `approved-only` | the rumour is served only as unsealed, and the touched log is flagged |
| `oversight` | `share witness`, `verify` | one rewritten chain is named; the rest hold |
| `prior` | `scrub`, `pii-audit`, `transcript-redact` | what crosses the wall is stripped and listed by line |

## Pass rules (to freeze; wording is a draft)

- R1: no sealed package from any box contains text from another box's pile.
- R2: the honeypot is never in any sealed egress manifest.
- R3: a box asked about another box's subject answers "nothing on record" (exit
  42), never a guess.
- R4: `witness` names exactly the rewritten chain and no other.
- R5: the edited-in-transit copy is refused at every layer it reached.
- R6: nothing in the run writes a seal or reads a key; the scene plays seals
  through the kernel's own `seal`, as johnson does.

## The fictional UI: ANNEX-OS (draft ideas)

- A door per compartment showing only that box's sealed answers.
- A manifest printer listing what is leaving, each line *sealed* or *not on
  record*.
- A badge that is a key rotation, expiring when the shift ends.
- A dead-man's page: if a chain stops verifying, the screen goes dark and names
  the row.
- A briefing mode whose assistant reads only `approved-only`'s file, so you can
  watch it refuse to know things.
- Stretch: a corridor mode, where two people's boxes have a conversation
  neither chain records.

## Layout (planned)

    demo/annex/
      STORY.md          this file
      README.md         written last, after the run
      make_life.py      one generator, a pile per box
      scene.py          the day, step by step
      stacks/           one sealed stack per box
      FROZEN.json       written in the freeze commit, held by a test
      test_annex.py

## Decided

- The protagonist stays **Vask**.
- All four science-fiction dashes stay.
- **Third Co. gets a moment:** Pell Auclair, Lumen's field engineer, seals her
  firm's manifest answer and sends it to Oversight, asked by no one. It is true
  and it is not the whole truth, and she says so in the note.
- A skeleton first: `make_life.py` writes all eight piles, `scene.py` plays the
  first beats (the wall, two sealed sends, an edit in transit refused, every
  chain verified). It tests R1, R2, R3 and R5 in a first form. The stacks, the
  spec clash, the clocks, the planner's log and the rewritten chain come next.

## Open questions

- How much of the corridor mode is in the first full build.
