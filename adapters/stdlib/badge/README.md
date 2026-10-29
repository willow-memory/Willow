<!-- willow-addon
section: Ways to use it
line: A badge for a page: these answers came from these files and were approved, linked to the check anyone can run.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, interface
-->
# badge

A small badge for a page: these answers were approved.

A page that quotes your answers can say so at a glance. This writes an SVG
badge, in the flat style README badges use, from what the record holds.

    python adapters/stdlib/badge/badge.py --box DIR --to FILE [--link URL]
    wrote FILE: 3 answers from 2 files
    markdown: [![willow: 3 answers from 2 files](https://example.org/badge.svg)](https://example.org/check)

| Badge | Colour | Means |
|---|---|---|
| 3 answers from 2 files | green | the chain holds and every approval stands |
| no approved answers | grey | nothing is approved yet |
| 3 answers from 2 files, 1 not standing | amber | an approval whose proof fails, or whose proposal file changed |
| record broken | red | the chain does not hold |

An answer counts when its approval proves under your key (the kernel's
`sealed`, so the key is read there and nowhere here) and its proposal file is
still the bytes you approved. A file counts when an answer cites a passage in
it. Nothing about the answers is in the badge but the counts.

The badge carries what a reader needs to check it, in its own title and
description: the record's length, the start of its tip hash, and the one
command anyone holding the box can run, `kernel.py verify --box BOX`. With
`--link URL`, where you explain or host that check, it also prints the Markdown
to paste on a page, with the badge's file name as its image address (change it
to where you publish the badge).

A badge is a claim shown to people who can't run anything: it is only as good as
the check behind it, and its description says so. It isn't signed. FILE is
written once, readable only by you, never over a file that exists, and the same
record gives the same bytes. Nothing is sent anywhere.

Exit codes, the kernel's: 0 written, green or grey; 42 written, but red or
amber, which waits on you; 2 refused (a bad command line).

**Uses:** the kernel's `read`, `sealed` and `standing`.

**Never:** reads the key, changes the box, or writes anywhere but FILE.
