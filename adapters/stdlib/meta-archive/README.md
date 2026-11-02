<!-- willow-addon
section: Reading more kinds of files
line: Facebook and Instagram's Download Your Information files: posts, comments and messages as dated lines.
source: new
added: 2026-10-29
writes: to
network: none
-->
# meta-archive

Your Facebook and Instagram messages, posts and comments, searchable by day.

    python adapters/stdlib/meta-archive/meta_archive.py mirror --from FOLDER --to MIRROR

The three kinds of JSON file that are your words are written, oldest first, as
dated lines:

    2024-03-02 08:15  Garden chat (Ana, Ben)  Ana: Six hours of sun.
    2024-03-02 09:00  post: Planted out the tomatoes.
    2024-03-03 19:40  comment: The slugs are winning.

Messages (message_1.json, with `participants` and `messages`) carry the
conversation's title, or its participants, and who sent each message. Posts
(your_posts_1.json) and comments are written as "post" and "comment". The
export writes its text as UTF-8 read as Latin-1, so an accented letter arrives
garbled; that is undone where it can be. Times are UTC. Photos, videos,
reactions and the other fields are not copied; other JSON is skipped and
counted.

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
