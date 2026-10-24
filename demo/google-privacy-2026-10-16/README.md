# Google's privacy policy, 16 October 2026: the text against the news

On 16 October 2026 Google changed its privacy policy. The reporting said
Gmail, Drive and Photos content can now be used for personalised ads. The
policy text keeps a default against that, plus an opt-in exception. This
folder asks the documents alone which one the text supports. Willow's kernel
answers, with the [snapshot](../../adapters/stdlib/snapshot/),
[clauses](../../adapters/stdlib/clauses/), [pdf](../../adapters/deps/pdf/),
[scan](../../adapters/stdlib/scan/) and
[quote-check](../../adapters/stdlib/quote-check/) add-ons, from files saved
once and never fetched again.

## The claim

The text supports the default with an opt-in exception, and it does not
support "Google scans Gmail for ads".

- Asked in the reporters' own words, of only the sentences the change
  touched, the kernel served the opt-in exception's clause for 6 of 10
  questions, and BM25 for 9 of 10. Random picks would land 20% of the time.
- Asked of the policy before the change, the same words reach the old
  default, "We don't show you personalized ads based on your content from
  Drive, Gmail, or Photos.", when they reach anything.
- Asked "Google scans Gmail for ads", in eight forms the reporting uses and
  24 blind rewordings, nothing served by either version, or by the changed
  sentences alone, holds a reading word, a mail word and an ad word together.
  The kernel's own answer on the changed sentences is that **no file in the
  folder has "scans"**, and the whole policy, before and after, has no
  "scan" in it at all.

In one line: *the 16 October text keeps "we don't show you personalized ads
based on your content from Drive, Gmail, or Google Photos" and adds
"unless you choose to make data from these services available to other
Google services that support personalized ads"; nothing in either version
says Google scans Gmail for ads.*

## How it could be wrong, and the rule that answers each

| Threat | Rule |
|---|---|
| The questions knew too much | `blind-kernel`, `blind-bm25`: rewordings by an agent that never saw the policy |
| Anything would have hit: the changed set is small | the random baseline in every landing rule; `null-changed`, `null-whole` |
| The old text said the same, so "the change" is nothing | `whole-old`: the old default; the clause diff |
| "Hit" was defined after the fact | the freeze: targets.json and every pass rule committed before any question |
| Absence is just a search that can't find anything | `probe`: the same test finds the policy's own analyze clause |
| The "before" copy is not what Google published | `renderings`: Google's own web page of each version; the Wayback Machine, tried |
| The questions aren't the reporters' words | every one held to quote-check, verbatim, in the saved articles, before the run |

## What is frozen

[FROZEN.json](FROZEN.json) holds the SHA-256 of each frozen file, and
`test_google_privacy.py` fails if one changes. The commit that froze them,
before any question was asked of either version, is the pre-registration.

- [sources.json](sources.json): the eight sources, each with its address,
  the time it was fetched, its type, size and SHA-256, as snapshot wrote
  them: the two versions' PDFs from www.gstatic.com, Google's archive page,
  its page for the 1 October version and the current one, and the three
  reports (tech-insider.org, dexerto.com, shattered.io). The repo keeps
  their hashes, never their text: the pages are Google's and the reporters'.
- [fetch.py](fetch.py): saves them once with snapshot, looks for the
  before copy on the Wayback Machine with
  [wayback](../../adapters/stdlib/wayback/), and checks a pile offline.
- [targets.json](targets.json): the hit rule. The new version's exception
  clause and the old version's default, quoted exactly; the four other
  sentences the change added about letting services share data (`opt-in`,
  reported, never counted); the unchanged analyze clause; and what
  *supports* a claim: one passage holding a word of each group the claim
  needs (a reading word, a mail word, an ad word; or for "on by default", a
  mail word, an ad word and "default"), by the kernel's own `holds`.
- [study.py](study.py): every step, and the twelve pass rules in its
  docstring.
