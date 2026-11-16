<!-- willow-addon
section: Finding things
line: A question that asks two things in one breath, split into parts, each asked by the kernel's own rule so neither loses the other's words.
source: new
added: 2026-11-16
version: 0.1.0
writes: nothing
network: none
role: tools
-->
# ask-parts

A question that asks two things in one breath, split into parts, each asked by the kernel's own rule so neither loses the other's words.

    python adapters/stdlib/ask-parts/ask_parts.py [--box DIR] "your question"

"what did colleen say about mam's headstone, how much was my half" asks two
things. The kernel serves a passage only when it holds half the question's
content words, so the email that says "Your half is 725 euro" holds one of
five and is never served, though it is what the second half asks. Asked on
its own, "how much was my half" finds it.

**Where it splits:** at a comma, a semicolon, "and" or "also" (", and also"
is one break), and only where each side is itself a question: it opens with
a question word (what, how, did, is, ...) and holds a content word (the
kernel's own `words` minus `FUNCTION`). "scone recipe", "salt and pepper",
"tom and jerry's address" and "what is salt and pepper" stay whole; so does
anything inside quotation marks, and a question with a quote left open. A
side that isn't a question of its own stays in the part before it. A
question of one part comes back as typed.

**Each part is asked alone,** not with the first part's words added: with
them "half" is one of five words again and nothing is served (a test holds
both). The kernel's ranking is the judge, not a guess.

Without `--box` it prints `{"parts": [...]}`. With one it asks each part of
the pile by the kernel's own `rank`, the same rule, order and words list as
a bite, and prints each part with its `bite_key`, its state and its passages,
like a bite's. `kernel.py` is never changed and no rank is loosened.

**To cite a part's passages,** bite that part through the kernel,
`kernel.py bite --box DIR "<the part>"`: it serves exactly what is printed
here. A proposal reaches only what the box's last bite served, so bite the
parts in turn and propose after the one whose passages you cite; one bite
serves one part. A part with a sealed answer shows as sealed in the kernel's
bite, which this doesn't look for.

**Exit codes:** 0 every part is held by something; 42 a part nothing holds,
left to the person; 2 refused.

**Uses:** the kernel's `words`, `FUNCTION`, `bite_key`, `config`,
`read_words`, `chunks`, `rank`, `echo` and `read`.

**Never:** writes to the record: it serves nothing an approval can cite.
