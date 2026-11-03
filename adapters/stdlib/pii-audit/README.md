<!-- willow-addon
section: Privacy and safety
line: Personal data sitting in your files (ID numbers, health details, card numbers), listed by file and line.
source: new
added: 2026-10-27
writes: nothing
network: none
output: report
-->
# pii-audit

Before a folder is shared, backed up somewhere new, or handed to a tool:
the identifying numbers sitting in it, each by file and line, shown masked.

```
python adapters/stdlib/pii-audit/pii_audit.py --box DIR [--json]
python adapters/stdlib/pii-audit/pii_audit.py --from FOLDER [--json]

pii-audit: populated, 3 personal numbers in 3 of 254 files
## a card number
  money/orders.csv:17  ···· 4242
## a National Insurance number, by shape
  work/p60.txt:9       ···· 45C
## an NHS number
  health/letter.txt:3  ···· 6789
```

It prints [a report](../ci/README.md#the-report-contract), the shape every
report add-on shares: a line saying what it found, then a group per kind,
each row where it sits and then what it is. `--json` gives the same report
as one JSON object.

**Every number is checked, not guessed.** A card number must pass the Luhn
check (13 to 19 digits, spaces or dashes between groups); a US Social
Security number and a UK National Insurance number their strict written
shapes, which carry no checksum, so their rows say so. An NHS number, an
Australian Medicare number and a tax file number must pass their own
weighted checks **and** their line must say what it holds (nhs, medicare,
tfn, tax file): one ten-digit run in ten passes such a check by luck — a
chat's timestamp, a phone number — and an audit doesn't flip coins. On
willow's demo folders that rule is the difference between 283 timestamps
crying wolf and Odile's six real card numbers in her invoices and books.

**A run that passes nothing is nobody's number** and is never listed; one
that passes two checks says both, since the digits can't say which it is;
a run holding a written date (2027-01-09) is dates, since no number is
grouped that way and two dates side by side pass Luhn one time in ten;
and one sixteen-digit order number in ten will pass Luhn, so a card row is
a place to look, not a verdict. What has no checkable shape at all — a
diagnosis, an address, a name — this cannot find, and that silence is said
in the output so it is never mistaken for a clean bill.

**The audit never repeats the number.** Each row shows the kind, the last
few digits, and where it sits: enough to go and deal with it, nothing worth
stealing from the audit itself. Secrets — keys, tokens, passwords — are
[secrets-audit](../secrets-audit/)'s; the numbers that identify a person are
this one's.

It only reads, through the kernel's own `chunks`, so what the kernel
searches is exactly what is audited, and the same folder gives the same
bytes. Exit codes, the kernel's, as the audits use them: 0 nothing found
(empty); 42 personal numbers found (populated), or nothing there to check
(unreachable); 2 refused.

**Uses:** the kernel's `chunks` and `config`.

**Never:** changes your files; writes anything, even the record; prints a
number whole; lists a run its checks don't own; calls its silence a clean
bill.
