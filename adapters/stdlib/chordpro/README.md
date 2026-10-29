<!-- willow-addon
section: Reading more kinds of files
line: ChordPro song sheets: titles, lyrics and chords, so you can ask which song had that line.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# chordpro

Your song sheets, searchable by a line of the lyrics.

    python adapters/stdlib/chordpro/chordpro.py mirror --from FOLDER --to MIRROR

Each song is a title line, its chords listed once, and its lyrics with the
chords taken out of the lines, so a question about a lyric finds the song.

    song: Down by the Estuary, by Ada Example (key G, capo 2)
    chords: G, C, D, Em

    Verse:
    Down by the estuary the tide comes in
    Chorus:
    Oh, the water, the water

| Used | Left out |
|---|---|
| title (t), subtitle (st), artist, composer, lyricist, album, year, key and capo | lines that begin with a hash |
| comment (c) lines, kept as lyrics | tab sections |
| verse, chorus and bridge sections, labelled; a custom section by its name or argument | a line of only chords |
| the chords, once each, in the order they first appear | |

A file may hold several songs, split by new_song (ns); each is its own
paragraph. Files are read with the extensions cho, chordpro, chopro, crd and pro.

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
