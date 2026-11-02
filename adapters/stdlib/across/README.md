<!-- willow-addon
section: Ways to use it
line: One page made from several willow records at once (each one's digest, export, timeline or readings), every line still cited by where it came from.
source: new
added: 2026-10-25
writes: nothing
network: none
tags: everyday
looks-for: digest, export, readings, timeline
-->
# across

One document across several boxes, where the document add-ons each make one
from a single box.

    python adapters/stdlib/across/across.py --boxes LIST   DOC [-- ARG ...]
    python adapters/stdlib/across/across.py --box DIR [--box DIR ...] DOC [-- ARG ...]

`DOC` is one of the document-making add-ons, run over every box, its parts
composed under a heading per box:

| DOC | What each box contributes |
|---|---|
| [digest](../digest/) | the one page of what that box needs from you |
| [export](../export/) | that box's approved answers, or its question log |
| [timeline](../timeline/) | one matter traced through that box, dated and cited |
| [readings](../readings/) | a bite of that box, with its numbers-over-time and dates |

Anything after a lone `--` is passed to the add-on unchanged, per box:

    across --boxes boxes.txt digest -- --days 7
    across --box alice --box bob timeline -- "mould landlord"
    across --box alice --box bob readings -- "when is the meeting"

## The list

A `--boxes LIST` file names one box folder a line; a blank line, or one that
begins `#`, is skipped, and a relative path is read from the list's own
folder — the same shape as [repo-pile](../repo-pile/)'s list of repositories.
`--box DIR` names boxes on the command line instead, and repeats. Give one
way or the other, not both.

Every line a box contributes keeps its own citation, so a date or a passage
in the composed document still points at the box, file and line it came from.

## What it does not do

It only reads and composes. The add-ons it runs each promise `writes:
nothing` and `network: none`, and so does across: it writes no box, reads no
key, reaches no network, and approves nothing. The arrow points one way, a
box to a document; a document never changes a box.

Exit codes, the kernel's: 0 nothing across the boxes waits on you; 42 a box
has something the document flagged; 2 refused (a bad command line, a listed
folder that isn't a kernel box, or an unknown `DOC`).
