# Craft assembly: taking programs apart, and building something larger

AI agents rebuilt Photoshop, Premiere, Excel and a dozen more as the
storytold *Craft* apps, open source, in Rust. This study does the opposite,
with no model anywhere: it takes those programs apart into pieces, proves
they rebuild exactly, then assembles pieces of five of them, and the library
they share, into one program larger than any of them, by written rules
alone. Every step is checked by hash or by Cargo, and each pass rule is a
row on a kernel record.

The whole of it, with the research it answers and every number counted
from the files here, is [REPORT.md](REPORT.md), written by
[report.py](report.py).

## The claim

1. **Taken apart, nothing is lost.** Fifteen Craft apps, six commits of
   their shared library `craft-libs`, and the three other repositories the
   apps take crates from by git (24 sources since freeze 2; 21 in run 1) go
   into one store of pieces: each distinct file once, by its SHA-256. Each
   source rebuilt from the store alone hashes to the git tree it was pinned
   at.
2. **The same input gives the same bytes.** Taking apart twice gives the
   same store; assembling twice gives the same composite.
3. **Assembled, nothing breaks.** cadcraft, designcraft, effectcraft,
   filmcraft and soundcraft, and every crate they take by git, at the
   commits each pinned and all from the store, become one Cargo workspace
   with one lockfile. Every package it holds that builds in its own app
   builds in it, and every one whose tests pass in its own app passes them
   in it. What the rules leave out is said, with whether it held in its own
   app.

## How it could be wrong, and what answers it

| Threat | Answer |
|---|---|
| A rebuild that only looks right | the git tree hash of every rebuilt source, against the commit's own tree from sources.json |
| Rules fitted to the result | the rules and pass rules were frozen in FROZEN.json, in a commit of their own, before any rebuild was checked or anything was built |
| "Larger" by copying, not assembling | compose.py reads only the store; GLUE.json lists every file the rules wrote and the piece each came from; every other file is a piece byte for byte; since freeze 2, the composite's lockfile takes nothing from git, only from the store's paths and crates.io |
| A composite that builds by leaving things out | what rules 3 and 6 left out is listed, each tested in its own app too, and the results say which of it held there (`left_out_held`) |
| Tests that failed already | each package is first built and tested in its own app, rebuilt from the store, with its own Cargo.lock; only what held there counts |
| Different build settings | profiles are joined setting by setting (rule 4) and what was dropped is listed; both sides build with `CARGO_PROFILE_DEV_DEBUG=0` and `CARGO_INCREMENTAL=0` |

## What is frozen

[FROZEN.json](FROZEN.json) holds each frozen file's SHA-256, and
`test_craft_assembly.py` fails if one changes. A change is a new freeze, in
its own commit, with its reason.

- [sources.json](sources.json): the 24 sources by address, commit and git
  tree hash; never their text. [sources.py](sources.py) fetches them and
  checks each tree without git.
- [pieces.py](pieces.py): taking apart and rebuilding, and the tree hash
  (the repo's own, from [php2shell's make_trees.py](../php2shell/make_trees.py)).
- [composite.json](composite.json) and [compose.py](compose.py): the five
  apps, and the seven rules that assemble them: inherit each app's own
  workspace settings; take every crate depended on or patched in by git
  from the store, at its pinned commit (or the one its app's Cargo.lock
  holds), with its path dependencies there; leave out a package name two
  apps share; join profiles setting by setting; keep each app's root
  manifest and lockfile as files, the composite's root the one Cargo uses
  (till freeze 3, dropped); when Cargo says two versions of a crate link
  one native library, leave out the side fewer apps use; and move each
  crate to the version the apps locked (freeze 3).
- [run.py](run.py): the stages and the five pass rules, `rebuilt`,
  `same-store`, `same-composite`, `builds` and `tests`, written as verdict
  rows with the SHA-256 of the results and of every tool.

## What was seen before freeze 1

Said plainly, since it shaped the rules:

- **Structure, from the clones:** 406 Rust files are identical in two or
  more Craft repos, all from gridcraft and sheetcraft, the same app
  published twice. Different apps share no whole crate; what they share is
  `craft-libs`, pinned at six commits across the five, each crate at one
  commit only, none depending on another in its repo. 31 of the five apps'
  173 outside dependencies are pinned to different versions in different
  apps, which rule 1 leaves to Cargo.
