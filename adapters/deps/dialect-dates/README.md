<!-- willow-addon
section: Your own words
line: The words your folder uses far more than the world does, each dated by its first and last appearance, with the passage that first says it.
source: new
added: 2026-11-06
version: 0.1.0
needs: wordfreq; Apache-2.0, its data CC BY-SA 4.0
floor: wordfreq 3.1.0; the 2020 rule names 2.3.2, and every release before 3.1.0 imports pkg_resources, which a Python 3.13 environment doesn't have
uses: dialect, first-mention
writes: nothing
network: none
role: page
-->
# dialect-dates

A folder's own words have a history. The word a household starts using when
a new neighbour moves in, the part a technician starts naming once a model
reaches the shop, the term a committee picks up when a new worry arrives:
each has a first day, and some have a last. This finds the words, as
[dialect](../dialect/) does, and dates each one, as
[first-mention](../../stdlib/first-mention/) does, in one run.

    pip install -r adapters/deps/dialect-dates/requirements.txt
    python adapters/deps/dialect-dates/dialect_dates.py --box DIR [--lang CODE] [--top N]

On a box of the Federal Reserve's FOMC statements and minutes, 2023 to 2026
(the money hour demo's `fed` box), with `--top 8`:

    Your words against wordfreq's en, dated: 16 words, oldest first.
      2023-03-22  2026-04-29  disinflation     41 mentions in 19 files
          minutes/20230322.html.txt:903  Participants commented that recent inflation data indicated ...
      2023-07-26  2025-12-10  restrictiveness  12 mentions in 8 files
          minutes/20230726.html.txt:917  They judged that maintaining the current degree of restrictiveness ...
      2025-12-10  2026-09-16  rmps             26 mentions in 5 files
          minutes/20251210.html.txt:585  In light of this projected decline in reserves as well as recent ...

**How a word is dated** is first-mention's way: a line's own date, else the
nearest date above it in its file, else the date in its file's name. The
first date is the oldest of a word's lines, the last the newest, and the
line shown is the first. A word no line can date is listed last, `undated`,
and counted at the end: your files don't say when, so it could be older
than everything above it.

**Which words** is dialect's choice, unchanged: those wordfreq's counts don't
have, and those your passages use far more than the world does, each held by
three passages or more. `--top N` (30 unless you say) is how many of each
kind are dated. `--lang` is wordfreq's language, `en` unless you say.

**Where it misleads, said so:**

- **One word, not a phrase.** dialect counts single words, so "artificial
  intelligence" is dated as "artificial", and a phrase's first use can be
  later than either of its words'. Ask first-mention the phrase itself.
- **The folder's own furniture counts.** A web page's address line, a
  reader's header, a list of names: on the Fed's minutes, staff names and
  "federalreserve" from each page's address are among its "words". They are
  the folder's, and dated truthfully; they're just not what you asked.
- **Split contractions.** A curly apostrophe splits "wouldn't" into a word
  "wouldn" that the world's counts don't have.
- **A line past its 500th character** is cut by the kernel, so a word said
  late in a long line is dated by a later line, or not at all. Mirror such
  files through a reader that breaks lines first.

It reads the box's passages and prints; it writes nothing, and its verdicts
are only ever the dates your files give. Exit codes, the kernel's: 0 a word
was dated; 42 no word passed dialect's bar, or none could be dated; 2
refused (a bad command line, not a box, a record that doesn't verify,
wordfreq not installed or without that language).
