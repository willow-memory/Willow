# Craft assembly: the full report

Written by [report.py](report.py) from this folder's own files, the same bytes every run. Every number below is counted from them by it; none was typed. What [willow](../../README.md)'s own tools say of it is in [results/checks.md](results/checks.md).

## In short

No model anywhere: 24 repositories, the AI-built Craft apps and what they are built from, taken apart into 19,743 pieces by SHA-256 (22,961 files, 423 MB; 1,662 pieces in two or more sources), and 24 of 24 rebuilt from those pieces alone to their exact git trees. Then 5 of the apps (cadcraft, designcraft, effectcraft, filmcraft, soundcraft), with 42 crates they take by git, all from the same pieces, assembled by written rules into one Cargo workspace of 136 packages: in run 3, 134 of the 134 packages that build in their own app build in it, and 127 of the 127 whose tests pass in their own app pass them in it. Every pass rule held. It took 3 freezes, each made before its run, and 2 runs that failed, kept beside the one that held.

| Run | Freeze | When (UTC) | rebuilt | same-store | same-composite | builds | tests |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 2026-10-25T03:52:35Z | satisfied | satisfied | satisfied | **failing** | **failing** |
| 2 | 2 | 2026-10-25T12:55:24Z | satisfied | satisfied | satisfied | satisfied | **failing** |
| 3 | 3 | 2026-10-25T20:16:14Z | satisfied | satisfied | satisfied | satisfied | satisfied |

## 1. Why: AI rebuilding large programs

Quoted whole from [BACKGROUND.md](BACKGROUND.md), written before the study; its facts are from search summaries, as it says, and nothing here checks them.

Written 2026-10-24, before the study, as the reason for it. In 2026, AI agents went from writing functions to rebuilding whole programs: a C compiler, a browser engine, an 800K-line runtime, and in October a free clone of most of Adobe Creative Cloud. A rough first version now takes days to weeks. A production-grade one still takes months, and what makes either possible is a precise, checkable target: a spec, a test suite, real files to round-trip. Whoever holds the tests can rebuild the program, which is pressuring both closed-source moats and copyleft licenses, and no court has ruled yet.

Note: this environment could not open the article pages, so the facts below come from search-engine summaries of the pages named. Check a page before quoting a number from it.

### Desktop apps: the Adobe clones (Oct 2026)

In early October 2026 one engineer, Brandon Thomas of the ArtCraft project, released free, open-source Rust clones of most of Adobe Creative Cloud, written mostly by AI. The Photoshop clone, PhotoCraft, went from first commit (30 Sep) to four releases by 7 Oct (cloudmagazin, PetaPixel).

| Clone | Stands in for | Reported state |
| --- | --- | --- |
| PhotoCraft | Photoshop | Layers, masks, layer styles, smart objects, brush engine; 34 tools, 27 blend modes; 134 of 135 real test files saved back byte for byte |
| LightCraft | Lightroom (not Classic) | Alpha |
| FilmCraft | Premiere Pro | Alpha; built by prompting Claude Opus, in Rust |
| Others | Illustrator, After Effects, InDesign, Acrobat | Alpha; names differ between reports |
| Later | Word, Excel, PowerPoint, AutoCAD, Pro Tools | Secondhand report only |

**How it was built.** The project says it is clean-room: Photoshop was studied only for behavior and appearance, from public specs. Its AGENTS.md forbids copying code, shaders, color profiles or assets. Thomas reportedly used Claude Opus 5.5 with Rust, and roughly 60–75% of commits list Claude as co-author; the sources conflict on the share and the model attribution is unverified.

**How good it is.** Alpha. A reviewer called it "glitchy, but real, Photoshop" (AppleInsider, Gizmodo). The project itself claims a quarter to a third of professional work. File compatibility, color management and print standards are the hard part, with about a hundred open issues there.

**Pushback.** Critics on Hacker News and Reddit question the quality, and some say the free apps advertise an AI-credits business. No Adobe statement has been reported. Copyright, trade dress and the PSD format are the open legal questions (Plagiarism Today).

