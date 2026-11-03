# Report 5: one matter through the commits, and the session sealed, 2026-11-03

`timeline` over the commit-and-comments mirror (hist-box, 1,431 commits of
the five repos plus their comments), four matters asked, each written to
its own file, oldest line first, every line cited. Then `session-seal`
over the proof box: everything asked and handed in there, bundled as one
suggestion for a person to seal.

## Four matters, two lessons

| matter | lines | undated | what it is |
|---|---|---|---|
| vault anchor receipt | 371 | 1 | the RFC 13 story, from one redential-cli commit |
| schema version | 18,029 | 591 | every diff that says schema or version |
| words list | 92,387 | 3,061 | every diff that says words or list |
| privacy test | 111,319 | 6,255 | every diff that says test |

The kernel's rule, half the matter's words in a passage, makes "privacy
test" mean "test", and a commit mirror is mostly tests. A timeline wants a
matter rare enough to be one story, and the three-word one was. Each run
took about seventeen seconds whatever it found.

## The vault's story, as its own fixture tells it

All 371 lines come from the commit that landed the backdated-segment
fixture (#39) and the one that drafted the anchor schema (#38). The
timeline reads the fixture's narrative as a dated story: an honest
operator anchors on 2026-03-15 (week-1 head, 4 receipts, `activity_period
2026-Q1`), claims `finished_at` spread across 04-01 to 06-10, splices the
gap into the chain, submits with `max_finished_at_claimed 2026-06-10`,
and the expected verifier outcome follows. The fixture's placeholder
hashes (`2222…`, `anchor-hash-seq-0-…`) sit in the timeline as written.
The dates are the story's, not the commit's: the kernel dates a line by
the nearest date above it, which in a diff is whatever the diff says, as
report HISTORY noted. Here that is the right reading, since the matter is
the story.

## session-seal beside RFC 13

session-seal bundled the proof box's rows 0 to 22 (9 bites served, 9
proposals passed, 2 fixity, 2 out, 1 boot) and proposed the bundle as the
answer to `session 0 to 22`, citing nothing, waiting on a seal at row 25.
`check`: 1 session, 0 sealed, 1 waiting, 0 broken. Set beside the anchor
record RFC 13 drafts:

| RFC 13 anchor field | session-seal has |
|---|---|
| `head_hash`, SHA-256 of the local vault head | the kernel's tip, the hash of the row before |
| `receipt_count_total`, `receipt_count_since_prev` | rows 0 to 22, and "0 rows since, not yet bundled" |
| `activity_period`, a coarse bucket, no gap exposure | counts by kind and no words, by the record's rule |
| `prev_anchor_hash` | the previous bundle's seal, on the same chain |
| `received_at_server`, the server's clock | nothing: it is local only |
| a splice forks `chain_id` | tip-pin refuses the record instead |

The client half of the RFC exists in Willow already, as a box plus two
add-ons, with the person's seal where the RFC puts a submit. What Willow
has no equivalent of is the server half, the authoritative clock. What
RFC 13 has no equivalent of is the seal: its anchors ride a submit, and
nothing in the draft is a person saying yes to a segment.

## Files

`timeline/*.md` (the four timelines), `proof-box/` (the session bundle
waiting at row 25).