- [questions/](questions/): `reporters.txt`, ten lines of the reporting,
  verbatim; `claims.txt`, "Google scans Gmail for ads" as the reporting
  words it, seven lines verbatim and the plain form; `policy-quotes.txt`,
  the policy as each report quotes it; `blind-reporters.txt` and
  `blind-claims.txt`, three rewordings of each by an agent given only those
  lines (a worried user's question, search keywords, synonyms); `null.txt`,
  thirty questions about the policy with nothing to do with ads, by another
  blind agent. Each file's header says who wrote it from what.

**Said plainly:**

- The author read both versions, their clause diff and all three reports
  before writing the questions, the targets and the rules. The hit rule is
  the change itself, as php2shell's was the fix.
- The `renderings` rule was first written over every sentence the diff
  marks changed. A dry run, with every question replaced by "qqqq zzzz",
  showed it judging the PDF's joined labels, which no web page holds, so it
  was narrowed to the target clauses before the freeze. That dry run showed
  the narrowed rule passing; it asks no question.
- The support groups were written knowing the analyze clause exists; the
  `probe` rule is there to show the test can find support where the policy
  gives it.
- The quotes are reported, not judged: the author had already read
  shattered.io's block quote.
- `wayback.py` was changed after the freeze (an empty window of days now
  asks the archive nothing). The study's run doesn't use it; fetch.py did,
  before the change.

FROZEN.json also records the SHA-256 of the tools at the freeze, and each
verdict row holds the tools it ran with.

## Reproduce

    pip install -r adapters/deps/pdf/requirements.txt
    python demo/google-privacy-2026-10-16/fetch.py --to /tmp/gp/pile            # online, once
    python demo/google-privacy-2026-10-16/fetch.py --to /tmp/gp/pile --check    # offline
    python demo/google-privacy-2026-10-16/study.py --pile /tmp/gp/pile \
        --work /tmp/gp/work --box /tmp/gp/verdicts --out /tmp/gp/answers.jsonl
    python kernel.py verify --box /tmp/gp/verdicts

The study refuses a pile that doesn't match sources.json. A page fetched on
another day may differ (the news pages carry new scripts and links), and
`--check` says which; the PDFs were byte-identical across two fetches 12
minutes apart. By hand, the steps are the add-ons':

    python adapters/deps/pdf/pdf.py mirror --from PILE/policy-new --to TEXT/new
    python adapters/stdlib/clauses/clauses.py mirror --from TEXT/new --to CLAUSES/new
    python adapters/stdlib/clauses/clauses.py diff --old CLAUSES/old/X --new CLAUSES/new/X --to CHANGED
    python adapters/stdlib/scan/scan.py index --from CLAUSES/new --to IX/new
    python adapters/stdlib/scan/scan.py scan --index IX/new --changed-from IX/old \
        --questions demo/google-privacy-2026-10-16/questions/reporters.txt
    python kernel.py init --box BOX --pile CHANGED --key KEY
    python kernel.py bite --box BOX "Google scans Gmail for ads"

## Results, 2026-10-24

Run by [study.py](study.py), as frozen. **Eleven of twelve rules pass.**
The verdicts are rows on a kernel record (`verify`: the chain holds, 13
rows, 0 sealed), each with the SHA-256 of the scored answers (c63e49b2) and
of the tools: `kernel.py` 68dc77b9, `scan.py` d93536eb, `clauses.py`
2eb6c0a5, `pdf.py` 854c80d5, `quote_check.py` f8dd5e55, `study.py` 776e2a07.
A second run, from fresh mirrors and indexes with another hash seed, gave
the same answers byte for byte.

The two versions: 36 pages each, 557 passages before and 564 after. The
clause diff lists 16 entries against 532 unchanged sentences: the effective
date; the ads paragraph's five (three reworded, two added); "Photos" become
"Google Photos"; the new "personalize content" glossary entry's four lines;
and five that are the PDF's labels joined to a sentence. Asked
`--changed-from`, the changed set is 15 passages.

### What the reporters' words land on

| Rule | Asked | Lands | Random | p | Result |
|---|---|---|---|---|---|
| changed-kernel | the changed set, the kernel's rank | 6 of 10 | 20% | 0.0064 | passes |
| changed-bm25 | the changed set, BM25 | 9 of 10 | 20% | 0.000004 | passes |
| whole-new | the whole new version, kernel | 5 of 10 | 0.5% | 10^-9 | passes |
| whole-old | the whole old version, kernel: the old default | 3 of 10 | 0.5% | 0.00002 | **fails**: under 5 |

By question (`exc` the exception clause, `opt` only another opt-in
sentence, `def` the old default, `—` served nothing, `miss` served others):

| Question | changed, kernel | changed, BM25 | whole new | whole old |
|---|---|---|---|---|
| dx-headline | exc | exc | exc | def |
| dx-lede | opt | exc | opt | miss |
| dx-exception | — | opt | — | — |
| ti-lede | — | exc | — | — |
| ti-headline | exc | exc | exc | def |
| ars-headline | exc | exc | miss | miss |
| verge-headline | exc | exc | exc | — |
| 9to5-headline | exc | exc | exc | def |
| sh-lede | exc | exc | exc | — |
| sh-headline | — | exc | — | — |

**Why `whole-old` fails.** The old default is a short sentence (Drive,
Gmail, Photos, personalized ads, content). The kernel serves a passage only
when it holds half a question's rarer words, and for five of the ten
questions no sentence of the old text does, so it served them nothing at
all; the new clause is longer, with "data", "services", "choose" and
"available" among its added words. It is the limit php2shell measured, again: the
kernel matches words, needs half of them in one passage, and a short target
is hard to reach. After the run, not judged: BM25 on the whole old version
lands on the default for 7 of 10.

### Blind questions and null questions

| Rule | Asked | Lands | Random | p | Result |
|---|---|---|---|---|---|
| blind-kernel | 30 rewordings, changed, kernel | 16 of 30 | 20% | 0.00005 | passes |
| blind-bm25 | the same, BM25 | 20 of 30 | 20% | 10^-8 | passes |
| null-changed | 30 null questions, changed, kernel | 0 of 30 | | | passes |
| null-whole | 30 null questions, whole new, kernel | 0 of 30 | | | passes |

By kind of rewording, of 10 each:

| Kind | kernel | BM25 |
|---|---|---|
| v1, a worried user's question | 8 | 10 |
| v2, search keywords | 8 | 10 |
| v3, synonyms ("email", "pictures", "cloud storage", "advertising") | 0 | 0 (all 10 reach another opt-in sentence) |

The policy says "Gmail", "Google Photos", "Drive" and "ads"; asked in other
words, a word-matcher doesn't find it. BM25 still reaches another opt-in
sentence for all ten, never the exception clause. This is the limit
[LIMITS.md](../../LIMITS.md) names.

### "Google scans Gmail for ads": the absence

| Rule | Asked | Result |
|---|---|---|
| no-support | 8 claims and 24 blind rewordings, kernel `bite` on the new version, the old, and the changed sentences alone: 96 answers | passes: no served passage supports a claim |
| names-it | the 8 claims, on the changed sentences alone | passes: the kernel's look names each claim's word as absent, 8 of 8 |
| probe | "We use automated systems that analyze your content for personalized ads", on each version | passes, weakly (below) |

On the changed sentences the kernel said, of each claim:

| Claim | Kernel's look |
|---|---|
| Google scans Gmail for ads | no file in your folder has scans |
| Google scans all Gmail messages to serve ads | no file in your folder has scans, all, messages, serve (exit 42) |
| Is Google reading my Gmail to show me ads? | no file in your folder has reading |
| Google is automatically scanning everyone's private emails and photos to serve ads. | no file in your folder has automatically, scanning, private, serve (exit 42) |
| Google reads inbox contents to pick ads. | no file in your folder has reads, inbox, pick |
| Google reads inboxes for ads | no file in your folder has reads, inboxes |
| Gmail ad use is on by default | no file in your folder has ad, default |
| Does Google now use my Gmail to target ads by default? | no file in your folder has now, target, default (exit 42) |

Of the whole policy, before and after alike, the kernel says no file has
"scans", "scanning" or "default". What it does serve for a claim, on the new
version, is most often the exception clause itself (10 of 32), and a
sentence about abuse ("sending spam to Gmail users, stealing money from
advertisers by fraudulently clicking on ads", 8 of 32): the denial, and a
sentence that names Gmail and ads for another reason. 14 of 32 got nothing.

**What the absence does not cover, said plainly.** Both versions, unchanged,
say: "We use automated systems that analyze your content to provide you
with things like tailored search results, personalized ads, or other
features tailored to how you use our services." Elsewhere, both say your
content "includes things like email you write and receive". Read together,
a reader can make "automated systems analyze your email for personalized
ads" out of the policy, and could before 16 October too: the sentence is
not in the changed set. The support rule doesn't join two sentences, and no
claim the reporting makes is in those words. The `probe` shows the kernel
reaches the sentence, but weakly: the probe copies the sentence's opening,
so the kernel marks it an *echo* and exits 42 on both versions. And the
kernel reads "ad" and "ads" as different words (its plain-form rule needs
four letters), which is why "ad" shows as absent above.

### The renderings, and the before copy

| Rule | Result |
|---|---|
| renderings | passes: the default is in Google's page for the 1 October version and not the current one; the exception and the four opt-in sentences are in the current page and not the 1 October one; the analyze clause is in both |

Reported: of the clause diff's changed sentences, 6 of 9 old ones and 14 of
15 new ones are in their own version's web page with the same words; the
rest are the PDF's labels joined to a sentence.

**The Wayback Machine could not be reached.** Asked for captures of the
before PDF between 1 and 16 October, web.archive.org closed the connection
every time ("connection reset by peer", three tries and the fetch's own),
and archive.org's API answered 429, too many requests. The before copy is
checked against Google's own second rendering, not an independent archive.
That check stands for anyone to run where the archive answers:

    python adapters/stdlib/wayback/wayback.py find --to /tmp/gp/wayback \
        --url https://www.gstatic.com/policies/privacy/pdf/20261001/f86f5p0s/google_privacy_policy_en.pdf \
        --after 20261001 --before 20261016 --against /tmp/gp/pile/policy-old/google_privacy_policy_en.pdf

### The reporters' quotes of the policy (reported, not judged)

| Report | Quote | Before | After |
|---|---|---|---|
| tech-insider.org | "Drive, Gmail, or Google Photos" | not there | verbatim, line 203 |
| dexerto.com | "unless you choose to make data from these services available to other Google services that support personalized ads." | not there | verbatim, line 203 |
| shattered.io | "We don't show you personalized ads based on your content from Drive, Gmail, or Photos, unless you choose to …" | not there | **not there** |

shattered.io's block quote is in neither version: it joins the old
sentence's "or Photos" to the new sentence's exception. The new text says
"or Google Photos". The meaning survives; the words don't.

## What it found, together

- **The text supports the default and the exception.** The reporters' own
  words, asked of only what changed, land on the exception clause far above
  chance (6 of 10 by the kernel, 9 of 10 by BM25, against 2 in 10), blind
  rewordings do too, and null questions never do.
- **"Can now be used" is the exception, not a new default.** The old
  default sentence is still there, word for word, with "unless you choose
  to …" added; the opt-in sentences around it say what choosing means.
- **Nothing says Google scans Gmail for ads,** before or after: no "scan"
  anywhere in the policy, and no served passage with reading, mail and ads
  together. The nearest thing is an older, unchanged sentence about
  automated systems analyzing "your content" for personalized ads.
- **The reporting itself is mostly careful;** its headlines are broader
  than its bodies, and one quote of the policy is misquoted.
- **What failed:** the kernel's rank on the old version (3 of 10, `whole-old`)
  and on synonyms (0 of 10); the Wayback check, which never got an answer;
  and the probe, which passed only as an echo. BM25 again does better than
  the kernel's own rank, as in php2shell.
