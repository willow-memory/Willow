<!-- willow-addon
section: Your own words
line: The names you call people, mapped to who they are, so 'Mum' finds Margaret.
source: new
added: 2026-10-29
writes: to
network: none
-->
# nicknames

"When is Mum's appointment" finds the note that says Margaret.

A question matches words as written, so "Mum" holds nothing in files that
only ever say "Margaret". A words list teaches the kernel that one word is
another (see [starter-words](../starter-words/)). This writes one from what
your own files say about who is who.

    python adapters/stdlib/nicknames/nicknames.py --from FOLDER --to FILE
    python adapters/stdlib/nicknames/nicknames.py --box DIR --to FILE --both

    mum = margaret    family/notes.txt:1  (3 mentions)
    wrote FILE: 1 nickname

and FILE, the kernel's words list, with where each line came from:

    # family/notes.txt:1 (3 mentions) mum = margaret
    mum = margaret

Where a family word (mum, mom, dad, gran, nana, grandad, auntie, uncle, sis,
bro, hubby and their kin) sits beside a capitalised name, the nickname is read
as the name. The shapes:

| Written as | Read as |
|---|---|
| Mum (Margaret) | mum = margaret |
| Margaret (Mum) | mum = margaret |
| Margaret, my mum | mum = margaret |
| my mum Margaret, my mum is Margaret | mum = margaret |
| Auntie Jean, Grandad was Albert | auntie = jean, grandad = albert |

A day, a month, a word like "The" and a chat's speaker label ("Dad: Thank
you") is no name, and father, mother, brother and sister are left out since
they are often a title, as in Father Liam. With `--both` the list also reads
the name as the nickname, so "Margaret" finds what is written "Mum".

A nickname that two names claim is kept with both and said on standard error,
since it may be two people or a slip. Everything it writes is a lead: it
copies what you wrote and cannot know who a nickname *is*, so read the list
before you use it. A place name beside a family word ("Brookhollow (Dad)")
reads as one too, and the evidence line shows why.

FILE is the kernel's words list: keep it outside the box, readable only by
you. It is written once, that way, never over a file that exists, and only
after the kernel has read it. Your files are only read, hidden folders and
binary files left out.

Exit codes, the kernel's: 0 written; 42 no nickname found, nothing written;
2 refused.

**Uses:** the kernel's `parse_words`, and its limits on a file read.

**Never:** changes your files, or writes anywhere but FILE.
