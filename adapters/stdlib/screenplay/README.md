<!-- willow-addon
section: Reading more kinds of files
line: Fountain and Final Draft scripts: scenes, characters and lines, cited by scene.
source: new
added: 2026-10-29
writes: to
network: none
-->
# screenplay

Your scripts, searchable by scene, character and line.

    python adapters/stdlib/screenplay/screenplay.py mirror --from FOLDER --to MIRROR

Each script is written as its scenes:

    title: Garden Party
    author: Ana Example

    scene 1: INT. KITCHEN - DAY
    Ana waters the tomatoes.
    ANA: Six hours of sun.

A scene is a heading (INT., EXT., EST., INT./EXT., I/E, or one forced with a
leading dot) numbered from one, or as the script numbers it. Action is kept as
written, and a cue with its dialogue is joined as "NAME: line" with the
extension, (V.O.) say, kept. Parentheticals, transitions, page breaks, notes,
boneyard comments, synopses and the transition arrows are left out; sections
become "section: X". A Final Draft (.fdx) file is read by its paragraph types.
A file that declares entities is not read.

Each file is written to MIRROR at the same relative path with .txt added.
FOLDER is only read: hidden folders and files are skipped, and nothing is
written inside it. A file that can't be read is skipped and counted, never a
crash:

    wrote 2 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`); Python's
standard library for the format.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, or goes online.
