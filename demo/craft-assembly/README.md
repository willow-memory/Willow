# Craft assembly: taking programs apart, and building something larger

AI agents rebuilt Photoshop, Premiere, Excel and a dozen more as the
storytold *Craft* apps, open source, in Rust. This study does the opposite,
with no model anywhere: it takes those programs apart into pieces, proves
they rebuild exactly, then assembles pieces of five of them, and the library
they share, into one program larger than any of them, by written rules
alone. Every step is checked by hash or by Cargo, and each pass rule is a
row on a kernel record.

## The claim

1. **Taken apart, nothing is lost.** Fifteen Craft apps and six commits of
   their shared library, `craft-libs`, go into one store of pieces: each
   distinct file once, by its SHA-256. Each source rebuilt from the store
   alone hashes to the git tree it was pinned at.
2. **The same input gives the same bytes.** Taking apart twice gives the
   same store; assembling twice gives the same composite.
3. **Assembled, nothing breaks.** cadcraft, designcraft, effectcraft,
   filmcraft and soundcraft, and the seven `craft-libs` crates they use, at
   the commits each pinned, become one Cargo workspace with one lockfile.
   Every package that builds in its own app builds in it, and every package
   whose tests pass in its own app passes them in it.

## How it could be wrong, and what answers it

| Threat | Answer |
|---|---|
| A rebuild that only looks right | the git tree hash of every rebuilt source, against the commit's own tree from sources.json |
| Rules fitted to the result | the rules and pass rules were frozen in FROZEN.json, in a commit of their own, before any rebuild was checked or anything was built |
| "Larger" by copying, not assembling | compose.py reads only the store; GLUE.json lists every file the rules wrote and the piece each came from; every other file is a piece byte for byte |
| A composite that builds by leaving things out | what rule 3 left out is listed; the build and test rules count every package that held in its own app |
| Tests that failed already | each package is first built and tested in its own app, rebuilt from the store, with its own Cargo.lock; only what held there counts |
| Different build settings | profiles are joined setting by setting (rule 4) and what was dropped is listed; both sides build with `CARGO_PROFILE_DEV_DEBUG=0` and `CARGO_INCREMENTAL=0` |

## What is frozen

[FROZEN.json](FROZEN.json) holds each frozen file's SHA-256, and
`test_craft_assembly.py` fails if one changes. A change is a new freeze, in
its own commit, with its reason.

- [sources.json](sources.json): the 21 sources by address, commit and git
  tree hash; never their text. [sources.py](sources.py) fetches them and
  checks each tree without git.
- [pieces.py](pieces.py): taking apart and rebuilding, and the tree hash
  (the repo's own, from [php2shell's make_trees.py](../php2shell/make_trees.py)).
- [composite.json](composite.json) and [compose.py](compose.py): the five
  apps, the library's address, and the five rules that assemble them:
  inherit each app's own workspace settings, take each library crate from
  the store at its pinned commit, leave out a package name two apps share,
  join profiles setting by setting, and drop each app's root manifest and
  lockfile for the composite's one.
- [run.py](run.py): the stages and the five pass rules, `rebuilt`,
  `same-store`, `same-composite`, `builds` and `tests`, written as verdict
  rows with the SHA-256 of the results and of every tool.

## What was seen before the freeze

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

## Reproduce

    python demo/craft-assembly/sources.py --to /tmp/craft            # online: about 700 MB
    python demo/craft-assembly/sources.py --to /tmp/craft --check
    python demo/craft-assembly/run.py --work /tmp/craft --box /tmp/craft-box
    python kernel.py verify --box /tmp/craft-box

The baseline and the composite need cargo and the network (crates.io, for
the apps' outside dependencies); `--stage pieces` runs the first stage,
offline and in seconds.

## Results

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
