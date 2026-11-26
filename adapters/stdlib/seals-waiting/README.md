<!-- willow-addon
section: Trust and proof
line: What waits on your seal, by subject, read from the record with no row added: what kernel.py out says, for a program that asks often.
source: new
added: 2026-11-26
version: 0.1.0
writes: nothing
network: none
role: page
-->
# seals-waiting

What waits on your seal, said as `kernel.py out` says it, with nothing
written.

    python adapters/stdlib/seals-waiting/seals_waiting.py --box DIR [--json]

    waiting on your seal: proposal:<sha256>
    12 rows; 3 sealed; 1 waiting

`kernel.py out` appends a row to the record each time it is asked. That is
right for a person asking now and then; a program that asks often, such as
an assistant's door asking before each answer, grows the record by a row an
ask, and they are most of a busy record's rows. This reads the record with
the kernel's own `read`, `sealed` and `waiting` and appends nothing: the
record is the same bytes after. The rows it counts are the ones there, not
one more as `out`'s are.

`--json` prints `state` (`waiting` or `empty`), `waiting` and `sealed`, each
a subject, and `rows`. A seal counts only while its proof holds under your
key, which the kernel's `sealed` reads; nothing here reads it.

Exit codes, the kernel's: 0 nothing waits; 42 something waits on you; 2
refused (not a box, a record that doesn't read, a bad command line).

**Uses:** the kernel's `read`, `sealed` and `waiting`.

**Never:** writes a row, or anything; reads the key; or says a seal whose
proof doesn't hold.
