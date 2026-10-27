<!-- willow-addon
section: Finding things
line: Your own quotes, gathered: every 'so-and-so, on this date: "..."' in your files, as a dated timeline of what was decided.
source: new
added: 2026-10-27
writes: nothing
network: none
tags: no-install, offline, read-only, search
-->
# said

Every line of your folder that quotes someone, as a dated timeline of who
said what, oldest first: what was decided in the chat, what the plumber
promised, what you told your sister you'd bring.

    python adapters/stdlib/said/said.py --box DIR [WHO]

    2023-04-17  Mags  Terry says Gerry owes him $10 from the footy  chats/mags.txt:3
    2024-02-28  Teo   first £100 back, thank you again x            chats/teo.txt:12
    undated     Sam   we'll cover the parts ourselves               minutes.md:4
    3 quotes by 3 speakers, 1 undated

**A quote is read by shape**, and three shapes are read: a chat's line (a
timestamp, then a name and a colon, as chats are written and as the chats
reader mirrors them); a speech verb at the line's start (a name, then said,
says, wrote, writes, asked, asks, replied, replies, texted or texts); and a
quotation (a name, a colon, and the words in quotation marks). A bare
`Name:` with none of those marks is not read: a mail's `Subject:` and a
note's `TODO:` wear the same shape, and a quote needs its marks. A name is
one to three capitalized words (Siobhán and O'Brien among them), so `RE:`
and `TODO:` never pass for one. What's quoted is as written, never
shortened but for the row's width, and reported speech ("Terry says Gerry
owes him") stays inside its speaker's quote: who told you is who's quoted.

**Dated as the files say.** A line's date is the latest it says, read as
the kernel reads one (its `newest`; a chat's `02/02/2022`, reading either
way round, is never guessed); a line that says none takes the nearest date
written above it in its file, else the date its file is named for, and the
timeline says which. Undated quotes come last: your files don't say when.

**WHO narrows it to one speaker**: every quote whose speaker's words hold
each of WHO's, so "mags" finds Mags Doyle, and "mags doyle" doesn't find
Mags Riley.

On willow's demo folders, Bernadette's folder gives 203 quotes by 6
speakers, her WhatsApp mornings in order (`said.py --box DIR mags` keeps
Mags's 41), and Teodora's gives 735; a chat line whose own stamp reads both
ways round takes its date from the stamped line above it, and says so.

It only reads, and the same folder gives the same bytes. Exit codes, the
kernel's: 0 quotes found; 42 none, or none by WHO; 2 refused.

**Uses:** the kernel's `chunks`, `newest`, `words` and `config`.

**Never:** changes your files; writes anything, even the record; reads a
field label as a speaker; shortens what was said beyond the row's width.
