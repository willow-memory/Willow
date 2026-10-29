<!-- willow-addon
section: Ways to use it
line: New approved answers as an RSS feed file, for any feed reader.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, interface
-->
# rss-out

What you approve, in your feed reader.

RSS is what feed readers subscribe to. This writes each answer you approved as
an item of an RSS 2.0 feed, newest first, so a reader shows you new answers as
they are approved.

    python adapters/stdlib/rss-out/rss_out.py --box DIR --to FILE [--link URL] [--title TEXT] [--since DATE]
    wrote FILE: 3 items

| Feed field | Is |
|---|---|
| item title | the answer's first line, 80 characters at most |
| item description | the answer, then "Why:" with the reason it was given, then "From:" with the places it cites |
| item date | when you approved it, as RFC 822 in UTC |
| item id (guid) | the suggestion's subject, not a link, so a reader shows an answer once |
| channel link | `--link`, or http://localhost/ |
| channel title | `--title`, or "Willow: approved answers" |
| last build date | the newest approval |

`--since DATE` (year-month-day) keeps only answers approved on or after that
day, for a feed of what is new. An approval is exported only while its proof
holds under your key (the kernel's `sealed`, so the key is read there and
nowhere here) and its proposal file still holds the bytes you approved; one
that doesn't is left out and said on standard error. The record keeps no
question's words, and the feed has none.

FILE is written once, readable only by you, never over a file that exists, and
the same record gives the same bytes. Nothing is served or sent: put FILE where
your reader can fetch it.

Exit codes, the kernel's: 0 written; 42 written, but an approval was left out
and waits on you; 2 refused (a record that doesn't verify, a bad command line).

**Uses:** the kernel's `read`, `sealed` and `standing`.

**Never:** reads the key, serves or sends anything, changes the box, or writes anywhere but FILE.
