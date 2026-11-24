<!-- willow-addon
section: Play
line: One way to sit at any game on the record: whose seat it is, the moves it may make, one move; so a GM, a bot or a person plays them all.
source: new
added: 2026-11-21
version: 0.1.0
looks-for: contradictions, session-seal, stack, forge
writes: record, to, beside
network: none
role: tools
-->
# table

One way to sit at any table on the record: a game night, a call with a
landlord, a meeting. Whose seat it is, the moves it may make, one move at a
time.

    python adapters/stdlib/table/table.py --box DIR [--words FILE]
    python adapters/stdlib/table/table.py --home FOLDER
    python adapters/stdlib/table/table.py --box DIR bring --as NAME [--at MATTER] "what they bring in"
    python adapters/stdlib/table/table.py --box DIR stands [--at MATTER] [--json]
    python adapters/stdlib/table/table.py moves [--seat host|guest]

## The front door

Nobody should have to remember a path to sit at their own table. With
`--home FOLDER` it opens on a list:

    Hello. You have 2 tables.

      1. Landlord
         You've settled 1 thing here.
      2. Work
         Nothing settled yet. Claude left 17 things for you to look at.

    1 more folder has a stack but no box yet: garden.

    Which one would you like? Type its number, or ask them all something. Enter on its own leaves.

**It speaks in sentences.** A table is for a person who has never seen it:
it asks one plain thing at a time, says who left what, and keeps its list
of keys out of the way until `?` is typed. A person can type a word (look,
list, undo, pause, who) where they would guess one; the single letters work
too. Every answer says what it does: y keeps it, n drops it, s skips it for
now. This came from the first real sitting, which read like a control
panel and felt like one.

A table is any folder under FOLDER whose box has been sat at or brought a
word, or that has had a table laid for it: its words, a prep sheet or an end
sheet put beside the box. The host picks one by its number and sits. When
that sitting ends, is paused or is left, they are back at the list, read
again; Enter leaves.

- **A table's own words** are read from a file named for them beside its
  box (`table-words.txt`), when there is one, and its title is the name it
  goes by in the list. Without one it goes by its folder's name.
- **A box nobody has brought a word to, and no table was laid for, is no
  table yet**, and isn't opened to find out.
- **A folder that itself holds one box is a front door of one.** Give
  `--home` that folder and its box is the list's only table.
- **A folder with a stack and no box** is named under the list, in one line.
  It can't be asked yet: there is no box there to ask.
- **Looking writes nothing.** The list reads each table's record and no more.

**Asking every table at once.** A line typed at the list that is not a
number is a question, and it is asked at every table in turn:

    Asking 2 tables, one at a time. A choice you make is asked once and used at each.

Each table answers it as it would at its own prompt, with its own yes (see
"The first bite", below). A fork is put once, and the pick is used at the
next table; each table takes its own yes before anything is written there.
When it went to more than one table, what each want found is gathered into
one list, every line ending with its table and where it is from:

    Everything that found, from every table:
      Want 1: “things marked todo”: todo (you named it).
           2026-11-02  TODO: ask for the deposit terms in writing.  (Landlord, notes.md:2)
           2026-11-02  TODO: ask for the deposit terms in writing.  (Work, notes.md:2)

At most five lines from each table are shown, then "and N more at TABLE, in
its page." One table asked gathers nothing: it reads as it does at its own
prompt. A single character that is not a number is only told to be one of
the table numbers.

## Two seats

| Seat | Who | The moves it may make |
|---|---|---|
| host | the person whose box it is, at a terminal | ask their files a question; say what is settled; answer what someone brought in; take a yes back; set a call aside; pause; end the sitting |
| guest | anyone else: a player, a clerk on the phone, a script, a model | bring something in, under a name |

**Nothing is true at the table until the host says so.** What the host
keeps with `say` (or `keep`) and says yes to is handed to the kernel as a
suggestion and sealed on that typed yes, by the kernel's own `seal`, with
the key the kernel was given when the box was made. A typed no is the
kernel's `decline`. A plain typed line is not that: it is a question (see
"The first bite"). No option answers for the host, and nothing here answers
on its own: closing it while a call waits leaves the call waiting.

`bring` is the guest's one move, and the only one a program makes. It
hands the words in, names who brought them, and stops with exit 42:

    waiting on the host's call: proposal:7f50452d…

It can't seal, and no seat but the host's is ever asked.

**Offered once** (CONST-V-11). The same words under the same name wait
once, on whatever day they are brought again. What the host said no to is
not offered to them again by a guest:

    the host said no to this on 2026-11-21: it is not offered again

and what stands needs no asking (`this table has held this true since…`).
Bringing a no back is the host's own to do, at the table, with o. A word
that was true and has since been replaced or taken back may be said anew:
the table changed, so it is a new suggestion.

