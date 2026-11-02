<!-- willow-addon
section: Reading more kinds of files
line: Link files dragged to a desktop or folder (.url, .webloc, .desktop) as their title and the address they hold.
source: new
added: 2026-11-02
writes: to
network: none
-->
# shortcuts

The links you dragged out of a browser onto your desktop or into a folder,
findable by what you called them.

    python adapters/stdlib/shortcuts/shortcuts.py mirror --from FOLDER --to MIRROR

Each link file becomes one passage: the title its file name gives, and the
address inside it. "Allotment rules.url" gives:

    Allotment rules
    https://example.org/allotment/rules

| File | Made by | What is read |
|---|---|---|
| `.url` | Windows (an Internet Shortcut) | `URL=` in its `[InternetShortcut]` section |
| `.webloc` | macOS | the `URL` key of its property list, XML or binary |
| `.desktop`, `Type=Link` | Linux desktops | `Name`, `Comment` and `URL` |
| `.desktop`, `Type=Application` | Linux desktops | a launcher's `Name`, `GenericName`, `Comment`, `Keywords` and the command it runs (`Exec`) |

Launchers are read too, since "where's the launcher for the text editor" is
a fair question of a folder of them. Each value is written as the file holds
it, one to a line, with no label of this reader's own: a word added to every
passage would let a question about something the folder doesn't hold land on
any of them. The cost: "show me my links" finds nothing, since no passage says
"link". A desktop entry of another type (a menu folder), or one marked
`Hidden=true` (deleted, by the desktop entry spec), is skipped and counted. A `.desktop` file's own `Name` is its title, not a
translation (`Name[fr]`), and its escapes (`\s`, `\n`) are read.

A `.url` file is read as UTF-8, and as Windows-1252 when it isn't: the
address itself is plain ASCII, but Windows writes other keys, such as the
path of an icon in a folder with an accented name, in the computer's own code
page. A `[DEFAULT]` section, which Windows writes for a page's base address,
lends the shortcut nothing. A `.desktop` file is UTF-8, as its spec says.

**Not read:** a Windows `.lnk` is a binary shell link, usually to a program
or a file on that computer rather than a web page. It is neither written nor
counted. Nor is an old Mac `.webloc` that keeps its address only in a
resource fork: copied off the Mac, it is empty, and is skipped and counted.
Browser bookmarks are another add-on's job.

Only what's in the file and its name is written, never its modified time,
so the same folder gives the same bytes on any copy. Each file is written to
MIRROR at the same relative path with .txt added (`MIRROR/<same path>.txt`).
FOLDER is only read: hidden folders and files are skipped, and nothing is
written inside it. A file with no address, or that can't be read, is skipped
and counted, never a crash:

    wrote 2 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

No real .url or .webloc was at hand to build this from: its tests and its
trial run use files made to each format as its makers write it (a binary and
an XML webloc written by plistlib, a .url as Windows 10 writes one, with its
property-store section). Its launchers were tried on a real Linux machine's
own desktop entries.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`); Python's
standard library for the formats (configparser, plistlib).

**Never:** writes inside FOLDER, modifies an original, follows a link it
reads, writes anything outside MIRROR, or goes online.
