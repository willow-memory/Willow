<!-- willow-addon
section: Keeping track
line: Meeting minutes: who decided what and when, and which actions are still open.
source: new
added: 2026-10-29
writes: nothing
network: none
-->
# minutes

Meeting minutes read for what was decided and what is still to do: who decided
what and when, and which actions are still open.

```
python adapters/stdlib/minutes/minutes.py --box DIR [--open]

decisions
  2026-03-02  board/march.md:4  Move the AGM to May.
actions open
  2026-03-02  board/march.md:6  Ana  send the figures by 2026-03-09  (due 2026-03-09)
actions closed
  2026-03-02  board/march.md:7  (no owner)  Book the hall - done
1 decision, 1 open action, 1 closed
```

**A decision** is a line that opens with Decision, Decided, Agreed or
Resolved. **An action** opens with Action (or Action item), AI or Todo.
Bullets, numbering, bold marks and a checkbox in front are ignored, so
"- **Action:** Ana to send the figures" is read.

**Its owner** is what the line says up front: "@ana", "(Ana)", "Ana to send",
"Ana will send", or "Ana: send". A line that names no one is "(no owner)";
none is guessed. A date it says after "by" or "due" is its due date.

**Open or closed.** An action is closed when its own line says done,
completed, closed or finished, or has a checked box [x]; or when a later line
(in any file, on its day or after) opens with "Done" and says the same words
as the action, owner included. Anything else is open. Nothing is chased or
reminded.

A line that shouts throughout, such as a calendar's ACTION:DISPLAY, is a
machine's and is never read. A line's day is the latest date it says before any "by", "due", "before" or
"until" (a due date is not the day of the meeting), else the nearest date
written above it in its file, else the date its file is named for; a line no
day reaches is left out. `--open` shows only the open actions.

It only reads. Exit codes, the kernel's: 0 something found; 42 no decision
or action; 2 refused.

**Uses:** the kernel's `chunks`, `newest`, `words` and `config`, and
[habits](../habits/)' `file_lines`.

**Never:** changes your files; writes anything, even the record.