## The host's attention is the host's

Sitting down at your own table and finding someone already talking is an
interrogation, not a table. So:

- **The table opens on the host's own prompt.** What guests brought in is
  said in one sentence, and left alone.
- **Nothing is asked until the host asks for it**, by typing look. Then the
  calls come oldest first, two at a time, each numbered so the host knows
  where they are, and each saying what an answer does:

      3 of 7. Your call. Claude says:

         The narrator never gives their own name.

         Is that right? Type y to keep it, n to drop it, or s to skip it for now.

  After two, one line says how to go on, and both ways are one key:

      5 more. Press Enter for the next two, or type n to stop here.

  Stopping leaves the rest waiting, for as long as the host likes, and says
  how to come back to them.
- **Guests may leave at most five things waiting.** A sixth is refused,
  with why, until the host has answered some:

      refused: 5 things already wait on the host, and 5 is the most: nothing more is brought in until they have answered some

  What the host brings in at their own table, with o, is theirs and is
  never counted against it.

The count a guest is given back says the same thing to whoever brought it:
how many wait now, and that the host is asked only when they choose.

## A sitting

    The table

    Previously, this table made true:
      - The deposit comes back within thirty days of moving out.

    Just for you, from last time:
      Owed: ask in writing.

    Claude left 2 things here for you to look at. Type "look" to see the first two.

    What is the first bite?
    (Ask your files anything, your way. Enter on its own finishes. Type ? to see what else you can do.)
    > say The deposit comes back within forty days of moving out.
       Before you decide:
       on 2026-11-22 this table made this true:
       The deposit comes back within thirty days of moving out.
       1. Mine stands now
       2. Keep the old one
       3. Both are true
       4. Let me reword it
       Which? 1
       It's true now, and the old one is replaced.

    What is the next bite? (Enter on its own finishes. ? shows what else you can do.)
    >

What guests brought in is not in that picture, because the host didn't ask
for it. Typing look brings them, oldest first.

**What is typed.** The prompt asks "What is the first bite?", and a line
typed there is a question for the host's own files, unless it is one of the
table's own words: look, list, who, undo, pause, about, prep, want, say,
keep, read, `?`, or Enter on its own to finish. To keep something as
settled, say it: `say` (or `keep`), then the words. Typing `say` alone asks
what the host wants kept. Typing the words of a fact with no `say` does not
keep it.

## What each move keeps

| Move | At the table | On the record |
|---|---|---|
| say | `say`, the words, then y | a suggestion handed in, a `table-said` row, the kernel's seal |
| bite | a question, a fork's pick and why, then y | the forge's suggestions, handed in and sealed by the kernel on that y; the wants added to a stack page beside the box (see "The first bite") |
| call, yes | y | the kernel's seal over what was brought in |
| call, no | n | the kernel's decline |
| mine stands now | 1 at a heads-up | the new word sealed; a replacement handed in and sealed with it (`table-replaces`), so the old one stays and no longer stands |
| keep the old one | 2 | the new word not kept; one brought in is declined |
| both are true | 3 | a `table-both` row: the pair isn't raised again; no seal, since no truth changed |
| let me reword it | 4, for the host's own word | nothing, until the new wording is answered |
| take back | u, then y | a replacement whose new word is nothing, sealed; nothing takes a seal back, this stands over it |
| set aside | x at a call | a `table-x` row: no one named, no reason; the call waits |
| pause | p at any prompt | a `table-pause` row: no one named, no reason; exit 42 |
| end | Enter, a line to remember, then y | a `table-note` row in the host's words; the sitting bundled by session-seal and sealed as one; the record checked |

**The heads-up** is the contradictions add-on's rule, read from the box's
own record: two lines are about the same thing when they share at least two
of their own words, and at least half the shorter one's. It can't tell
agreeing from disagreeing, and never picks a side: it asks, and "both are
true" is there for the pair that agrees. The same words again, and a pair
the host already called both true, are never raised. Without that add-on
beside this one there is no heads-up, and `moves` says so.

**A note for next time** is the host's own words, kept as a row and shown
only when they next sit down. It is never sealed and never a truth of the
table.

**A long list of what is settled** opens on its newest three, then one
line:

    and 4 more, settled earlier. Type "list" to read them all.

A table with matters opens on all of what is settled, a matter at a time.

`stands` prints what the table holds true now, oldest first, each with the
day it was made true and who brought it. `--json` gives the same as data.
It reads, and writes nothing.

## One table, several matters

A life is not one matter. A box made from several folders, each under a
name, is one table over all of them:

    python kernel.py init --box BOX --from move=FOLDER --from work=FOLDER --from girls=FOLDER --key FILE

Each name is a **matter**. There is still one record, one sitting, and one
seal at its end.

- **The host says which matter the next words are about** with m, by its
  number or its name; 0 is no matter, the table itself. The prompt shows it.