- **The dry run.** Before the freeze, the pipeline was run on the real
  sources up to the composite's manifests, and no further: take apart,
  compose, and `cargo metadata --no-deps --offline`, which parses every
  manifest and resolves, downloads and compiles nothing. No rebuild was
  checked and nothing was built or tested. It found two bugs, both fixed
  before the freeze:
  - Python's `fnmatch` lets `*` cross a `/`, so `crates/*` named
    soundcraft's test fixtures, workspaces of their own, as members, and
    Cargo refused the composite. Members now match a folder at a time, as
    Cargo's globs do, with a fixture test that fails on the old matcher.
  - Rule 4 first kept only whole profiles every app had alike, which would
    have dropped every app's `dev` profile, and with it their opt-level 3
    for the video codecs, building the composite slower than its sources.
    It now joins profiles setting by setting.
- **What the dry run's composite held:** 140 members; 7 library crates, two
  of them (`craft-ui`, `craft-docpath`) used by all five apps; 5 left out,
  the five apps' `xtask`; `release.codegen-units`, `release.debug` and
  `release.opt-level` dropped; and each app's `.cargo/config.toml`, whose
  only setting is an `xtask` alias, not read from the composite's root.

## Freeze 2, and what was seen before it

Made after run 1 failed (below), in its own commit, with its reasons:

- **Rule 2, every git dependency.** Run 1's rule 2 rewrote only
  `craft-libs`, so the composite left Cargo to fetch effectcraft's sixteen
  filmcraft crates, designcraft's `indd-utils`, and the crates designcraft
  and effectcraft patch in, from GitHub. Now any git dependency, in a
  dependency table or a `[patch]`, is taken from the store at its commit:
  its `rev`, or for a branch, the commit its app's Cargo.lock holds (for
  designcraft's `indd-utils`, which tracks `main`). The crates it depends on
  by path at that commit come too. Three sources were added for it:
  filmcraft at `2c5ba7a726` (effectcraft's pin, not the study's filmcraft),
  `indd-utils` at `7f3060e5bc`, and storytold's fork of `winit` at
  `3d51077fd1`.
- **Rule 6, native libraries.** Run 1 found that Cargo won't hold two crates
  linking one native library. Rule 6 asks Cargo to resolve, and when it
  names such a clash, leaves out the side fewer apps use. Chosen by the
  person running the study, over dropping soundcraft whole or stopping.
- **run.py.** Packages are named `name@version` (two copies of filmcraft's
  crates, at 0.12.0 and 0.1.1, now share one build), composing includes
  rule 6, and the baseline also tests what the rules left out.

Seen before freeze 2, beyond run 1's results:

- that a workspace may hold a member and an excluded path dependency of one
  name at two versions, and `cargo build -p` tells them apart (tried on a
  two-crate workspace made for it);
- filmcraft at `2c5ba7a726` holds 26 crates in the closure effectcraft
  needs, with no git dependency of their own; `indd-utils` and the `winit`
  fork are one package each, Apache-2.0 or MIT;
