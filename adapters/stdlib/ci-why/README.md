<!-- willow-addon
section: For maintainers
line: Why CI went red: the failing block pulled out of the job's log, plain, put where people look.
source: bot
added: 2026-10-24
writes: nothing
network: none
-->
# ci-why

A red CI run leaves a log of hundreds of lines and one failure somewhere in
it. This reads the log and prints only the failing part: which check, which
test or line, what it asserted and what it got.

    python adapters/stdlib/ci-why/ci_why.py LOG [--record RECORD.JSONL]
    python adapters/stdlib/ci-why/ci_why.py --record RECORD.JSONL
    gh run view JOB --log-failed | python adapters/stdlib/ci-why/ci_why.py -

`LOG` is what `adapters/stdlib/ci/ci.py run` printed, or a CI job's raw log (`-` reads it from
standard input). `RECORD.JSONL` is the CI record `adapters/stdlib/ci/ci.py` keeps: its verdict
rows say which checks failed, so the log is read only there.

    ci-why: 2 failing (tests:adapters, tests:strip); 2 blocks found

    ── tests:adapters  failing  (exit 1)
       adapters/stdlib/ci/test_contract.py::test_every_add_on_a_person_runs_is_listed_here
          >       assert run_by_people == set(COMMANDS)
          E       AssertionError: assert {'again', 'ai...'browse', ...} == {'aider', ...}
          E         Extra items in the left set:
          E         'again'
          adapters/stdlib/ci/test_contract.py:144: AssertionError

    ── mutants:aider  failing  (exit 2)
       aider: 6 of 6 killed, 0 accepted
          stale deadbeef0000: accepted, but no longer made or no longer surviving; take it out of accepted.json

| Failure | What is pulled out |
|---|---|
| pytest | the test, the line that failed (`>`), its `E` lines (the assertion and its diff), and where. Not the source around it, the dots or the timings. A very long assertion keeps its first 15 and last 8 `E` lines and says how many it left out. |
| mutants | the `stale`, `survived` and `couldn't run` lines, with the add-on's count |
| ruff | the rule, the place, the offending line, and a format check's diff |
| a Python traceback | its last frame and the error |

**Which checks failed.** From the record when you give one; otherwise from
the summary `adapters/stdlib/ci/ci.py run` prints at the end of its log. With neither (a bare
pytest log, say), a section counts as failing when it holds one of the shapes
above. A check that is `unreachable` (a tool isn't installed) did not fail,
and a passing check's output is left alone.

**It never guesses.** A check that failed in a shape this doesn't know is
said so, with that section's last lines marked as such. A failing check the
log has no section for is said. "Couldn't find a failing block" is its own
answer, and so is "the log says it passed".

**"Nothing failed" takes a whole run.** ci.py prints its summary only once
every check has run, so a log of checks without one was cut off (a job
that timed out, a run stopped partway): it is said where the log stops,
and that nothing can be said of the checks after it. A record alone can't
say whether its run finished either, so with no log it says what the record
holds and asks for the log. A bare pytest log passed only when its last
line says so.

Exit codes, the kernel's: 0 nothing failed in a whole run, or every failing
check's block is printed; 42 couldn't find a failing block for a failing
check (or for any check, when nothing says which failed), a run that may
not be whole, and a record with no verdicts; 2
refused (no such file, a record that doesn't verify, a bad command line).

**Fetching the log.** This add-on reads what it is given and goes nowhere.
Getting a job's log from the forge is one line for the person or the
workflow, `gh run view JOB --log-failed`, piped in with `-`; code that talks
to GitHub belongs in [github](../github/), not here. (The planned entry said
the add-on would reach the forge itself; building it showed the part worth
testing needs no network, and a fetcher that tests can never run would be a
promise nothing checks.)

**Uses:** the kernel's `read` and its exit codes.

**Never:** writes anything, reads the key, or goes online. It doesn't change
the log or the record it reads.
