# The kernel's rank, for agents

What the kernel's search promises, and the jobs that need another one. Part
of [AGENTS.md](../../AGENTS.md).

`kernel.rank` serves a passage only when it holds half the question's content
words. That is the promise that an answer the folder doesn't have is never
invented, and the eight beats in `test_kernel.py` test it.

- **Don't loosen it for recall.** A third of the words, or any two, finds a
  few more on code, but answers questions about something else several times
  as often, and breaks the beat where a folder holding only the question says
  so.
- **Pointing at where to look** is another job: `scan --rank bm25`, which
  always serves its top passages.
- **Comparing two texts** is another job again: count against the shorter
  one, so a long line doesn't hide a short one it contains.
- **Use the kernel's public names.** A page's text is `kernel.html_text`, not
  `_TAG` and `_lines_kept`.
- **A passage that asks the question back is an echo**, marked and not
  served as an answer (`kernel.echo`): it holds the whole question's words in
  a row, in order, for a question of three words or more, or eight of them in
  a row for a longer one. A test passage built that way tests the echo rule,
  not the answer: put its words in another order.
