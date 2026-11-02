<!-- willow-addon
section: Privacy and safety
line: Strips the hidden details (EXIF, author, edit history) from a file before you share it.
source: new
added: 2026-10-29
writes: to
network: none
-->
# scrub

The details a file carries that you didn't mean to share.

A photo carries the camera, the time, and often the place it was taken. A
Word file carries who wrote it, who saved it last, and when. This writes a
copy without those details and says what it took out.

    python adapters/stdlib/scrub/scrub.py --from FILE --to FILE

    removed  Exif (Make, Model, DateTime, GPS): 3,402 bytes
    removed  XMP packet: 1,180 bytes
    kept     the orientation, so the photo still shows the right way up
    wrote FILE: 2 removed

The kind of file is read from what is inside it, not its name:

| Kind | Taken out | Kept |
|---|---|---|
| JPEG | Exif (camera, time, GPS), XMP, IPTC and Photoshop blocks, comments, other application blocks | the picture, the colour profile, and the orientation |
| PNG | text chunks (Author, Software, Comment...), Exif, the time of last change | the picture and its colours |
| docx, xlsx, pptx | author, last saved by, created and modified times, revision, keywords, description, company, manager, custom properties; a Word file's edit-session ids; the names on comments and tracked changes; the zip's file times | the text, tables and slides, and the title |

The orientation is kept because a photo with its Exif gone would otherwise
turn on its side. Tracked changes are not accepted or rejected: they stay and
their authors go. A page thumbnail inside an Office file is said and left,
because removing it means rewriting the file's index.

Anything else is refused and not copied unchanged: a copy that claims to be
scrubbed and isn't is worse than none. PDFs, audio and video are not handled
yet. A name typed into a document's text, a face in a photo and a street sign
in the background are not hidden details and stay: this strips what a format
keeps in a known place.

FILE is not changed. The copy is written once, readable only by you, never over
a file that exists, and the same bytes for the same file.

Exit codes, the kernel's: 0 written; 2 refused (a bad command line, a kind of
file it doesn't handle, a file it can't read, a copy that already exists).

**Uses:** the kernel's exit codes; Python's zipfile, struct and zlib.

**Never:** changes the file it reads, or writes anywhere but FILE.
