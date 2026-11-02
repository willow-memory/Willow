<!-- willow-addon
section: Finding things
line: Is this exact quote in my files, and where? For writers, journalists and students.
source: box
added: 2026-10-23
writes: nothing
network: none
-->
# quote-check

Is this exact quote in my files, and where? For writers, journalists and
students checking a quote against their own sources.

    python adapters/stdlib/quote-check/quote_check.py --box DIR "the quote"

    verbatim     letter.txt:2
    same words   draft.md:1   (spacing, case or punctuation differ)

"verbatim" means the very characters, spacing aside, and the line given is the
one the quote starts on. "same words" means the same words in the same order,
which is how a quote is usually mangled. Words are split the kernel's way. A
quote is matched within one paragraph; one split across a blank line is two.

**Exit codes:** 0 found; 42 not in your folder; 2 refused.

**Uses:** the kernel's `chunks`, `words` and `config`.

**Never:** writes anything.
