<!-- willow-addon
section: Finding things
line: SQL straight over your record, in place: 'how many answers did I approve in March?'
source: box
added: 2026-10-29
needs: DuckDB; MIT
floor: duckdb 1.1.1; the 2020 rule names 0.2.3, built for Python 3.6 to 3.9, and 1.1.1 is the first release with a wheel for Python 3.13 (1.1.0 has none and is compiled from source)
writes: nothing
network: none
-->
# record-sql

Your record answers questions about itself: how often you asked, what was
served, what you approved and when. This puts it in front of SQL.

    pip install -r adapters/deps/record-sql/requirements.txt
    python adapters/deps/record-sql/record_sql.py --box DIR \
        "SELECT count(*) AS approved FROM record WHERE kind = 'seal'
         AND ts >= '2026-03-01' AND ts < '2026-04-01'"

**Two tables.** The record is read, and its chain checked, as the kernel
reads it; a record that doesn't verify is refused. Then its rows become two
tables in memory:

- `record`: a row for each record row, a column for every field any row
  has: `n`, `kind`, `who`, `ts` (a TIMESTAMP, UTC), `standing`, `where` and
  the rest, a field holding a list or an object as JSON;
- `served`: a row for each passage a bite served: `n`, `ts`, `id`, `where`,
  `echo`, so "which file answers me most?" is one GROUP BY.

`--tables` prints each table's columns and types.

**In place, and read only.** Nothing is copied to disk: the tables live in
DuckDB's memory and are gone when it ends. Before your SQL runs, DuckDB's
way out is shut and locked shut: no file read or written, no other database
attached, no extension installed, no network. A query can make tables of its
own, in memory, and nothing else.

On Bernadette's demo box, after one bite for each of the 42 quoted lines in
her STRIP.md:

    SELECT count(*) AS bites,
           count(*) FILTER (WHERE json_array_length(served) = 0) AS unanswered
    FROM record WHERE kind = 'bite'
    bites | unanswered
    42 | 9
    (1 row)

and `served`, grouped by `where`, puts her WhatsApp chat with Gerry first,
served five times from one passage.

**Without DuckDB** it refuses and names the install: exit 2, never a quiet
skip.

**Uses:** `read`, the record's rows and fields, and the kernel's exit codes:
0 rows came back; 42 none did; 2 refused (not a box, a record that doesn't
verify, or SQL DuckDB refused).

**Never:** writes anything, not even the record, or goes online, and never
reads the key.