- **A guest says it** with `--at MATTER`. A matter the table doesn't have is
  refused, naming the ones it has.
- **What stands is read back a matter at a time**, the table's own first,
  then A to Z; `stands --at MATTER` gives one alone.
- **The heads-up looks across every matter**, and says which one the older
  word was about:

      girls> say The girls are away with their mother for the school holiday week.
         Before you decide:
         on 2026-11-21 (about move) this table made this true:
         The truck is booked for the school holiday week.

  That is what one table is for. Kept apart, the move's box would never
  have shown the girls' word, nor theirs the move's.
- **The same words about another matter are another suggestion**, with its
  own answer.

A box over one folder has no matters, and nothing here changes for it.

What it does not do: it doesn't put two dates side by side. The heads-up
goes by the words two lines share, and leaves out numbers, months and
weekdays, so "the truck comes on the 15th" and "the recital is on the 14th"
are not raised. Dates across matters are the coming-up add-on's to show,
and today it reads one folder, not a box of several.

## The first bite

The prompt is "What is the first bite?" A line typed there that is no other
move is a question for the host's own files, asked their way, and handed to
the forge add-on. The forge drafts the steps that could answer it. Typing
`want` on its own still works: it asks the same thing, "What do you want to
find out before you sit down?", and goes the same way.

A word that could mean more than one card is put as one plain question, and
then the table asks why, in a few words, or just Enter:

    > what is due and what I still have to do

       “due” could be answered more than one way:
       1. coming-up: Dates written in your files in the next N days: appointments, renewals, deadlines.
       2. renewals: Passports, licences, insurance and memberships: when each expires, from your documents.
       Which would you like? A number, two as 1,2, n for neither, or s to leave it for later. 1
       Why coming-up for “due”? A few words, or just press Enter:

Then what would be written is shown, and one question is asked: put them on
it? Only on that yes is anything handed in. The host's typed picks and that
yes are what seal the forge's suggestions, by the kernel, as any call's
answer is. Leaving before the yes writes nothing. A fork left for later
(`s`) puts nothing on a page, and that it was left is kept as a decision of
its own, as the forge keeps it.

**Where the wants go.** They are added to the folder's own stack, `stack.md`
beside the box, under a heading of their own, with no step put in twice:

    Then these would be added to your own stack here, stack.md:
    - todo: TODO, FIXME and "need to" lines across the folder, oldest first.
    - coming-up: Dates written in your files in the next N days: appointments, renewals, deadlines.
    ...
    Put them on it? (y/n) y
    Added to your own stack, DIR/stack.md: 4 new steps, and 1 it already had.

A stack the folder makes from a `stack.src` is left alone, and `prep.md` is
used, with a line saying so. A folder with no stack gets a `prep.md`:

    They are on your prep sheet now (5 steps): a page of proposals you can cut from, in DIR/prep.md. Typing "prep" runs it again any time.

**Asked, so answered.** Once the wants are on a page, just what the bite
asked is run, at once, and no other step of the stack. The run is kept under
`bites/001`, `bites/002` and so on, beside the box, with a page for each
step. It is read back a want at a time, with up to five of the lines each
step found, each with its file and line, then "and N more, in its page."
when there are more:

    Here is what that found:
      Want 1: “what is due and what I still have to do”: todo (what “still have to do” usually means here).
         todo: populated, 1 line marked to do, none dated
           TODO: ask for the deposit terms in writing.  (notes.md:2)
      Want 2: “due”: coming-up, not renewals, because deadlines.
         coming-up: empty, nothing dated between 2026-11-22 and 2026-12-06
      ...

    Each one's page is in DIR/bites/001

The sentence names `todo` itself, from “still have to do”, so it is the
first want; “due” is the fork, and its answer is the second.

**Beside the steps.** After a bite, up to three lines say what the person's
other stacks put beside those steps, under "Your other stacks put these
beside those steps:". These come from the forge's `next`, which looks at the
folders beside this table's own that have a stack. It only reads. When there
is nothing to say, nothing is said.

**A bite can be a page.** A page's name, or `read NAME`, is read instead of
being taken as a sentence. The page is found under the folder the box reads,
beside the box, or at the path as typed. The forge's same scan is given its
text, and each line that asks for something is shown with its line number:

    > read lease.md
       I read lease.md. These are the lines in it that ask for something:
         lease.md:3  The deposit is due back within thirty days.  (“due”, “back”)
         lease.md:4  TODO: get the key copied.  (“todo”)

The first line each word reaches is the one shown, cut at 100 characters.
The want is kept in those words and the page's name, not the page's text.
The first 100,000 bytes are read, and a long page says so. A page that isn't
text is refused, and so is a `read` of a name there is no page for. From
here the bite goes as any other does.

## A table's sheets: before a sitting, and after

