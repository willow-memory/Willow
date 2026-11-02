<!-- willow-addon
section: Your own words
line: The words you use far more than the world does: your own dialect, from your files against wordfreq's counts.
source: new
added: 2026-10-29
needs: wordfreq; Apache-2.0, its data CC BY-SA 4.0
floor: wordfreq 3.1.0; the 2020 rule names 2.3.2, and every release before 3.1.0 imports pkg_resources, which a Python 3.13 environment doesn't have
writes: nothing
network: none
-->
# dialect

Every household, trade and family has words the rest of the world hardly
uses: a street, a nickname, a part of a piano. Those are the words a
newcomer's question won't have and your files will. This finds them, by
setting your files' words against wordfreq's counts of how often the world
writes each one.

    pip install -r adapters/deps/dialect/requirements.txt
    python adapters/deps/dialect/dialect.py --box DIR [--lang CODE] [--top N]

On Odile's demo folder (she tunes pianos):

    Your words against wordfreq's en, from 909 passages.

    Words the world's counts don't have:
      petrak     in 55 passages
      keybed     in 35 passages
      trapwork   in 27 passages
      acrosonic  in 24 passages

    Words you use far more than the world does (Zipf, you and it):
      dcsd    6.2 to 1.1, +5.1  in 58 passages
      samick  5.7 to 1.1, +4.6  in 32 passages
      odile   6.9 to 2.5, +4.4  in 166 passages

**How a word is counted.** Letters only, three or more, not a function word;
once a passage, a passage said many times over counting once; held by three
passages or more, so one letter's quirk isn't a dialect. A word only ever
written in capitals (an ICS file's DTSTART, a bank's EFTPOS) is a file's
code, not a person's word, and is left out. Both numbers are on wordfreq's
Zipf scale, a word's frequency per billion words as a power of ten: "the"
is about 7.7, a word in a million 3. The first list is by passages, the
second by how far beyond the world you use the word, ties by word; the top
30 of each unless `--top` says. `--lang` takes any of wordfreq's 40-odd
languages (de, fr, ro, ...), en unless you say.

**On the four demo folders** it finds Bernadette's Ballarat (Wendouree,
Kilmurry, Corio, Siobhán, Weetbix), Teodora's Romanian kitchen (bunica,
sarmale, brânză) and Hollis's spinet and fallboard. It also finds what
email and bank exports repeat: `charset`, `noreply`, a bank's product
names. Those are your files' words too, if not yours; read the list, keep
what's yours.

**It never changes anything.** The lists are printed for you to read; a
word you keep goes in your words list by your hand.

**Without wordfreq** it refuses and names the install: exit 2, never a quiet
skip.

**Uses:** `chunks`, `words`, `FUNCTION`, `read`, `config`, and the kernel's
exit codes: 0 words listed; 42 none held by enough passages; 2 refused.

**Never:** writes anything, not even the record, or goes online: wordfreq's
counts come inside the package.
