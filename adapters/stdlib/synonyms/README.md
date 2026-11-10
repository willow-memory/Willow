<!-- willow-addon
section: Your own words
line: Words-list lines for a word no file holds: the dictionary's other words that your files do hold.
source: new
added: 2026-11-09
version: 0.1.0
writes: nothing
network: loopback
role: words
-->
# synonyms

You ask in your words; your files answer in theirs. For a word of your
question that no file holds, this finds the dictionary's other words for it
and keeps the ones your files do hold, as lines for your words list.

    python adapters/stdlib/synonyms/synonyms.py --box DIR --data DICT [--embed MODEL [--url URL]]
        ("your question" | --questions FILE)

    postponed = table, defer
    gaps = crack
    # snooze: no file holds it, nor any of the dictionary's 3 other words for it

**The dictionary is WordNet**, Princeton's database of which English words
share a meaning. DICT is a folder holding its own eight files: an index and
a data file for each of noun, verb, adj and adv. You get them once, yourself:
from [Princeton](https://wordnet.princeton.edu/download/current-version)
(the "database files only" download, about 10 MB), or from your system's
packages (Debian and Ubuntu's wordnet-base puts them in its own folder under
the shared data folder). WordNet's licence lets anyone use and pass on the
database with its notice kept, and each file opens with that notice. This
add-on reads the files with a few lines of its own: nothing is installed,
and it never downloads them for you.

**How a word is read.** Each word of your question that no file holds (and
that your words list doesn't already read) is looked up as written, then
with a plural, tense or comparing ending taken off, by WordNet's own rules:
"gaps" is "gap", "postponed" is "postpone". Every other single word that
shares a meaning with it is a candidate, the most used meaning's first.
Phrases are left out, since a words list reads one word as others. A
candidate is kept only when your files hold it, the way the kernel holds a
word. The line lists them, the one in the most passages first.

**Read each line before you keep it.** A dictionary doesn't know which sense
you meant. "postponed" brings "table" (to table a motion) beside "defer",
and your files may hold "table" for quite another reason. A line here is a
suggestion to read, never a fact about your files.

**`--embed MODEL` puts the nearest word first.** An embedder is a small
model that turns a word into numbers, so that words close in meaning are
close in number; Ollama's nomic-embed-text is one. With `--embed`, each
line's words are ordered by how near each is to your word, by that model,
and a note says so. With it, the line above reads `postponed = defer,
table`. It orders and drops nothing: "shelve" is a true synonym of
"postponed" that an embedder may still put last. URL is Ollama's
http://127.0.0.1:11434/v1 unless you give another (any server on this
machine that answers the OpenAI embeddings call), and one off this machine
is refused before a word is sent. Only the words themselves go to it: yours,
and the dictionary's candidates. Never a passage, a path or a question.

**Everything printed is a words list.** A word that gets no line gets a
note, after a `#`, saying why: your files hold none of the dictionary's
words for it, or the dictionary has none. So the output can be read, cut
down, and kept as it is. Nothing is written; add the lines you want to your
own words list, the one named at `init`, or give them to
[scan](../scan/) with its `--words`.

**`--questions FILE`** reads every question in FILE (one a line, or a name,
a tab and the question, as scan takes them) and looks each word up once.

**What it can't do.** It helps only with a word no file holds. A question
whose words are all in your files, but never together in one passage, gets
nothing here: that is a job for search by meaning
([latent](../../deps/latent/)). And WordNet knows general English, not your
project's own names for things.

On the pile this was built for, 266 files of one person's old screens and
plans, ten real questions held no word the files lacked, and it said so.
Asked "which widgets get postponed, shelved or snoozed until the overhaul",
it gave `postponed = table, shelve, defer` and `overhaul = pass, service,
modernize`, and with nomic-embed-text, `postponed = defer, table, shelve`
and `overhaul = modernize, service, pass`.

Exit codes, the kernel's: 0 every word no file holds got a line, or your
files hold every word; 42 a word got none, or the embedder couldn't be
asked (and then nothing is printed); 2 refused: a bad command line, a
folder that isn't a box or a record that doesn't verify, a folder that
isn't WordNet's database (it names the files missing), a words list
readable beyond its owner, or an embedder off this machine.

**Uses:** the kernel's `chunks`, `words`, `holds`, `held_by`, `config`,
`read_words` and `read`.

**Never:** writes anything, the record included; sends a passage, a path or
a question anywhere; or asks a model off this machine.
