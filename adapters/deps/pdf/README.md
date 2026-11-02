<!-- willow-addon
section: Reading more kinds of files
line: Text out of PDFs.
source: new
added: 2026-10-23
needs: pypdf; BSD-3-Clause
floor: pypdf 3.1.0; the 2020 rule names 1.9 from 2014, a Python 2 release under the same name, and 3.1.0 is the first since it was revived
writes: to
network: none
-->
# pdf

Text out of PDFs, into a mirror folder the kernel can search. The first
add-on in `adapters/deps/`: it needs one package, pinned in
[requirements.txt](requirements.txt).

    pip install -r adapters/deps/pdf/requirements.txt
    python adapters/deps/pdf/pdf.py mirror --from FOLDER --to MIRROR
    python kernel.py init --box BOX --pile MIRROR --key KEY

Each .pdf becomes `MIRROR/<same path>.txt`, one paragraph per page, headed
`== page N`, so an answer says which page it came from.

**The reader contract** (shared with every file reader): hidden files and
folders are skipped; nothing is written inside FOLDER and no original changes;
MIRROR inside FOLDER, or the other way round, is refused; the same PDF always
gives the same bytes; a corrupt or password-protected PDF is skipped and
counted, never a crash.

**Can't:** read a scanned page, which is a picture with no text in it (the
planned `ocr` add-on is for that). Columns and tables come out in the order
pypdf reads them.

**Without pypdf** it refuses and names the install: exit 2, never a quiet
skip.

**Uses:** the kernel's exit codes.

**Never:** writes inside your folder, changes an original, or goes online.
