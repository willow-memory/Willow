# A stack over the five repos, 2026-11-03

**What was built.** One willow box whose pile is `/home/user`, the folder
holding all five repositories (Willow, socratic-fork, redential-cli,
glapagos, NaturalConvDataSet-fork), and a stack file of 38 steps in 8 pools
run over it with Willow's own `stack` add-on. The box was made with a scratch
key written for this session only; no real key was read, and nothing was
sealed. The record verifies (`the chain holds: 2 rows, 0 sealed`). No repo
tree was changed and nothing was committed or pushed.

| Piece | Where |
|---|---|
| the stack file | `five-repos.md` beside this report |
| the page it made (31,827 lines) | `five-stack.out` beside this report |
| the box | `five-box/` in the same scratch folder |
| run time | 1 min 36 s, 38 steps, 13 flagged with exit 42 |

The pile is 1,644 files once `.git` is skipped. Willow is 19 MB of the
28 MB and carries four made-up demo lives and hundreds of test fixtures, so
every audit over the whole box is dominated by Willow's own planted material.
The per-repo counts below separate the two.

## Real leads, by repo

**Willow**
- `CONSTITUTION.md` links a Casebook, CASEBOOK.md, five times and no such
  file exists anywhere in the repo (xref).
- Six add-ons load a sibling module with `exec(compile(...))` (browse,
  digest, live, secrets-audit, start, transcript-redact), and four readers
  build SQL with an f-string table name (bookmarks, oakenscroll, zotero,
  record-sql). risky-code lists them as leads to read, not verdicts.
- `vectors/cases.json` is over 1 MB, so the kernel can't read it (box-health).
- Everything named in CLAUDE.md and AGENTS.md exists (agents-md-check).

**redential-cli**
- the FAQ, docs/faq.md, and its four translations jump from an h1 to an h3 on their
  first question, which a screen reader's outline renders as a hole (a11y-check).
- Both alias packages depend on `@redential/cli >=0.5.0` with no lockfile
  pin (pins). Expected for an alias package, but it is the only npm range
  in the five repos without one.
- agents-md-check read `@redential/cli` in CLAUDE.md as a path. A false
  lead, worth knowing the tool does that with scoped package names.
- Only CLAUDE.md loads, for claude-code and opencode; codex, cursor,
  copilot and windsurf would load nothing (instruction-files).

**glapagos**
- Four Python ranges in `requirements.txt` (fastapi, uvicorn,
  python-multipart, flask) have no lockfile pin (pins).
- CODEOWNERS gives `CONSTITUTION.md` to the governance team and everything
  else to maintainers (codeowners).
- No instruction file for any coding agent (instruction-files).
- 45 TODO-shaped lines, mostly unticked ROADMAP.md boxes (todo).

**socratic-fork**
- No instruction file would load; `SKILL.md` is a skill, not an AGENTS.md,
  so an agent opening the repo cold reads nothing (instruction-files).
- Clean on secrets, PII, a11y and xref.

**NaturalConvDataSet-fork**
- README jumps from h1 straight to h4 (a11y-check).
- Found nothing on every question asked across the five: it is two files.

## Counts per repo, fixture noise included

| step | Willow | redential-cli | glapagos | socratic | NaturalConv |
|---|---|---|---|---|---|
| todo lines | 317 | 20 | 45 | 9 | 0 |
| risky-code places | 102 | 10 | 0 | 10 | 1 |
| xref broken | 118 | 9 | 0 | 0 | 0 |
| secrets-audit places | 140 | 6 | 1 | 0 | 0 |
| duplicate copies | 4,579 | 188 | 8 | 8 | 0 |
| contradiction rows | 14,596 | 144 | 18 | 0 | 0 |

How to read the noise: Willow's `demo/redteam/target` is planted on purpose
(the `evil-pkg` postinstall, `DEBUG = True`, `shell_exec`), its privacy and
secrets add-ons hold the words they look for, and its test fixtures hold the
dates and sums that contradict each other. redential-cli's risky-code rows
are regex `.exec(` calls, not shell. glapagos's 18 contradiction rows are
its governance deadlines (72 hours, 60 days, 90 days) paired with Willow
fixtures that share a few words. Every secrets-audit hit outside Willow is
the word `password` or `key` in a privacy test or a pattern list; no value
was shown and none looked real.

## One question, each repo answering in turn

fair-merge ranks each top-level folder on its own and deals the lists out in
turns, so Willow's volume can't bury the others:

- "who may approve": Willow answers with a test about nothing approved,
  glapagos with its Technical Council, socratic with the enterprise grade's
  audit-trail row, redential-cli with a summary test.
- "what never leaves the machine": Willow's test_it_never_dials_out,
  redential-cli's RFC 13 table of what leaves and what doesn't, socratic's
  production-grade retention row. glapagos found nothing.
- "where is the vault": why-not says the files do hold it, in Willow's
  CHANGELOG and ADDONS (the Obsidian-vault reader). First mention of
  "vault" is 2024-02-09 in the markdown add-on's card; 129 mentions in 24
  files.

## Play

people's roster, by what the files do with a name, seats Ana, Cargo, Google,
Article, Teo, Dad and Windows in its top seven: the demo families sit beside
the build tools, exactly as the card warns. pile-poetry, seeded "five repos":

    What is identical bytes or empty the card
    Own doc split n nid n start timedelta
    And not kept when the bass string object
    Makes and got returncode and is written by

and seeded "the vault is sean's key", four lines:

    Public npm publish a record byte for p
    Or rows append the clear consequential assumptions are
    When none none when one decided here root
    Written nothing set g for c c t

## What the stack doesn't do, and what's next

Every step reads the box or a repo folder by name and writes nothing into
any of them; the steps that mirror (git-history, code-comments, markdown)
were left out so the arrow stays one way, a box to a document. A second
layer would mirror each repo's git history and comments into a scratch
folder and add that to the pile, so "when did we change X" and "what does
this function say it does" answer too. The stack file is kept outside the
repos because its paths are this machine's; it could become an eighth
example under `adapters/stdlib/stack/examples/` with `--from` paths made
relative, which would need the CHANGELOG entry and FILES.md line the
add-on rules ask for.
