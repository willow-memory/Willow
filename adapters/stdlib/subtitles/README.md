<!-- willow-addon
section: Reading more kinds of files
line: Subtitle and transcript files (.vtt, .srt) as lines cited by timestamp, for podcasts and videos already transcribed.
source: new
added: 2026-10-27
writes: to
network: none
-->
# subtitles

The podcasts and talks you already have transcripts of, as plain text the
kernel reads: each cue one line, its start time first, so what was said can
be asked about and the answer carries the moment to scrub to.

```
python adapters/stdlib/subtitles/subtitles.py mirror --from FOLDER --to MIRROR

00:00:01  The tide keeps its own calendar.
00:00:04  Ada: And the harbour keeps the tide's.
```

**What is read.** .srt files, and .vtt files, which open with WEBVTT. A
cue's lines are joined with a space; styling tags are taken off, and a
WebVTT voice tag becomes the speaker's name with a colon. Times are written
HH:MM:SS, hours added where a cue leaves them off, the fractions dropped: a
second is as close as a person scrubs. Cue numbers, NOTE and STYLE blocks
say nothing and are left out.

**What is not guessed at.** A .vtt without its WEBVTT first line, and a
.srt with no readable cue, are skipped and counted: a file that isn't what
its name says is someone else's. Hidden files and folders are never read.

Each file is written to MIRROR at the same relative path with .txt added:
a talk at talks/ep1.srt becomes `MIRROR/<same path>.txt`. FOLDER is only read:
originals are never modified and nothing is written inside it. It keeps
[the readers' contract](../ci/test_contract.py): the same folder gives the
same bytes, and `wrote N files to MIRROR; skipped M` says what happened.
Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused
(FOLDER is not a folder, or MIRROR and FOLDER are inside one another).

Point the kernel at MIRROR (`kernel.py init --pile MIRROR ...`) to ask
questions of what was said; [said](../said/) then reads a voice-tagged line
as its speaker's quote.

**Uses:** the kernel's exit codes; the mirror is for `chunks` to read.

**Never:** changes your files; writes outside MIRROR; reads a hidden file;
guesses at a file that isn't what its name says.
