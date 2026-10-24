<!-- willow-addon
section: Trust and proof
line: Every reference in your files checked: each link to another file, and each quoted line, still there and still saying it.
source: bot
added: 2026-10-24
writes: nothing
network: none
tags: no-install, offline, read-only, trust, everyday
-->
# xref

Every reference in your files to another of your files, checked.

    python adapters/stdlib/xref/xref.py --box DIR
    python adapters/stdlib/xref/xref.py --from ANY-FOLDER

    notes/index.md:2      link       ../trips/2019.md: not there
    letters/reply.txt:1   file:line  care/log.txt:40: past the end (31 lines)

    7 references checked, 2 don't hold; 1 leading out of your folder, not checked.

| Reference | Checked |
|---|---|
| a Markdown link to another file, or a web page's `href` or `src` | the file is there, followed from the folder the link is written in |
| a place written out, `care/log.txt:12`, as willow's answers cite them | the file is there, from its own folder and then from the top of yours, and has that line |

These aren't checked:
- A link to the web, an e-mail address, or a place in the same page isn't a file of yours.
- A link that leads out of your folder is counted, never followed.
- A `file:line` that names no file in your folder may name one somewhere else entirely.

**Where it comes from:** willow-bot's xref (its link and `file:line`
patterns), for one person's folder rather than a set of repositories. It
leaves out the bot's repo ids, commits and git blob checks.

Exit codes, the kernel's: 0 every reference holds; 42 one doesn't; 2 refused.

**Never:** follows a link out of your folder, or writes anything.