### Other large agent-built systems

Three projects set the pattern before the Adobe clones: many agents, a shared repo, a test suite as the boss, and a long run.

| Project | When | Scale | Cost and time | Caveats |
| --- | --- | --- | --- | --- |
| GitHub Copilot runtime port | Sep 2026 | TypeScript rewritten as 800K+ lines of production Rust, 128 PRs | About $120K in tokens plus about 3 weeks of a developer's time, over 14.5 weeks | A few dozen regressions shipped |
| Anthropic C compiler | Feb 2026 | 16 parallel Claude Opus 4.6 agents wrote a Rust C compiler that builds Linux 6.9 for x86, ARM and RISC-V | About $20K, about 2,000 sessions | "Almost" autonomous (InfoQ); may echo existing compilers (shape-of-code) |
| Cursor FastRender browser | Jan 2026 | 1.3M–3M lines of Rust from thousands of agents | A few weeks; longest run about a week | "Kind of" works; 88% CI failure rate reported; may lean on Servo parsers and QuickJS |

Smaller ports show the same split between fast first output and slow finishing: a C-to-Rust library port reached 25K lines in two days (Rubin/LSST), while an agent's Rust port of ScanCode ran faster but returned wrong results (AboutCode).

### Measuring it: MirrorCode

MirrorCode, from Epoch AI and METR, found that agents can rebuild real programs without their source when given a detailed, checkable spec.

- **Setup:** the agent may run the original program but not read it, and must rebuild it whole. About 25 targets: Unix tools, serializers and query tools, bioinformatics, interpreters, static analysis, crypto, compression.
- **Grading:** end-to-end tests from the original's test suite, real data and LLM-generated cases.
- **Best result:** Claude Opus 4.6 rebuilt gotree, a Go bioinformatics toolkit of about 16K lines with 40+ commands. Epoch puts the human effort at 2–17 weeks.
- **Limits:** bigger targets such as Pkl stayed unsolved. Each attempt gets up to 10B tokens and 7 days; more compute kept helping.

### The licensing fight

An AI clean-room rewrite can move code from one license to another, and no court has said whether that holds.

| Case | When | What happened |
| --- | --- | --- |
| PhotoCraft and the Adobe clones | Oct 2026 | Clean-room from behavior and public specs; copyright, trade dress and the PSD format are untested |
| claw-code | After 31 Mar 2026 | After Claude Code's source leaked, a self-described clean-room Python rewrite, with a Rust port under way; widely forked |
| chardet 7.0 | Mar 2026 | The LGPL library was rewritten with Claude Code from a design document and released as MIT. Original author Mark Pilgrim filed "No right to relicense this project" |
| Malus.sh | Feb 2026 (FOSDEM) | Satirical but working "clean room as a service": one set of agents reads the docs, another writes the code |

The US Supreme Court declined *Thaler* in March 2026, leaving purely AI-made works without copyright. So a fully AI-written clone may itself belong to no one.

### What it means

- **The test suite is the moat.** Every success above had a precise target: GCC's torture tests, a program to probe, 135 real PSD files. Hard-to-specify parts (color management, print, file quirks) are where the clones fall short.
- **First pass in days, finish in months.** The last 25–75% of professional features is where the cost and the regressions are.
- **Provenance is the open question.** Clean-room claims rest on AGENTS.md rules and commit logs, not on anything a court has tested.
- **For Willow:** this matches the freeze-first rule in AGENTS.md. A FROZEN.json of questions and pass rules is the same kind of checkable target MirrorCode grades against, and kernel rows with SHA-256 are the kind of provenance record the clean-room disputes lack.

## 2. Before the study

The research's repositories, Apache-compatible licences only, were made into a kernel box and asked questions; the script that did it became the `repo-pile` add-on, and running it found two things `privacy` missed. Quoted whole from [CHANGELOG.md](../../CHANGELOG.md):

