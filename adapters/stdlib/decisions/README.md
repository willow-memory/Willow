<!-- willow-addon
section: Trust and proof
line: A recorded no with its reason and the condition that would reopen it, so a rejection is kept, not forgotten.
source: new
added: 2026-11-01
writes: record
network: none
tags: no-install, offline, records, trust
-->
# decisions

What you decided and what you ruled out, each with its reason, so a new
question finds the old answers before anyone argues it again.

    python adapters/stdlib/decisions/decisions.py chose  --box DIR --question "Which database holds the orders?" --answer SQLite --reason "one file, nothing to run"
    python adapters/stdlib/decisions/decisions.py chose  --box DIR --question "Which database holds the orders?" --answer Postgres --reason "the orders outgrew one file" --replaces 1
    python adapters/stdlib/decisions/decisions.py no     --box DIR --question "Should we move hosting to the cloud?" --option "move now" --reason "too dear this year" --reopen-when "the hosting bill passes 500 a month"
    python adapters/stdlib/decisions/decisions.py no     --box DIR --question "Should we sell the customer data?" --option "sell it" --reason "we promised not to" --never
    python adapters/stdlib/decisions/decisions.py ask    --box DIR "what database should hold orders now"

    on the record about: what database should hold orders now
    every row stands unattested; none is approved by this
    chose, row 2 (2026-11-01T09:00:00Z): Postgres
      because: the orders outgrew one file
      asked as: Which database holds the orders? (matched: database, hold, orders)
      replaced row 1: SQLite (because: one file, nothing to run)

**`chose`** writes a `chose` row: the question, the answer and the reason, all
three required. `--replaces ROW` says it stands after an earlier decision; that
row stays on the record with its own reason, and the chain of rows is the
lineage. A row can be replaced once.

**`no`** writes a `no` row: an option ruled out and why. It is a **never**
(`--never`, a closed door) or a **not-yet** (`--reopen-when`, the condition
that would make it worth asking again), said when it's written. A no with
neither, or with both, is refused: there is no row for a no that doesn't know
which it is.

**`reopen`** (`--row ROW --because WHY`) writes a `reopen` row for a not-yet
whose condition has come true. The no stays beside it, and `ask` shows both.
A never names no condition, so it can't be reopened; if you change your mind,
write the decision with `chose`.

**`ask`** reads the rows back for a new question: the decision that stands and
the ones it replaced, every no with its reason, and each not-yet's condition,
for you to check. It shows the words; it never decides whether a condition has
come true. A row is about the question when the two hold at least half of the
shorter one's content words, the kernel's own share, counted against the shorter
text so a long line doesn't hide a short one it contains. It writes nothing, and
says which words matched. A row it can't read is named on stderr and left out.

When nothing matches it says so, and that is not the same as free to decide:
nothing was written down. The words are only compared, not understood: a
question put in other words may miss a row, and "we use X" and "we don't use X"
share words alike. Read what it shows.

Exit codes, the kernel's: `chose`, `no`, `reopen` 0; `ask` 0, or 42 when nothing
on the record is about the question; 2 refused (a record that doesn't verify, a
reason left out, a no that is neither or both kinds, a row that can't be
replaced or reopened, a bad command line).

**Uses:** the kernel's `read`, `append`, `words`, `forms`, `holds`, `FUNCTION` and
its exit codes.

**Never:** seals, approves, reads your key, or writes anything but the record's
rows, through the kernel. Every row stands unattested; only your seal, made with
`kernel.py seal`, approves anything. It keeps the words you give it, reasons
included, in the record.

**Where it comes from:** the SAFE App Store's `aristarchus`, a decision memory
that keeps the lineage and the rejections, and tells a never from a not-yet.
Its signing of rows with a shared secret is not here: in willow only the person
seals. Its database, ledger and sentence-encoder matching are not either; the
rows are the kernel's, and the match is the kernel's word share.