- **the dry run, again:** take apart, compose, rule 6's `cargo
  generate-lockfile` (which resolves and downloads, and compiles nothing),
  and `cargo metadata --no-deps`. No rebuild was checked, nothing was built
  or tested. It found that `[patch]` tables still took `hayro`, `krilla` and
  `winit` from GitHub, which is why rule 2 now reaches them. Its composite:
  136 members; 35 crates by git, all from the store; 9 left out, the five
  `xtask`s, and soundcraft's `playback` (it asks for `cpal` 0.18) with the
  three that depend on it, `soundcraft`, `soundcraft-web` and `ui-egui`; a
  lockfile of 1,054 packages, 177 from the store's paths, 877 from crates.io,
  none from git.
- a `[patch]` reaches the whole build: in the composite, cadcraft and
  filmcraft get designcraft's `winit` fork where their own apps use
  crates.io's. That is a difference the rules make, and it stays.

## Freeze 3, and what was seen before it

Made after run 2, in its own commit, for its two lost test suites:

- **Rule 7, pins.** Run 2's lockfile was resolved fresh, so `cadcraft-io` got
  `acadrust` 0.6.7 where cadcraft locks 0.6.5. Now, once Cargo has resolved,
  each crates.io package is moved with `cargo update --precise` to the
  version the apps' own lockfiles hold for it, the highest any app locked
  in the range Cargo counts compatible. A move Cargo refuses is recorded
  (`not_pinned`), not forced.
- **Rule 5, kept roots.** Run 2 dropped each app's root `Cargo.toml` and
  `Cargo.lock`, and `filmcraft-testkit` tests that its root manifest is
  there. Now both stay, byte for byte, and every member the rules rewrite
  names the composite's root as its workspace (`package.workspace`), so the
  apps' roots are files Cargo never reads as roots.

Seen before freeze 3, beyond run 2's results: that only cadcraft locks
`acadrust`; that Cargo builds a member naming its workspace root while its
app's own `[workspace]` manifest sits above it (tried on a workspace made for
it); and the dry run, again to the lockfile and no further: 136 members, 9
left out as in run 2, 53 crates moved to the apps' versions and 11 that
Cargo wouldn't move (each needed newer by another crate, such as
`derive_arbitrary` 1.5.0 by `arbitrary`), `acadrust` at 0.6.5, filmcraft's
root manifest in place, and a lockfile of 1,053 packages, none from git.
Nothing was built or tested.

## Reproduce

    python demo/craft-assembly/sources.py --to /tmp/craft            # online: about 700 MB
    python demo/craft-assembly/sources.py --to /tmp/craft --check
    python demo/craft-assembly/run.py --work /tmp/craft --box /tmp/craft-box
    python kernel.py verify --box /tmp/craft-box

Every stage needs cargo, since composing resolves, and the network for
crates.io; `--stage pieces` stops before the builds, in about a minute.

## Results

### Run 3, 2026-10-25: every rule held

Run by [run.py](run.py) from freeze 3 (a268e52), 20:16 to 01:36 UTC. Its
outcomes are [results/run-3.json](results/run-3.json) (SHA-256
`a287e07f312bbe26…`), and its verdicts are rows 11 to 15 of the record runs
1 and 2 are on: `python kernel.py verify --box <box>` said
`the chain holds: 16 rows, 0 sealed`.

| Pass rule | Verdict | What it found |
|---|---|---|
| rebuilt | satisfied | all 24 sources rebuilt from the store hash to their pinned git trees |
| same-store | satisfied | taking apart twice gave the same store, byte for byte |
| same-composite | satisfied | composing, resolving and pinning twice gave the same composite, lockfile and all |
| builds | satisfied | all 134 of the composite's packages that build in their own app build in it |
| tests | satisfied | all 127 that pass their tests in their own app pass them in it |

Against each app on its own, the composite lost nothing and gained nothing:
every package builds and passes, or doesn't, exactly as it does alone. The
two that run 2 lost are back: `cadcraft-io`, with `acadrust` at cadcraft's
0.6.5 again (rule 7), and `filmcraft-testkit`, with filmcraft's root
`Cargo.toml` in place (rule 5).

**Rule 7 moved 53 crates** to the versions the apps locked; Cargo refused
11 moves, each a crate another needed newer, and those 11 cost no test.
**What the rules left out** is as in run 2: the five `xtask`s and
soundcraft's `playback` with the three that depend on it; of these, the
`xtask`s and `soundcraft-web` build in their own app.

**What it shows.** No model anywhere: 24 repositories taken apart into
19,743 pieces by SHA-256, each rebuilt to its exact git tree; and five of
the AI-built Craft apps, with 42 crates from four other repositories, all
from those pieces, assembled by seven written rules into one Cargo
workspace of 136 packages and one lockfile, the same bytes twice. Every
package that built and passed its tests on its own builds and passes in it.
It took three freezes, each made before its run and written down with why,
and two runs that failed, kept here beside the one that held.

### Run 2, 2026-10-25: four rules held; two packages lost their tests

Run by [run.py](run.py) from freeze 2 (3b25ab9), 12:55 to 18:37 UTC. Its
outcomes are [results/run-2.json](results/run-2.json) (SHA-256
`dbba33f2ca620d7e…`), and its verdicts are rows 6 to 10 of the same record
as run 1's, after it: `python kernel.py verify --box <box>` said
`the chain holds: 11 rows, 0 sealed`.

| Pass rule | Verdict | What it found |
|---|---|---|
| rebuilt | satisfied | all 24 sources rebuilt from the store hash to their pinned git trees |
| same-store | satisfied | taking apart twice gave the same store, byte for byte |
| same-composite | satisfied | composing and resolving twice gave the same composite, lockfile and all |
| builds | satisfied | all 134 of the composite's packages that build in their own app build in it |
| tests | **failing** | 125 of the 127 that pass their tests in their own app pass them in it; two don't |

**The composite.** Five apps, 136 packages, one Cargo workspace and one
lockfile of 1,054 packages: 177 from the store's paths and 877 from
crates.io, none from git. 42 crates came in by git, all from the store: 27
of filmcraft's at effectcraft's pin, 13 from `craft-libs` at six commits,
`indd` and the `winit` fork. Two `craft-libs` crates, `craft-ui` and
`craft-docpath`, are built once for all five apps. The store: 22,961 files,
423 MB, as 19,743 pieces, 1,662 of them in two or more sources.

**The two packages that lost their tests**, found after the run by running
each in its own app and in the composite, and diffing:

- `cadcraft-io`: one test of its 335, `damaged_dwg_opens_partially_and_says_what_it_left_out`,
  fails in the composite. Its dependency tree differs from cadcraft's own in
  patch releases only, among them `acadrust`, the DWG reader, at 0.6.7 where
  cadcraft locks 0.6.5. Pinned back to 0.6.5 in a copy of the composite,
  the test passes. The cause is the composite's lockfile, which Cargo
  resolved fresh, taking crates.io's newest compatible releases, not the
  versions each app had locked.
- `filmcraft-testkit`: one test, `root_is_the_workspace`, checks that
  filmcraft's root `Cargo.toml` exists. Rule 5 drops it, by design: the
  composite has one root. A loss the rules themselves make.

**What the rules left out**, each tested in its own app too: the five
`xtask`s (rule 3), and soundcraft's `playback`, which asks for `cpal` 0.18,
with the three that depend on it, `soundcraft`, `soundcraft-web` and
`ui-egui` (rule 6). Of these, the five `xtask`s and `soundcraft-web` build in
their own app (`left_out_held`); the rest don't build here at all.

**In their own apps** (the baseline, rebuilt from the store), against run 1:
the same packages fail, but for `filmcraft-codecs`, which failed its tests
in run 1 and passed in run 2, on the same bytes.

**What it shows.** Programs taken apart into hashed pieces rebuild exactly,
and the same pieces assemble into the same bytes. Five apps and 42 crates
from four other repositories, put together by six written rules and no
model, make one build in which everything that built alone still builds,
and 125 of 127 test suites that passed alone still pass. The two that don't
are two kinds of loss an assembly can make: a dependency resolved anew, and
a file the assembly removes.

**What a third freeze would try**, not done here: resolve the composite's
lockfile from the apps' own, each crate at the version its app locked where
Cargo can hold it; and leave each app's root manifest in place under
another name, to see whether a test that only looks for the file is the
only one that cares.

### Run 1, 2026-10-25: taking apart held; assembling failed

Run by [run.py](run.py) from the freeze (8849664), 03:52 to 06:35 UTC. Its
outcomes are [results/run-1.json](results/run-1.json) (SHA-256
`6acabe8abcfbc5be…`), and its verdicts are rows 1 to 5 of a record outside
the repo, of which `python kernel.py verify --box <box>` said
`the chain holds: 6 rows, 0 sealed`.

| Pass rule | Verdict | What it found |
|---|---|---|
| rebuilt | satisfied | all 21 sources rebuilt from the store hash to their pinned git trees |
| same-store | satisfied | taking apart twice gave the same store, byte for byte |
| same-composite | satisfied | composing twice gave the same composite, byte for byte |
| builds | **failing** | 135 of 140 packages build in their own app; none builds in the composite |
| tests | **failing** | 127 of 140 pass their tests in their own app; none in the composite |

**The store.** 21,657 files, 408 MB, became 18,975 pieces; 1,173 of them
(24.7 MB) are in two or more sources.

**Why assembling failed.** Cargo could not resolve the composite at all, so
no lockfile was made and every build stopped at once:

    package `cpal` links to the native library `alsa`, but it conflicts with
    a previous package which links to `alsa` as well

effectcraft and filmcraft use the audio crate `cpal` 0.16, which reaches ALSA
through `alsa-sys` 0.3; soundcraft uses `cpal` 0.18, through `alsa-sys` 0.4.
Cargo allows several versions of a crate in one build, which rule 1 relies
on, but only one crate in a build may link a given native library. Rule 1's
"each app keeps its own versions, so apps that pin different versions need no
choosing" is false for a crate that links one.

**What the frozen rules missed, all of it in the manifests before the
freeze:**

- the `links` conflict above;
- effectcraft takes sixteen of filmcraft's crates (its codecs, `media`,
  `color` and more) by git, at filmcraft's commit `2c5ba7a726`, not the
  `552f008d27` the study pins for filmcraft; rule 2 rewrites only
  `craft-libs`, so the composite would have fetched those from GitHub, not
  the store, and held two copies of filmcraft's codecs;
- designcraft takes `indd-utils` by git with no commit at all; only its own
  Cargo.lock says which.

So the README's "compose.py reads only the store" held for every file it
wrote, not for what the composite's manifests left Cargo to fetch.

**In their own apps**, rebuilt from the store: the packages that didn't
build are the effectcraft, filmcraft and soundcraft app binaries and
soundcraft's `playback` and `ui-egui`; those that built and failed their
tests are the `ui-egui` crates of cadcraft, designcraft and effectcraft, and
filmcraft's `av1`, `cli`, `codecs`, `engine` and `media`. They count for
neither rule.

**Seen while it ran:** the tests of effectcraft and filmcraft write scratch
files into a `target/` folder inside their app (about 1 GB for filmcraft),
whatever `CARGO_TARGET_DIR` says. And to keep the disk from filling, which
would have failed builds for want of space rather than for anything they
hold, the baseline's build folder was deleted once the baseline was over,
and finished copies (the second store and composite, the fetched sources,
the scratch above) as each was no longer read. No outcome was read from
them afterwards.
