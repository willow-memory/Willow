<!-- willow-addon
section: Keeping track
line: Passports, licences, insurance and memberships: when each expires, from your documents.
source: new
added: 2026-10-27
writes: nothing
network: none
tags: no-install, offline, read-only, tracking
-->
# renewals

Every line of your folder that says an expiry and its date, soonest first,
what's already gone by marked: the register of the things you hold —
passports, licences, insurance, registrations, memberships — kept by your
own documents.

```
python adapters/stdlib/renewals/renewals.py --box DIR [--now TS]

gone by  2024-01-31  ids/passport.md:3      Passport expires 2024-01-31.
         2026-03-04  mail/racv.eml:12       Your policy HC-7718203 renews on 4 March 2026.
         2026-10-31  work/insurance.txt:4   Your cover ends on 31/10/2026 unless renewed.
3 renewals: 1 gone by, 2 to come
```

**What counts.** A line that says one of the expiry words — expires, expiry,
expiration, renew and its forms, valid until (till, through, thru), cover
ends, ends on — and says its own date on the same line. A date is read as
the kernel reads one (its `newest`; `03/11/2025`, reading either way round,
is never guessed), or written out with a month's name and its day (4 March
2026; March 4, 2026; the 1st of June 2027). A renewal that names no day
("renews March") says too little to place, and an expiry whose date only a
nearby line holds is not stitched together: the line that tells you when is
the one cited, and both silences are said here so they aren't passes.

**Gone by is by the clock you give.** `--now`, an ISO timestamp (the
kernel's kind), marks what has passed; without it, today. Nothing is
reminded, totalled or renewed for you, and a past "Renewed 22/04/2026" line
is listed as your file wrote it: the register shows what the documents say,
you decide what needs doing. The next few weeks' view is
[coming-up](../coming-up/)'s job; the things themselves are this one's.

On willow's demo folders: Hollis's referral, "valid through November 10,
2026", is his one renewal to come; Teodora's car insurance and Bernadette's
RACV policy ("renews on 4 March 2026", written out in an email) are theirs;
Odile's folder says no expiry with its date, and it says so. Bernadette's
"Registration expiry: 03/11/2026" reads either way round, so it is never
guessed — her registration is the ambiguity rule earning its keep.

It only reads, and the same folder and clock give the same bytes. Exit
codes, the kernel's: 0 renewals found; 42 none; 2 refused.

**Uses:** the kernel's `chunks`, `newest`, `now` and `config`.

**Never:** changes your files; writes anything, even the record; guesses a
date that reads two ways; stitches an expiry to another line's date.
