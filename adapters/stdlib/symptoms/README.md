<!-- willow-addon
section: Keeping track
line: A symptom diary over time, ready to show a doctor: what, when, how bad, each line cited.
source: new
added: 2026-10-27
writes: nothing
network: none
-->
# symptoms

One symptom's diary from your files, oldest first, each line dated, its turn
marked where the line says one, and cited, so a doctor can see the course of
it and check any line against your files.

```
python adapters/stdlib/symptoms/symptoms.py --box DIR "knee"

2026-03-01  worse    Knee bad on the stairs. Voltaren and a hot pack.  Daily/2026-03-01.md:4
2026-03-04  better   Walked the lake loop, 6.2km, knee held up.        Daily/2026-03-04.md:2
2026-03-09  5/10     Physio: knee pain 5/10 after the stairs test.     Health/physio.md:7
3 lines name "knee", 2026-03-01 to 2026-03-09: 1 worse, 1 better, 1 scored
```

**You name the symptom with words**, as a question is asked: "knee", "lower
back", "migraine". A line counts when it itself holds every one of your
content words, each read the kernel's way (your words list, and a word's
plain form, so "knee" finds "knees"). The line has to say it: a folder named
knee holds the word for asking, but writes no diary line. A word with
ordinary uses catches those too — "back" is a direction before it's a spine
— and the diary shows the lines as written, for you to read.

**A turn is marked only where the line says one.** Worse is worse,
worsening, bad, badly, flare and its forms, swollen, agony or worst; better
is better, easing, eased, improved, improving, settled, fine, or held up; a
line saying both is mixed, and a score the line gives as N/10 is shown as
written, a word outranking it. Nothing is averaged, trended or diagnosed:
the course of it is yours and your doctor's to read, and the counts at the
foot only say how often each word was yours.

**Dated as the files say.** A line's date is the latest it says (the
kernel's `newest`), else the nearest date written above it in its own file,
else the date its file is named for, and the diary says which; undated lines
come last. The whole story of a matter, passages and all, written to a file
to hand over, is [timeline](../timeline/)'s job; this is the quick dated
diary of one symptom's own lines.

On willow's demo folders, Bernadette's knee gives 20 lines from 2024-02-08
to 2026-10-06, 8 worse and 10 better, her daily notes' "Knee bad on the
stairs" and "knee held up" carrying the course of it.

It only reads, and the same folder gives the same bytes. Exit codes, the
kernel's: 0 the symptom is named somewhere; 42 never, or only common words;
2 refused.

**Uses:** the kernel's `chunks`, `newest`, `words`, `forms`, `held_by`,
`FUNCTION`, `read_words` and `config`.

**Never:** changes your files; writes anything, even the record; averages,
trends or diagnoses; marks a turn the line doesn't say.
