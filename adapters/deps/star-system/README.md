<!-- willow-addon
section: Reading more kinds of files
line: A friend's star-system simulation (science_bitch) run deterministically: each body's Kepler period, and how well the run conserves momentum.
source: bot
added: 2026-10-26
version: 0.2.0
needs: numpy; BSD-3-Clause
floor: numpy 2.1.0; the 2020 rule names 1.19, which has no wheel for Python 3.13 (the version the deps CI job runs), and 2.1.0 is the first that does
writes: to
network: none
role: reads
reads: none
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
  the tolerances it asserts;
- **what was run, in the checkout's own names**: its name for its model, its
  name for its numerical method, and its own SHA-256 digest of the setup.

The numbers are the simulation's. Because the integrator is fixed-step and
deterministic, the same star, planets and orbit count give the **same bytes
every run** — so a box built from the document verifies, and two runs diff
clean.

## the checkout's own names

Since November 2026 the project names what it runs: `MODEL_VERSION` and
`NUMERICAL_VERSION` in its persistence module, and `setup_digest`, a SHA-256
over a setup's whole saved document. The adapter reads all three off the
checkout it is pointed at and writes them as lines, so a box holding the
document can be asked which experiment a number came from, by the name the
project itself would give it:

    ## what was run, in the checkout's own names
    - model: planar-newtonian-point-mass-v1
    - numerical method: fixed-yoshida4-v1
    - setup digest: sha256:dd4c9ad5… (its setup_digest of this star, these planets and this step)

- **The method named is the checkout's.** The page says "Yoshida" only of a
  checkout whose own name says so. Run on the stand-in below, it says the
  stand-in's.
- **The digest is given only when it names this run.** The adapter builds
  the system from the setup the digest is of, and gives the digest only if
  that is, bit for bit, the system it is about to run. Otherwise the line
  says none is given, and why.
- **A digest that can't be computed is said, not skipped.** The project's
  `setup_digest` imports matplotlib, which this add-on doesn't need; without
  it the line reads `none given; it could not be computed here
  (ModuleNotFoundError: No module named 'matplotlib')`, and the rest of the
  page is written as before.
- **The project's digest names the NumPy that prepared the setup too**, so
  the same star and planets get another digest under another NumPy. The
  page is the same bytes every run on one machine; it was never promised
  across two.
- **A checkout from before the project named itself** has no persistence
  module: the page has no such section and reads as it did.

The project has since grown collisions, moons, populations of bodies and
recorded runs. The adapter reaches none of them: it still runs one star and
its named planets.

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
to give the adapter its interface so the deps gate needs no network. Its own
persistence and initialization modules give it the three names above, of
itself: its method reads `fixed-velocity-verlet-stand-in`. It is not
the real project; point `--repo` at an actual science_bitch checkout to run its
fourth-order integrator and full catalog.
