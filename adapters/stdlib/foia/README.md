<!-- willow-addon
section: Keeping track
line: Freedom-of-information requests: what you asked, when, and when the answer is due by law.
source: new
added: 2026-10-29
writes: nothing
network: none
-->
# foia

Freedom-of-information requests: what you asked, when, and when the answer is
due by law.

```
python adapters/stdlib/foia/foia.py --box DIR [--law us|uk|au|ca|nz|ie] [--now TS]

Police        sent 2026-03-05  due 2026-04-02  open, overdue 27 days
Fire Service  sent 2026-04-01  due 2026-04-29  open, due today
Home Office   sent 2026-02-02  due 2026-03-02  answered 2026-03-02 (on the day)
City Council  sent 2026-03-02  due 2026-03-30  answered 2026-03-27 (3 days early)
4 requests: 2 answered, 2 open
```

**A request** is a line, on a day, that says freedom of information, FOI, FOIA,
public records, OIA, ATIP or right to information, and that you sent, filed,
submitted, requested, asked, made, emailed or posted it. **An answer** is a
later line about the same body that says received, replied, response, answered,
released, disclosed, refused, denied, rejected or withheld; it closes the latest
earlier request to that body that is still open. A line that only says the
request was acknowledged is neither. The body is the capitalised words after to,
with, from, at or by ("FOI request to City Council"), else the name the line
starts with. An answer that matches no request is counted, not dropped.

**When it is due** is the date the line says after "due", else the day sent plus
the time the law of `--law` gives: us, uk, nz and ie 20 working days; au and ca
30 days. Days are counted from the day after it was sent; working days are
Monday to Friday, and public holidays are not known to this, so a real deadline
can fall a few days later than the one shown. Without `--law`, and with no "due"
on the line, no deadline is guessed. Open requests come first, the longest
overdue first. Distances are from `--now` (an ISO timestamp, the kernel's kind;
today if not given).

These are the general times: a body may extend them, and an appeal has its own.
Nothing is sent or chased for you.

It only reads. Exit codes, the kernel's: 0 requests found; 42 none; 2 refused.

**Uses:** the kernel's `chunks`, `newest`, `config` and `now`, and
[habits](../habits/)' `file_lines`.

**Never:** changes your files; writes anything, even the record; contacts a
body or an appeals office.
