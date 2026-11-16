# demo

Willow tried on things. Some are made-up people, with their own files and
their own questions; some are studies and runs, on real sources, that
anyone can rerun. Every person here is made up, and each says so in the
first lines of their own files. The real people, papers and records that a
study names are named as themselves, and are never made up.

A **frozen** study fixed its sources, questions and pass rules in a commit
of their own, before anything real was asked. Its tests fail if a frozen
file changes; a change is a new freeze, with its reason.

## Lives

A life is one made-up person's files, written by a `make_life.py` into
`life/`, with an answer key (`PLANTED.md`) of what is planted in them and
twenty questions (`QUESTIONS.md`) in their own words. Run
`python3 make_life.py` in the folder to write the files, and
`--check` to see the planted evidence is on disk.

- [teodora](teodora/): Teo Marinescu, 33, a bookkeeper in Leeds, with a
  partner, his daughter and a sister in Cluj. A client owes her, her cover
  lapses and her MOT is due, all in files that never say so. [Blind
  strip-down](teodora/STRIP.md), 2026-10-22.
- [bernadette](bernadette/): Bernie Halloran, 67, a retired ICU nurse in
  Ballarat, with Gerry and their grandson. Her car registration lapses on
  3 Nov 2026 and hasn't been paid. Her files are in the raw formats her apps
  leave. [Blind strip-down](bernadette/STRIP.md) through the whole stack,
  2026-10-24; `python demo/bernadette/stack.py run --to DIR` runs it.
- [hollis](hollis/): Hollis Varga, 54, an independent piano tuner in Larkfield,
  with an 81-year-old father. His hearing is going and none of his files
  say so. [Blind strip-down](hollis/STRIP.md), 2026-10-22.
- [corwin](corwin/): Corwin Tamsett, 46, a master electrician in Orrin Falls
  who keeps a ledger of lines about zero. The Planck line he means to put on
  a slide is a misquote. His files hold real papers, fetched into
  `life/sources/` by `fetch.py`. [Blind strip-down](corwin/STRIP.md),
  2026-11-06.
- [odile](odile/): Odile Varga, 61, a piano tuner and beekeeper in Calloway,
  whose father Laszlo, 88, lives with her; his weight is climbing and nobody
  has joined it up. [First strip-down](odile/STRIP.md), plain questions, no
  key, 2026-10-22.

### The boxes that lay a life

A box holds a life, or a binder, as a record you can ask, where nothing
stands as an answer until the one who holds the key seals it.

- [life-box](life-box/): the game box with a person's life for its binder.
  It lays any of the five lives above, and Marisol's from ofrenda, runs a
  week's prep at their own today, asks their own questions, and decides each
  answer with a key made for them, since they are made up. Their answer keys
  are in the folder; Marisol has none, so hers wait. It refuses a study whose
  folders are several people's, with no questions of their own (money-hour,
  stewart-crossover, johnson).
- [game-box](game-box/): a game master's binder that can be asked: monsters,
  people and four nights of session notes, the GM's own words, a prep sheet,
  two stories and a few games, all made up for the demo. The life box is its
  twin; the keys are the GM's.

## Work and research

### Frozen studies

- [php2shell](php2shell/): the kernel asked about PHP2Shell in the
  advisories' own words, tried on 16 PHP releases and seven ways. Frozen
  2026-10-24.
- [known-gaps](known-gaps/): php2shell's method pointed at the fleet's own
  twelve known security gaps. Frozen 2026-10-28.
- [google-privacy-2026-10-16](google-privacy-2026-10-16/): Google's privacy
  policy of 16 October 2026, its text against the news about it. Frozen
  2026-10-24.
- [craft-assembly](craft-assembly/): the *Craft* apps taken apart into
  pieces and assembled into one larger program, by rules alone, no model.
  Frozen 2026-10-25.
- [redteam](redteam/): seven read-only add-ons composed into one recon pass
  over a planted-weakness target, and the home of the novelty check.
  Frozen 2026-10-25.
- [ofrenda](ofrenda/): a séance where a small local model speaks for three
  ghosts, and falls silent when the kernel serves nothing. Frozen 2026-10-31.
- [stewart-crossover](stewart-crossover/): a made-up fan's files beside the
  real record of Sir Patrick Stewart's life, 2020 to 2023: is every word
  about him from a source? Frozen 2026-11-02.
- [money-hour](money-hour/): four made-up people from other demos, and the
  real markets: every figure or quote in their files held to the record.
  Frozen 2026-11-05 (its third freeze). It meets teodora, bernadette and
  hollis, so it is a study that borrows lives, not one of them.
- [percus-yevick](percus-yevick/): can a derivation in physics be found step
  by step in open sources, instead of asked of a model? Frozen 2026-11-06.
- [soil-phys-001](soil-phys-001/): can willow's tools stand in for reading
  a speculative ledger's sources? Frozen 2026-11-06.
- [shared-runs](shared-runs/): a study of remembering and sharing, run by a
  script and judged. Frozen 2026-11-11; its trials came before.

### Runs

Not frozen. Each is a record of one session.

- [five-repos](five-repos/): five repositories, this one among them, put
  through seven stacks.
- [kept](kept/): this repository asked, by one stack, what it remembers.
- [small-models](small-models/): Gemma 3 and Qwen2.5, handed willow's cards
  and teodora's files, with every result kept.
- [markets-2026-11-05](markets-2026-11-05/): a broad pile of equities and
  macro data, from public sources, fetched once. money-hour reads it.

### Tools for the demos

- [novelty.py](novelty.py): has this demo's combination of pieces been put
  together before? Every demo can run it; [test_novelty.py](test_novelty.py)
  tests it.
- [renamed.py](renamed.py): a frozen study's code, run where its add-ons now
  are, after one is renamed. A study's tests call it.

## Neither

- [johnson](johnson/): one report passed between five made-up willows, with
  share. It is a scene, not a study (nothing is frozen), and its people are
  made up for it, so it isn't one of the lives above either.
