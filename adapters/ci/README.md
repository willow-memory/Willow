# ci

This repo's checks as a kernel record. Each check runs one fixed command and
is written as one `verdict` row through the kernel's own `append`, so the CI
record is hash-chained like any other and the kernel's `verify` checks it.

    python adapters/ci/ci.py run    [lint|tests|ports|demo ...] [--box DIR]
    python adapters/ci/ci.py verify [--box DIR]
    python adapters/ci/ci.py show   [--box DIR]

`run` with no part runs all four. The record goes in `.ci-record/` by default
(git ignores it), and the key `init` makes goes beside it in
`.ci-record.key`. A record or key inside the repo where git would count it is
refused: it would be hashed into the very files it records. CI keeps its
record in the runner's temp folder.

| Part | Gates, in this order |
|---|---|
| lint | `lint:check`, `lint:format` (ruff) |
| tests | `tests:beats` (`kernel.py test`), `tests:kernel`, `tests:docs`, `tests:adapters`, `tests:vectors` (pytest) |
| ports | `ports:java`, `ports:ts`, `ports:csharp`: `vectors/compare.py`, one port at a time |
| demo | `demo:hollis`, `demo:odile`, `demo:teodora`: each person's files made in a temporary folder and held to their `demo/*/PLANTED.md` |

Each verdict row holds the gate, its state, a hash of every file in the repo
it ran on, a hash of what the command printed, the Python version, and a
reason when it didn't pass.

**States, never collapsed:** `satisfied`; `failing` (the command failed, or
its output didn't show what it must, such as a port that `vectors/compare.py`
skipped); `unreachable` (a tool isn't installed). Neither of the last two is a
pass.

**Exit codes, the kernel's:** 0 every gate satisfied; 42 a gate unreachable
and none failing; 2 a gate failing, or a record that doesn't verify.

**Deterministic:** every row's time is the commit's, and what changes between
runs (durations, temporary folders, where the repo sits) is taken out before
the output is hashed. The same files give the same record, byte for byte.

**Uses:** the kernel's `init`, `append`, `read`, `verify`, `h256` and its exit
codes.

**Never:** writes a `seal` row, or a field a seal reader looks at (`proof`,
`subject`). Its verdicts are draft. What makes a tree count is a person
merging it.

In CI (`.github/workflows/ci.yml`) each part is its own job with its own
record, verified and uploaded as that run's artifact.
