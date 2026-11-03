# The Johnson case: one report, five willows

Each person's willow is a chain: their files, their record, their key. This
demo passes one report between five of them, with
[share](../../adapters/stdlib/share/), and shows what each chain knows
afterwards. The people are made up, and so is everything they write down.

    python demo/johnson/make_life.py
    python demo/johnson/scene.py run --life demo/johnson/life --to /tmp/johnson

| Who | What they do | Their folder |
|---|---|---|
| **Ines Calder** | loss adjuster at Calder & Pike; the case is hers | site visit, calls, the 2024 invoice, the roofer's quote, other work |
| **Walt Brenner** | her boss: "send me the report on the Johnson case" | open cases |
| **Aurelie Stone** | claims handler at Northfield Mutual, the client | claims she handles |
| **Tamsin Reyes** | Northfield's counsel | the dispute |
| **Harold Ames** | the mediator | the mediation list |

## The scene

1. **Ines seals four answers** from her own files: the storm damage, when
   the leak was reported, whether the north slope was worked on before, and
   the roofer's quote. Each cites the line it came from. (Sealing is the
   person's act; the scene plays it through the kernel's own `seal`, as
   bernadette's stack test does.)
2. **Walt asks for the report.** She packs the four answers for Walt's key.
   Her chain gets a `sent` row; the package holds the answers, their places
   (`johnson/calls.md:3`) and fingerprints, never her files' text.
3. **It goes on.** Walt receives it (`received` on Walt's chain) and forwards
   it to Aurelie with "Reviewed, approved"; Aurelie to Tamsin, "For the
   file"; Tamsin to Harold, "Exhibit 4". Harold sees four layers, each
   signed, each by the person the layer inside it was for.
4. **A copy edited on the way** to Tamsin ($2,140 made $21,400) is refused
   where it lands, at every layer the edit reached, and the refusal is a row
   on her chain. The true copy holds.
5. **Ines finds her mistake.** Her report said the leak was reported on
   2026-03-04; her call log says 2026-03-06. She seals the right answer and
   sends a new report that `--replaces` the first. At each hop `receive`
   says who the old report went to next and which package to name, so the
   correction walks the same path out to Harold. On the way, Walt's laptop
   is replaced: Walt rotates to a new key, signed by the old one and on
   Walt's chain, and Aurelie's `receive` says `steady: 1 package that held
   … first as <the old key>, rotated since`, not a stranger.
6. **The people are the witnesses.** Ines rewrites a copy of her record:
   the seal on her wrong answer backdated, every row after it re-hashed.
   Her own `verify` still says the chain holds; that is the limit
   LIMITS.md names. But every layer of every package is signed over where
   its sender's record stood, so each person who kept one holds a pin of
   her record that she can't reach. `share witness` holds her record to
   them: the real one holds, the rewritten one is `rewritten` for Walt,
   Aurelie, Tamsin and Harold alike. Harold never had a package from Ines;
   her layer inside Tamsin's is enough.
7. **Every chain verifies**, and only Ines's holds seals: nobody along the
   way approved anything, they only received and passed on.

`test_scene.py` holds the scene to each of those, and to one more: no
package holds a line of anyone's files.

## What it found

- **A sealed answer stands for its question.** Asked the same words again,
  the kernel serves Ines's sealed answer first, as it promises, so there was
  nothing to cite for a corrected one; and a sealed answer can't be
  declined. Her correction is an answer to the question asked another way
  ("what day did Della Johnson call to report the leak"). A way to retire
  your own sealed answer would be the kernel's to add, not an add-on's.
- **A broken package's sender is only a claim.** The first run counted the
  edited copy's signer as a key Tamsin had met; a signature that doesn't
  hold proves nothing about who sent it, so now only packages that held
  count.
- **Inner signers are met only through the outer one.** Harold has never had
  a package from Ines, only from Tamsin; Harold can check Ines's signature but
  not that her key is Ines. Who a key belongs to is still learned the old
  way: in person, or from someone you already trust.
- **Witnesses only for what was sent.** A package pins its sender's record
  up to the row it was signed at. A rewrite of rows after the last package
  anyone holds is unseen until the next one goes out; and a record nobody
  was ever sent anything from has no witness but `tip-pin`.
- **A rotation has to reach the forward rule.** Walt's correction was
  packed for Walt's old key; after rotating, Walt's forward of it was refused
  as "for someone else". A forward is now good when what it wraps was for
  its signer's key or one its signed rotations leave, and a package for a
  key you rotated from is still yours at `receive`.
- **A received answer can't become yours.** The kernel seals only answers
  made from your own files' passages. Walt can pass Ines's report on and
  everyone can check it, but it never becomes Walt's own sealed answer.
  That is the kernel's promise working, and it is why the chain of who said
  what stays readable.