> - `repo-pile`: a list of public repositories made into a box you can ask.
>   Each is cloned, kept only when its own licence file grants one an
>   Apache-2.0 project can use (anything else, or none, is left out and said
>   why), and its docs made the pile; the kernel makes the box, and scan
>   indexes the docs and the whole source. Then ask, bite, quote, report,
>   check and backup are willow's own add-ons over it, what they print
>   scrubbed by privacy. It never reads the key or seals. (#37)

> - `privacy` also withholds a national phone number written from its 0 in
>   groups (`0113 555 0122`, `07700 900123`: 10 or 11 digits), and a bank
>   number after its label (sort code, account number, acct, a/c, routing),
>   keeping the label so the line still reads. Its card already said bank
>   numbers; only IBANs were caught. Found when repo-pile was run on the demo
>   lives, where 64 phone numbers and 121 bank numbers got through; on 3,165
>   docs from 44 public repositories neither shape matched anything. (#37)

## 3. The study's claim, and how it could be wrong

Quoted whole from [README.md](README.md), written before the runs.

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

| Threat | Answer |
|---|---|
| A rebuild that only looks right | the git tree hash of every rebuilt source, against the commit's own tree from sources.json |
| Rules fitted to the result | the rules and pass rules were frozen in FROZEN.json, in a commit of their own, before any rebuild was checked or anything was built |
| "Larger" by copying, not assembling | compose.py reads only the store; GLUE.json lists every file the rules wrote and the piece each came from; every other file is a piece byte for byte; since freeze 2, the composite's lockfile takes nothing from git, only from the store's paths and crates.io |
| A composite that builds by leaving things out | what rules 3 and 6 left out is listed, each tested in its own app too, and the results say which of it held there (`left_out_held`) |
| Tests that failed already | each package is first built and tested in its own app, rebuilt from the store, with its own Cargo.lock; only what held there counts |
| Different build settings | profiles are joined setting by setting (rule 4) and what was dropped is listed; both sides build with `CARGO_PROFILE_DEV_DEBUG=0` and `CARGO_INCREMENTAL=0` |

## 4. The sources

24 sources, pinned 2026-10-25 by address, commit and git tree in [sources.json](sources.json), never their text: 15 apps, 6 commits of their shared `craft-libs`, and 3 repositories the apps take crates from by git. The composite's apps are marked.

| Source | Commit | Address |
|---|---|---|
| artcraft | 1f969a9224 | https://github.com/storytold/artcraft |
| **cadcraft** | b9f96d3dd3 | https://github.com/storytold/cadcraft |
| **designcraft** | c313c53497 | https://github.com/storytold/designcraft |
| drawcraft | dae0edb39c | https://github.com/storytold/drawcraft |
| **effectcraft** | eb5108786b | https://github.com/storytold/effectcraft |
| figcraft | 10702311f3 | https://github.com/storytold/figcraft |
| **filmcraft** | 552f008d27 | https://github.com/storytold/filmcraft |
| gridcraft | 3099df934e | https://github.com/storytold/gridcraft |
| lightcraft | 23f54803e6 | https://github.com/storytold/lightcraft |
| pdfcraft | c894928e6f | https://github.com/storytold/pdfcraft |
| photocraft | 1c3db2e5c3 | https://github.com/storytold/photocraft |
| sheetcraft | 10bec74810 | https://github.com/storytold/sheetcraft |
| slidecraft | 7be391a1be | https://github.com/storytold/slidecraft |
| **soundcraft** | 93800e0764 | https://github.com/storytold/soundcraft |
| wordcraft | cf2fe4733e | https://github.com/storytold/wordcraft |
| craft-libs@5c874d51ee | 5c874d51ee | https://github.com/storytold/craft-libs |
| craft-libs@82a24b006e | 82a24b006e | https://github.com/storytold/craft-libs |
| craft-libs@9f75d3dc19 | 9f75d3dc19 | https://github.com/storytold/craft-libs |
| craft-libs@d991bf6792 | d991bf6792 | https://github.com/storytold/craft-libs |
| craft-libs@e9546e191d | e9546e191d | https://github.com/storytold/craft-libs |
| craft-libs@f0ad6c1e1d | f0ad6c1e1d | https://github.com/storytold/craft-libs |
| filmcraft@2c5ba7a726 | 2c5ba7a726 | https://github.com/storytold/filmcraft |
| indd-utils@7f3060e5bc | 7f3060e5bc | https://github.com/storytold/indd-utils |
| winit@3d51077fd1 | 3d51077fd1 | https://github.com/storytold/winit |

## 5. The freezes

Each freeze is the SHA-256 of the study's tools, held in [FROZEN.json](FROZEN.json) and by a test, committed before its run. A run's freeze below is found by hashing: the freeze whose files hash as the tools on that run's verdict rows did.

| Freeze | Commit | Why | Run judged by it |
|---|---|---|---|
| 1 | 8849664 | the first: before any run | 1 |
| 2 | 3b25ab9 | after run 1 failed to resolve: rule 2 for every git dependency and patch, rule 6 for native-library clashes, three sources added, run.py's package specs and wider baseline | 2 |
| 3 | not in FROZEN.json | after run 2 lost two test suites: rule 7 pins each crate to the version the apps locked; rule 5 keeps each app's root Cargo.toml and Cargo.lock, members naming the composite root | 3 |

What was seen before each, quoted whole from [README.md](README.md):

### What was seen before freeze 1

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

### Freeze 2, and what was seen before it

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

### Freeze 3, and what was seen before it

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

## 6. The runs, counted

|  | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| sources rebuilt to their trees | 21 of 21 | 24 of 24 | 24 of 24 |
| files taken apart | 21,657 | 22,961 | 22,961 |
| pieces in the store | 18,975 | 19,743 | 19,743 |
| pieces in two or more sources | 1,173 | 1,662 | 1,662 |
| composite members | 140 | 136 | 136 |
| crates from outside the apps | 7 | 42 | 42 |
| left out by the rules | 5 | 9 | 9 |
| a lockfile resolved | **no** | yes | yes |
| crates moved to the apps' versions | 0 | 0 | 53 |
| moves Cargo refused | 0 | 0 | 11 |
| packages tried alone | 140 | 145 | 145 |
| packages tried in the composite | 140 | 136 | 136 |
| build alone, and in the composite | 0 of 135 | 134 of 134 | 134 of 134 |
| pass alone, and in the composite | 0 of 127 | 125 of 127 | 127 of 127 |
| results SHA-256 | `6acabe8abcfbc5be…` | `dbba33f2ca620d7e…` | `a287e07f312bbe26…` |

**Run 1.** Lost builds: all 135. Lost tests: all 127. Outcomes in the composite that differ from the app alone: 135.

**Run 2.** Lost builds: none. Lost tests: `cadcraft/cadcraft-io`, `filmcraft/filmcraft-testkit`. Outcomes in the composite that differ from the app alone: 2.

**Run 3.** Lost builds: none. Lost tests: none. Outcomes in the composite that differ from the app alone: none.

## 7. Run 3, the composite

| App | Members | Build alone | Build in it | Pass alone | Pass in it |
|---|---|---|---|---|---|
| cadcraft | 15 | 15 | 15 | 14 | 14 |
| designcraft | 20 | 20 | 20 | 19 | 19 |
| effectcraft | 35 | 34 | 34 | 33 | 33 |
| filmcraft | 53 | 52 | 52 | 48 | 48 |
| soundcraft | 13 | 13 | 13 | 13 | 13 |

**Crates from outside the apps**, each from the store, with the apps that use it:

| Crate | From | Used by |
|---|---|---|
| `craft-atomic` | craft-libs@e9546e191d | designcraft |
| `craft-cms` | craft-libs@e9546e191d | designcraft |
| `craft-docpath` | craft-libs@82a24b006e | cadcraft, designcraft, effectcraft, filmcraft, soundcraft |
| `craft-media` | craft-libs@f0ad6c1e1d | filmcraft, soundcraft |
| `craft-pdf` | craft-libs@9f75d3dc19 | designcraft, effectcraft |
| `craft-print` | craft-libs@d991bf6792 | designcraft |
| `craft-ui` | craft-libs@5c874d51ee | cadcraft, designcraft, effectcraft, filmcraft, soundcraft |
| `filmcraft-aac` | filmcraft@2c5ba7a726 | effectcraft |
| `filmcraft-ac3` | filmcraft@2c5ba7a726 | other crates here, by path |
| `filmcraft-av1` | filmcraft@2c5ba7a726 | effectcraft |
| `filmcraft-bitstream` | filmcraft@2c5ba7a726 | other crates here, by path |
| `filmcraft-cfb` | filmcraft@2c5ba7a726 | other crates here, by path |
| `filmcraft-codecs` | filmcraft@2c5ba7a726 | effectcraft |
| `filmcraft-color` | filmcraft@2c5ba7a726 | effectcraft |
| `filmcraft-dnx` | filmcraft@2c5ba7a726 | other crates here, by path |
| `filmcraft-frame` | filmcraft@2c5ba7a726 | effectcraft |
| `filmcraft-geom` | filmcraft@2c5ba7a726 | effectcraft |
| `filmcraft-h264` | filmcraft@2c5ba7a726 | other crates here, by path |
| `filmcraft-h264enc` | filmcraft@2c5ba7a726 | effectcraft |
| `filmcraft-hevc` | filmcraft@2c5ba7a726 | effectcraft |
| `filmcraft-interchange` | filmcraft@2c5ba7a726 | effectcraft |
| `filmcraft-isobmff` | filmcraft@2c5ba7a726 | effectcraft |
| `filmcraft-matroska` | filmcraft@2c5ba7a726 | other crates here, by path |
| `filmcraft-media` | filmcraft@2c5ba7a726 | effectcraft |
| `filmcraft-mpeg2v` | filmcraft@2c5ba7a726 | other crates here, by path |
| `filmcraft-mpegts` | filmcraft@2c5ba7a726 | other crates here, by path |
| `filmcraft-mxf` | filmcraft@2c5ba7a726 | other crates here, by path |
| `filmcraft-ogg` | filmcraft@2c5ba7a726 | other crates here, by path |
| `filmcraft-opus` | filmcraft@2c5ba7a726 | effectcraft |
| `filmcraft-project` | filmcraft@2c5ba7a726 | effectcraft |
| `filmcraft-prores` | filmcraft@2c5ba7a726 | effectcraft |
| `filmcraft-testkit` | filmcraft@2c5ba7a726 | other crates here, by path |
| `filmcraft-time` | filmcraft@2c5ba7a726 | effectcraft |
| `filmcraft-vp9` | filmcraft@2c5ba7a726 | effectcraft |
| `hayro` | craft-libs@9f75d3dc19 | designcraft |
| `hayro-cmap` | craft-libs@9f75d3dc19 | designcraft |
| `hayro-interpret` | craft-libs@9f75d3dc19 | designcraft |
| `hayro-jbig2` | craft-libs@9f75d3dc19 | designcraft, effectcraft |
| `hayro-syntax` | craft-libs@9f75d3dc19 | designcraft, effectcraft |
| `indd` | indd-utils@7f3060e5bc | designcraft |
| `krilla` | craft-libs@9f75d3dc19 | designcraft |
| `winit` | winit@3d51077fd1 | designcraft |

**Left out by the rules**, and whether it built in its own app:

| Member | Why | Built alone |
|---|---|---|
| `cadcraft/xtask` | the name xtask is in 5 apps | yes |
| `designcraft/xtask` | the name xtask is in 5 apps | yes |
| `effectcraft/xtask` | the name xtask is in 5 apps | yes |
| `filmcraft/xtask` | the name xtask is in 5 apps | yes |
| `soundcraft/apps/soundcraft` | it depends on a member left out for alsa | no |
| `soundcraft/apps/soundcraft-web` | it depends on a member left out for alsa | yes |
| `soundcraft/crates/playback` | it asks for cpal 0.18, which links alsa, as cpal 0.16 does in more apps | no |
| `soundcraft/crates/ui-egui` | it depends on a member left out for alsa | no |
| `soundcraft/xtask` | the name xtask is in 5 apps | yes |

**Rule 7 moved 53 crates** to the version the apps locked: `acadrust 0.6.7 -> 0.6.5`, `arbitrary 1.5.0 -> 1.4.2`, `basic-udev 0.1.3 -> 0.1.2`, `cc 1.10.0 -> 1.6.0`, `clipboard-win 5.4.3 -> 5.4.1`, `combine 4.6.9 -> 4.6.8`, `crc32fast 1.5.3 -> 1.5.2`, `deranged 0.5.9 -> 0.5.8`, `equivalent 1.0.3 -> 1.0.2`, `find-msvc-tools 0.1.15 -> 0.1.14`, `icu_provider 2.4.0 -> 2.3.1`, `litrs 1.0.1 -> 1.0.0`, `lyon_geom 1.0.20 -> 1.0.19`, `lyon_tessellation 1.0.23 -> 1.0.22`, `memmap2 0.9.12 -> 0.9.11`, `mio 1.2.4 -> 1.2.3`, `num_threads 0.1.8 -> 0.1.7`, `open 5.4.5 -> 5.4.4`, `powerfmt 0.2.1 -> 0.2.0`, `redox_syscall 0.9.5 -> 0.9.4`, `rmcp 3.7.0 -> 3.5.0`, `rmcp-macros 3.7.0 -> 3.5.0`, `roxmltree 0.21.2 -> 0.21.1`, `rustls-native-certs 0.8.5 -> 0.8.4`, `rustls-webpki 0.103.16 -> 0.103.15`, `schannel 0.1.30 -> 0.1.29`, `schemars 1.2.3 -> 1.2.2`, `smallvec 1.16.4 -> 1.16.2`, `syn 3.0.9 -> 3.0.6`, `thin-vec 0.2.21 -> 0.2.20`, `tokio 1.54.1 -> 1.53.2`, `tokio-util 0.7.20 -> 0.7.19`, `toml 1.1.8+spec-1.1.0 -> 1.1.6+spec-1.1.0`, `toml_edit 0.25.17+spec-1.1.0 -> 0.25.15+spec-1.1.0`, `toml_parser 1.1.5+spec-1.1.0 -> 1.1.3+spec-1.1.0`, `toml_writer 1.1.3+spec-1.1.0 -> 1.1.2+spec-1.1.0`, `typed-path 0.12.4 -> 0.12.3`, `unicode-ident 1.0.27 -> 1.0.26`, `unicode-normalization 0.1.26 -> 0.1.25`, `ureq 3.5.0 -> 3.4.2`, `ureq-proto 0.6.5 -> 0.6.4`, `uuid 1.29.0 -> 1.27.0`, `wat 1.262.0 -> 1.261.0`, `webbrowser 1.2.5 -> 1.2.4`, `webpki-root-certs 1.0.11 -> 1.0.9`, `zbus_names 4.3.5 -> 4.3.4`, `zerocopy 0.8.63 -> 0.8.61`, `zeroize 1.9.1 -> 1.9.0`, `zip 7.4.0 -> 7.2.0`, `zip 9.1.0 -> 9.0.5`, `zopfli 0.8.4 -> 0.8.3`, `zvariant 5.15.1 -> 5.15.0`, `zvariant_derive 5.15.1 -> 5.15.0`.

**Cargo refused 11 moves**, each a crate another needed newer: `derive_arbitrary 1.5.0 -> 1.4.2`, `icu_locale_core 2.4.0 -> 2.3.0`, `rustls 0.23.46 -> 0.23.45`, `schemars_derive 1.2.3 -> 1.2.2`, `serde_spanned 1.1.2 -> 1.1.1`, `tinystr 0.8.5 -> 0.8.4`, `toml_datetime 1.1.2+spec-1.1.0 -> 1.1.1+spec-1.1.0`, `yoke 0.8.4 -> 0.8.3`, `zerocopy-derive 0.8.63 -> 0.8.61`, `zerovec 0.11.9 -> 0.11.8`, `zerovec-derive 0.11.7 -> 0.11.6`.

**Profile settings dropped** (rule 4), since the apps set them differently: `release.codegen-units`, `release.debug`, `release.opt-level`.

## 8. What each run found, in the words written after it

Quoted whole from [README.md](README.md), which was written by hand after each run; [results/checks.md](results/checks.md) holds it to the counts above.

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

## 9. The record

The verdicts are rows on a kernel record kept outside the repo; [results/record.jsonl](results/record.jsonl) is a copy of it, without its key. Read by the kernel's own `read`: the chain holds, 16 rows, 0 of them seals. Each run's rows name the SHA-256 of its results, and each results file above hashes to it.

| Row | When (UTC) | Gate | State | Results |
|---|---|---|---|---|
| 0 | 2026-10-25T03:52:35Z | boot | - | - |
| 1 | 2026-10-25T03:52:35Z | craft-assembly:rebuilt | satisfied | results/run-1.json |
| 2 | 2026-10-25T03:52:35Z | craft-assembly:same-store | satisfied | results/run-1.json |
| 3 | 2026-10-25T03:52:35Z | craft-assembly:same-composite | satisfied | results/run-1.json |
| 4 | 2026-10-25T03:52:35Z | craft-assembly:builds | failing | results/run-1.json |
| 5 | 2026-10-25T03:52:35Z | craft-assembly:tests | failing | results/run-1.json |
| 6 | 2026-10-25T12:55:24Z | craft-assembly:rebuilt | satisfied | results/run-2.json |
| 7 | 2026-10-25T12:55:24Z | craft-assembly:same-store | satisfied | results/run-2.json |
| 8 | 2026-10-25T12:55:24Z | craft-assembly:same-composite | satisfied | results/run-2.json |
| 9 | 2026-10-25T12:55:24Z | craft-assembly:builds | satisfied | results/run-2.json |
| 10 | 2026-10-25T12:55:24Z | craft-assembly:tests | failing | results/run-2.json |
| 11 | 2026-10-25T20:16:14Z | craft-assembly:rebuilt | satisfied | results/run-3.json |
| 12 | 2026-10-25T20:16:14Z | craft-assembly:same-store | satisfied | results/run-3.json |
| 13 | 2026-10-25T20:16:14Z | craft-assembly:same-composite | satisfied | results/run-3.json |
| 14 | 2026-10-25T20:16:14Z | craft-assembly:builds | satisfied | results/run-3.json |
| 15 | 2026-10-25T20:16:14Z | craft-assembly:tests | satisfied | results/run-3.json |

No row is sealed. Sealing is the person's, with their key, and nothing in this study, this report or its checks reads the key.

## 10. How this report was made

| Input | SHA-256 |
|---|---|
| [sources.json](sources.json) | `9d5e7dcffd1c711b…` |
| [composite.json](composite.json) | `e6ae01d871269648…` |
| [FROZEN.json](FROZEN.json) | `496c9a89f4af4048…` |
| [README.md](README.md) | `1e24c7c5eeccde22…` |
| [BACKGROUND.md](BACKGROUND.md) | `cb48d9fe68e4d40c…` |
| [results/run-1.json](results/run-1.json) | `6acabe8abcfbc5be…` |
| [results/run-2.json](results/run-2.json) | `dbba33f2ca620d7e…` |
| [results/run-3.json](results/run-3.json) | `a287e07f312bbe26…` |
| [results/record.jsonl](results/record.jsonl) | `38c44c76eb470537…` |
| [CHANGELOG.md](../../CHANGELOG.md), two entries | - |

    python demo/craft-assembly/report.py write    # this file, then results/checks.md
    python demo/craft-assembly/report.py check    # exit 1 if either would change

Of willow's add-ons: the kernel's `read` checks the record; `xref` checks every reference in this folder, this file's included; `claim-check` looks for each counted claim in the hand-written README. `serve` (pull request 43, not merged) was left out: it hands a model only a scope the person has sealed, with ids drawn at random each run, so it can't be part of a file made the same every time; once this report is sealed as a scope, it is the way to serve it.
