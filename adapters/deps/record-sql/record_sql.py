"""record_sql.py: SQL straight over your record, in place, read only.

    python adapters/deps/record-sql/record_sql.py --box DIR "SQL"
    python adapters/deps/record-sql/record_sql.py --box DIR --tables

Needs DuckDB (MIT), pinned in requirements.txt beside this file:

    pip install -r adapters/deps/record-sql/requirements.txt

The record is read and its chain checked, as the kernel reads it; a record
that doesn't verify is refused. Its rows become two tables in memory, never
on disk:

- `record`: one row a record row, a column for every field any row has:
  `n`, `kind`, `who`, `ts` (a TIMESTAMP, UTC), `standing`, `where`, `hash`,
  `prev` and the rest; a field that holds a list or an object is JSON.
- `served`: one row for each passage a bite served: `n` (the bite's row),
  `ts`, `id`, `where`, `echo`.

    SELECT count(*) FROM record
    WHERE kind = 'seal' AND ts >= '2026-03-01' AND ts < '2026-04-01'

Then DuckDB's way out is shut, and locked shut, before your SQL runs: no
file, no other database, no extension, no network. A query can make tables
in memory, and they're gone when it ends; it can't write a file or reach the
record, so the record is only ever read.

`--tables` prints each table's columns and types.

If DuckDB isn't installed it refuses and names the install; it never skips
quietly. Exit codes, the kernel's: 0 rows came back; 42 none did; 2 refused
(not a box, a record that doesn't verify, or SQL DuckDB refused).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

INSTALL = "pip install -r adapters/deps/record-sql/requirements.txt"
#: the record's own fields first, in this order; any others after, sorted
FIRST = ["n", "kind", "who", "ts", "standing", "where", "family", "version"]
SHUT = [
    "SET autoinstall_known_extensions = false",
    "SET autoload_known_extensions = false",
    "SET enable_external_access = false",
    "SET lock_configuration = true",
]


def kind_of(values: list) -> str:
    """The SQL type every non-null value of a field fits."""
    seen = [v for v in values if v is not None]
    if seen and all(isinstance(v, bool) for v in seen):
        return "BOOLEAN"
    if seen and all(isinstance(v, int) and not isinstance(v, bool) for v in seen):
        return "BIGINT"
    if all(isinstance(v, str) for v in seen):
        return "VARCHAR"
    return "JSON"


def stamp(ts):
    """The kernel's '2026-03-01T10:00:00Z' as DuckDB reads a TIMESTAMP."""
    return ts.replace("T", " ").rstrip("Z") if isinstance(ts, str) else None


def tables(rows: list[dict]) -> dict[str, tuple[list[tuple[str, str]], list[tuple]]]:
    """{table: ([(column, type)], [row values])} for `record` and `served`."""
    fields = [k for k in FIRST if any(k in r for r in rows)]
    fields += sorted({k for r in rows for k in r} - set(fields))
    cols = []
    for k in fields:
        cols.append(
            (k, "TIMESTAMP" if k == "ts" else kind_of([r.get(k) for r in rows]))
        )
    values = []
    for r in rows:
        out = []
        for k, t in cols:
            v = r.get(k)
            if k == "ts":
                v = stamp(v)
            elif t == "JSON" and v is not None:
                v = json.dumps(v, ensure_ascii=False, sort_keys=True)
            out.append(v)
        values.append(tuple(out))
    served = [
        (r["n"], stamp(r.get("ts")), s.get("id"), s.get("where"), s.get("echo"))
        for r in rows
        if isinstance(r.get("served"), list)
        for s in r["served"]
        if isinstance(s, dict)
    ]
    served_cols = [("n", "BIGINT"), ("ts", "TIMESTAMP"), ("id", "VARCHAR"),
                   ("where", "VARCHAR"), ("echo", "BOOLEAN")]  # fmt: skip
    return {"record": (cols, values), "served": (served_cols, served)}


def connect(rows: list[dict]):
    """An in-memory DuckDB holding the two tables, its way out locked shut."""
    import duckdb

    con = duckdb.connect(":memory:")
    for name, (cols, values) in tables(rows).items():
        spec = ", ".join(f'"{c}" {t}' for c, t in cols)
        con.execute(f"CREATE TABLE {name} ({spec})")
        if values:
            marks = ", ".join("?" for _ in cols)
            con.executemany(f"INSERT INTO {name} VALUES ({marks})", values)
    for line in SHUT:
        con.execute(line)
    return con


def cell(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "true" if v else "false"
    return " ".join(str(v).split())


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    args: list[str] = []
    it = iter(argv)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        else:
            args.append(a)
    if (
        not opts.get("--box")
        or len(args) != 1
        or (args[0].startswith("--") and args[0] != "--tables")
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    try:
        import duckdb
    except ImportError:
        print(f"refused: record-sql needs DuckDB: {INSTALL}", file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused: the record doesn't verify:", *breaks, sep="\n  ",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    con = connect(rows)
    if args[0] == "--tables":
        for name, (cols, values) in tables(rows).items():
            print(f"{name} ({len(values)} rows)")
            for c, t in cols:
                print(f"  {c} {t}")
        return kernel.ALIVE
    try:
        got = con.execute(args[0])
        found = got.fetchall() if got.description else []
    except duckdb.Error as exc:
        print(f"refused: {' '.join(str(exc).split())}", file=sys.stderr)
        return kernel.REFUSED
    if got.description:
        print(" | ".join(d[0] for d in got.description))
    for row in found:
        print(" | ".join(cell(v) for v in row))
    print(f"({len(found)} row{'s' * (len(found) != 1)})")
    return kernel.ALIVE if found else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
