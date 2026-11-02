<!-- willow-addon
section: Trust and proof
line: A claim checked against your sources: the passages that hold all of its parts, the ones that hold only some, and the parts no file names.
source: new
added: 2026-10-24
writes: nothing
network: none
-->
# claim-check

A claim checked against your sources, part by part.

    python adapters/stdlib/claim-check/claim_check.py --box DIR "the claim" [--top N]

    some parts   policy.txt:203   google, gmail, ads   lacks scans
    some parts   policy.txt:981   google, gmail, ads   lacks scans
    no file has  scans

A claim is made of parts. "Google scans Gmail for ads" needs Google, scans,
Gmail and ads in one place before a source can be said to back it. The
kernel answers a question with the passages that hold half its words or
more; claim-check asks for all of them, and says what's missing:

- **all parts**: every passage holding every part;
- **some parts**: the passages holding the most parts short of all, up to
  `--top` (3), each with what it lacks;
- **no file has**: the parts nothing in your folder holds at all.

Parts are the claim's words less the kernel's common ones ("the", "for",
"is"), read the kernel's way: a word or its plain form (scans and scan are
one), in the passage or its file's path, and through your words list if the
box has one.

**It finds where to read; it never reads for you.** A passage holding every
part may deny the claim ("we never scan email for ads" holds all three of
"scan email ads"), and one holding some may back it in other words. The
strongest thing it says is the last line: a part no file has is a part
nothing in your folder names.

**What it was built for:** in
[demo/google-privacy-2026-10-16](../../../demo/google-privacy-2026-10-16/),
"Google scans Gmail for ads" needed a frozen rule and three kernel boxes.
claim-check says it in one command: the nearest passages hold google, gmail
and ads, and none holds "scans". The planned `thesis` add-on would run it
over every claim in a document.

**Exit codes:** 0 some passage holds every part; 42 none does; 2 refused.

**Uses:** the kernel's `chunks`, `config`, `words`, `FUNCTION`, `toks`,
`held_by` and `read_words`.

**Never:** writes anything.
