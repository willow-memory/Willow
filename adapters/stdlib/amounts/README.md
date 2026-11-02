<!-- willow-addon
section: Finding things
line: Every sum of money in your files, with its date and the line it's on.
source: new
added: 2026-10-27
writes: nothing
network: none
-->
# amounts

Every sum of money your folder writes, each with its date and the line it's
on, oldest first: invoices, receipts, a debt in a chat, the rent in a letter.

    python adapters/stdlib/amounts/amounts.py --box DIR

    2026-03-14  £54.85    car/mot.txt:3      MOT test £54.85
    2026-05-02  €725      letters/may.md:1   my half €725 (paid May 2024)
    undated     $20       notes.md:9         Found $20 in a coat pocket.
    255 sums: 254 dated, 1 undated

**What counts as a sum.** A number written with its currency: a symbol
before it (`$20`, `£1,840.00`, `€ 45`, `US$9.50`), a currency code before it
(`EUR 100`), or a code or `lei` after it (`45.50 USD`, `200 lei`). The
number may group thousands with commas and give pence after a dot. A number
written any other way names no sum here, rather than a guessed one: `100,00`
and `1.995` read two ways, and a bare `450` is never money. A sum is shown
as your file writes it, never converted or added up: what `$20` was worth,
and whether it was paid or only mentioned, is the line's to say.

**How a sum is dated.** By its line: the latest date the line says, read as
the kernel reads one (its `newest`; `11/03/2026`, either way round, is never
guessed). A line that says none takes the nearest date written above it in
its own file, and says which line (`date from line 4`); one with neither
takes the date its file is named for, and says so (`date from file name`).
A sum no date reaches comes last, marked `undated`: your files don't say
when, and the listing says that.

On willow's demo folders it finds Odile's 255 sums (every invoice line, all
dated), Hollis's 139, Teodora's 136 (her `200 lei` among them; her tax
summary's sums are undated, and say so), and Bernadette's 77.

It only reads, and the same folder gives the same bytes. Exit codes, the
kernel's: 0 sums found; 42 none in your folder; 2 refused.

**Uses:** the kernel's `chunks`, `newest` and `config`.

**Never:** changes your files; writes anything, even the record; converts a
sum or totals them.
