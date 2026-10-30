<!-- willow-addon
section: Ways to use it
line: Ask from Alfred, Raycast, KRunner or PowerToys Run, answers with file and line.
source: new
added: 2026-10-30
writes: nothing
network: none
tags: no-install, offline, read-only, interface
-->
# launcher

Ask your folder from the box you already open with a keystroke.

A launcher runs a command each time you type and shows what it prints. This
prints the passages your folder holds for what you typed, ranked the kernel's way,
each with its file and line.

    python adapters/stdlib/launcher/launcher.py --box DIR [--format alfred|lines] [--limit N] "your question"

For **Alfred** (and **Raycast**, which reads Alfred's workflows) it prints the JSON
a Script Filter reads:

    {"items": [{"uid": "...", "title": "Tomatoes want six hours of sun.",
                "subtitle": "notes/garden.md:3", "arg": "/home/ana/notes/garden.md",
                "quicklookurl": "file:///home/ana/notes/garden.md",
                "text": {"copy": "Tomatoes want six hours of sun. Water them daily.", "largetype": "..."},
                "variables": {"line": "3", "path": "notes/garden.md"}}]}

| Field | Is | So the launcher can |
|---|---|---|
| `title` | the passage's first line, cut at 100 characters | show it |
| `subtitle` | its file and line | say where it is |
| `arg` | the file's full path | open it |
| `quicklookurl` | the same as a file link | preview it |
| `text.copy` | the whole passage | put it on the clipboard |
| `variables.line` | the line number | hand an editor the line |

Set the Script Filter to run the command above with `{query}` as the question.
With no question it shows an item that says to type one, and with none found an
item that says nothing holds it; neither does anything when chosen.

`--format lines` prints one passage to a line, as tab-separated title, subtitle and
path, for a launcher whose plugin runs a command and shows its lines. KRunner's
and PowerToys Run's command plugins can be pointed at it; neither is wired here,
and nothing about them has been tried. `--limit` is how many passages are shown
(10 unless said, from 1 to 50).

A question's words are looked up in the box's words list when it has one, as the
kernel's own bite does. Asking this way writes nothing, not even the row a bite
appends; it reads no key and opens, serves and sends nothing: it prints.

**Exit codes:** 0 printed (even "type a question"); 42 `--format lines` only, when
nothing holds the question; 2 refused (a bad command line, not a box, a words list
that doesn't read).

**Uses:** the kernel's `rank`, `chunks`, `config` and `read_words`.

**Never:** writes anything, even the record; reads the key; opens a file or
starts a server.
