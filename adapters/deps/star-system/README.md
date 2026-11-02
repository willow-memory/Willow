<!-- willow-addon
section: Reading more kinds of files
line: A friend's star-system simulation (science_bitch) run deterministically and written as cited passages: each body's Kepler period and how well the run conserves energy, angular momentum and linear momentum.
source: bot
added: 2026-10-26
needs: numpy; BSD-3-Clause
floor: numpy 2.1.0; the 2020 rule names 1.19, which has no wheel for Python 3.13 (the version the deps CI job runs), and 2.1.0 is the first that does
writes: to
network: none
-->
# star-system

An adapter for a friend's project,
[science_bitch](https://github.com/AllHailSeizure/science_bitch) — small,
self-checking physics simulations in Python. It runs that project's own
`star_system` (full unsoftened Newtonian N-body gravity, a fixed-step Yoshida
fourth-order integrator) and writes what it computes as a short markdown
document of cited lines a willow box can hold and answer from. The project's
code is imported and run, not copied here.

    pip install -r adapters/deps/star-system/requirements.txt
    python adapters/deps/star-system/star_system.py --repo DIR --to FILE \
        [--star NAME] [--planet NAME ...] [--orbits N]

`--repo` is a checkout of science_bitch. It evolves the system for `--orbits`
(default 3) orbits of the outermost body and writes to `--to`:

- each body's **Kepler period** and distance;
- how well the run **conserves** energy, angular momentum and linear momentum
  over those orbits — the same invariants the project's own tests check, with
  the tolerances it asserts.

The numbers are the simulation's. Because the integrator is fixed-step and
deterministic, the same star, planets and orbit count give the **same bytes
every run** — so a box built from the document verifies, and two runs diff
clean.

## what it reads and writes

It reads the checkout and writes only `--to` (it makes no folder — the parent
must exist); it reads no box, no key, and reaches no network. The guard holds
it to `writes: to` and `network: none` while its tests run.

Exit codes, the kernel's: `0` the document was written; `42` a close encounter
halted the run (the project's own guard) — widen the orbits; `2` refused (a bad
command line, a `--repo` that is not a science_bitch checkout, an unknown body,
or an orbit inside a star).

## its dependency, and the stand-in checkout

`numpy` (BSD-3-Clause) is the one requirement — the project's core needs it.
The floor is **2.1.0**: the 2020 rule names 1.19, which has no wheel for the
Python the deps job runs (3.13), and 2.1.0 is the first that does.

The tests run against a minimal **stand-in** checkout under
`adapters/deps/star-system/example_repo/` — a plain textbook velocity-Verlet
with a two-star, four-body catalog, there only
to give the adapter its interface so the deps gate needs no network. It is not
the real project; point `--repo` at an actual science_bitch checkout to run its
fourth-order integrator and full catalog.
