<!-- willow-addon
section: Keeping track
line: Applications sent, replies and interviews, by date: who you're still waiting on.
source: new
added: 2026-10-29
writes: nothing
network: none
uses: habits
-->
# job-hunt

Applications sent, replies and interviews, by date: who you're still waiting
on.

```
python adapters/stdlib/job-hunt/job_hunt.py --box DIR [--now TS]

Acme (Designer)  interview 2026-03-10  after applied 2026-02-20  waiting 233 days
Initech          applied 2026-09-01  waiting 58 days
Umbrella         applied 2026-10-28  waiting 1 day
Globex           rejected 2026-03-02  after applied 2026-02-10
Hooli            offer 2026-09-15  after applied 2026-08-01
5 applications: 3 waiting, 1 rejected, 1 offer
```

**What counts.** A line, on a day, about a job search (the line or the path of
its file says job, application, CV, resume, recruiter, vacancy, role, position,
hiring or career) that names a company and says one of: applied (applied,
application sent, sent my CV), replied (replied, heard back, got back),
interview (interview, phone screen, assessment, take-home), followed up
(followed up, chased), rejected (rejected, declined, not moving forward,
unsuccessful, regret) or offer. A line that says several takes the strongest
(offer, then rejected, interview, replied, followed up, applied). The company
is the name that starts the line ("Acme: applied"), else the capitalised words
after "to", "at", "with", "from" or "for"; a role in brackets is kept. A line
naming no company is left out. The day is the line's latest date (the kernel's
`newest`), else the nearest date written above it in its file, else the date
its file is named for.

**Where it stands** is the company's latest event. A company whose latest is
rejected or offer is finished; any other is waiting, and the days are counted
from that event to `--now` (an ISO timestamp, the kernel's kind; today if not
given). Waiting longest first, then the finished. Nothing is sent or chased
for you.

It only reads. Exit codes, the kernel's: 0 applications found; 42 none; 2
refused.

**Uses:** the kernel's `chunks`, `newest`, `config` and `now`, and
[habits](../habits/)' `file_lines`.

**Never:** changes your files; writes anything, even the record.
