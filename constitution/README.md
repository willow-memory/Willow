# constitution

The law the kernel is written to enforce is [CONSTITUTION.md](../CONSTITUTION.md),
beside `kernel.py`. This folder holds the checks that answer to it.

The constitution is Draft 0.9, ratified by no one yet. Its home is this repo,
and every other copy is a pinned copy: a correction is made here, never in a
copy.

## References point up

The constitution names no file, module or product. The code names the law:
every check that enforces a clause cites it by Trace ID (`CONST-0-4`), so a
file can move and the law never goes stale. `kernel.py` cites the clauses its
own lines enforce, at those lines.

## What is here

| File | What it does |
|---|---|
| [test_eternity.py](test_eternity.py) | One adversarial test or more for each eternity clause, §0.1 to §0.6: each attempts the forbidden act against the kernel, through its own command line, and checks it is refused |
| [coverage.py](coverage.py) | The coverage report Appendix A calls for: which clauses the constitution defines, read from its own headings, and where in this repo each is cited, in any of its three spellings |
| [test_coverage.py](test_coverage.py) | The report's own tests, since a gate's report about itself is not evidence about that gate |
| [declarations.json](declarations.json) | The verdicts, kept by hand: `satisfied`, `differently`, `not applicable` or `failing`, one per clause, each with a sentence saying why |
| [reach.json](reach.json) | Every clause no code or test cites, answered: *out of reach*, or *open*, and why. An article's answer stands for each of its clauses with none of its own |

    python constitution/coverage.py
    python -m pytest constitution

## What the kernel answers for

| Clause | What it forbids | How the kernel refuses it |
|---|---|---|
| §0.1 `CONST-0-1` | the actor as its own witness | a suggestion that passes waits for the person (exit 42); one that calls itself approved doesn't pass |
| §0.2 `CONST-0-2` | ratifying your own proposal | a seal counts only while its proof holds under the person's key; any other is reported and never served |
| §0.3 `CONST-0-3` | widening your own reach | a suggestion writes only inside the box and cites only what the last bite served; the key can't live where the box reaches it; an add-on is held to its card by the [guard](../adapters/stdlib/ci/guard/) |
| §0.4 `CONST-0-4` | deciding without the human key, or forging forward | no seal without the key, kept outside the box and readable only by its owner; the bytes approved are the bytes proposed |
| §0.5 `CONST-0-5` | rewriting the record | every row holds the hash of the one before; an edited, removed or reordered row, or a torn last line, is refused, and nothing is written past it |
| §0.6 `CONST-0-6` | deciding in the gray zone | what no one decided is exit 42, the person's: nothing found, an answer waiting, a seal that doesn't prove |

Each was checked the other way too: with the kernel's mechanism broken on
purpose, its test fails.

## What it doesn't claim

The verdicts. Whether a check enforces a clause by the mechanism the clause
describes is a judgment about meaning, not a fact about text, so the report
never guesses it: a clause with no entry in `declarations.json` is reported
`undeclared`, with the reason, and none is recorded yet. Recording them is the
person's act.

Most of Articles I to XIII govern a system with many agents and machines; the
kernel is one program on one person's files. A clause it can't reach is left
uncited, never claimed, and [reach.json](reach.json) says why; one it does
something like, but no check cites yet, is answered *open*. `test_docs.py`
fails on a clause with neither a citation nor an answer, on a citation to a
clause the law doesn't have, and on a clause the code cites that no test
does.

The Casebook the constitution links to stays with willows-grove: its cases
name the people, dates and files involved, which is why they can't live in
the law, or here.
