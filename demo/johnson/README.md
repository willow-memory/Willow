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
2. **Walt asks for the report.** She packs the four answers for his key.
   Her chain gets a `sent` row; the package holds the answers, their places
   (`johnson/calls.md:3`) and fingerprints, never her files' text.
3. **It goes on.** Walt receives it (`received` on his chain) and forwards
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
   correction walks the same path out to Harold.
6. **Every chain verifies**, and only Ines's holds seals: nobody along the
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
  a package from Ines, only from Tamsin; he can check Ines's signature but
  not that her key is Ines. Who a key belongs to is still learned the old
  way: in person, or from someone you already trust.
- **A received answer can't become yours.** The kernel seals only answers
  made from your own files' passages. Walt can pass Ines's report on and
  everyone can check it, but it never becomes Walt's own sealed answer.
  That is the kernel's promise working, and it is why the chain of who said
  what stays readable.