A table may keep two pages beside its box, each a stack of wants in the
host's own words, the way a game master keeps a prep sheet:

    prep.md   run before a sitting, when the host asks for it
    end.md    run when the host ends a sitting, before it is sealed

Each is a stack file for the stack add-on: a want, why a card answers it,
then the step. They are proposals: cut any, add your own.

    ## what I owe

    Want 1: "What do I still have to do?" The lines I marked to do.
    - todo -- --box {box}

Typing prep runs the prep sheet and reads it back a want at a time, each
with what its step said and up to five of the lines it found:

    Your prep sheet, run just now:
      Want 1: "What do I still have to do?" The lines I marked to do.
         todo: populated, 8 lines marked to do, the oldest from 2026-11-02
           2026-11-02  TODO: ask for the deposit terms in writing.  (notes.md:2)
           2026-11-02  TODO: item 1 of the move.  (notes.md:3)
           2026-11-02  TODO: item 2 of the move.  (notes.md:4)
           2026-11-02  TODO: item 3 of the move.  (notes.md:5)
           2026-11-02  TODO: item 4 of the move.  (notes.md:6)
           and 3 more, in its page.

    Each one's page is in DIR/prep/001

Every run is kept in a folder of its own beside the box, numbered, with a
page for each step. Nothing runs until the host asks, and a sheet seals
nothing. The end sheet runs after the host says the sitting is over; it may
bundle the sitting itself with a session-seal step, and when it doesn't the
table does, so a sitting is sealed once either way.

This is Die-Namic's own shape, taken as it is: its prep sheet, its end of
the night and its family night are pages of exactly this kind. The forge
add-on drafts one from what a person says they want, each want carrying what
it was chosen over and why. Without the stack add-on beside this one a table
has no sheets, and says nothing of them.

It needs the forge add-on and what that installs. Without them the table
says a sheet can be written by hand, and how.

## The words are a table's own

Every line a person reads is in one list in `table.py`, and `--words FILE`
replaces any of them, a name and its text on a line:

    title: Die-Namic
    call: Your call, GM.
    is_true: Is that true in your world? (y/n)
    done: That's our night? (y/n)

A line starting with `#` is a comment. A name the list doesn't have is
refused, so a slip is never silent. What the record keeps is the same
whatever the words. At the front door a table's words are read from
`table-words.txt` beside its box.

## No future at the table

A table keeps what happened and what was decided. It has no way to keep
what will happen, and that is on purpose.

- **A chance is shown only where the outcomes can be counted:** a roll, a
  draw, a table of results. That is play-odds' work, and it is exact because
  every outcome can be listed.
- **What a person, an office or a month will do can't be counted.** A number
  put on it is somebody's guess, and running a made-up board many times
  measures the board, never the world. Such a guess is a guest's word like
  any other: brought in under a name, waiting on the host, and never shown
  as odds.
- **A date is something on the table, not what decides it.** A sitting ends
  when the host says so. A day that passes changes nothing that stands.

The world can be played as a game. Nobody lives in the game: the host gets
up from the table, and what was made true is still theirs.

## What it doesn't do yet

- **A sheet, and the chances.** What a seat carries between sittings, and
  each way forward with its odds, are a game's own today (the play add-ons'
  and play-odds').
- **A guess, settled.** A forecast written down, settled against the day
  and scored is still an idea (horoscope-grades, ninety-percent, tides).
  Until one is built, a guess brought in here is only a word that waits.
- **A bite's run is kept apart.** It goes under `bites/` beside the box, not
  into the folder's own run folders.
- **A folder with a stack and no box can't be asked.** The front door names
  it, and that is all.
- **A page is read for its first 100,000 bytes**, and each word it reaches
  shows only the first line that has it.
- **A word longer than one passage** (500 characters) is refused, and said
  shorter or in two.
- **A slip from an earlier sitting** can't be taken back with u: say the new
  word, and choose "mine stands now".
- **Taking back a word that replaced another** leaves both set aside: the
  older one does not stand again. Say it again to make it true.

Exit codes, the kernel's: 0 the sitting ended, or `stands` and `moves`
printed; 42 something waits on the host (a call, a pause, a sitting left
open, what `bring` handed in), or `stands` found nothing; 2 refused (a bad
command line, not a box, a record that doesn't check out, a words file
naming a word the table doesn't have).

**Uses:** the kernel's `read`, `append`, `sealed`, `declined`, `standing`,
`subject_of`, `stem`, `h256`, `now` and exit codes, and its commands `bite`,
`propose`, `seal`, `decline` and `verify`; and, as a guest, the forge
add-on's `suggest`, `propose` and `next`, and the stack add-on's runs.

**Never:** seals without the host's typed answer; answers for the host by
any option; names a person in a set-aside or a pause; changes or removes a
row; reads the key (the kernel does); goes online.
