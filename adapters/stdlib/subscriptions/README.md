<!-- willow-addon
section: Keeping track
line: What you pay for every month, found in bank statements and emails, and when each renews.
source: new
added: 2026-10-29
writes: nothing
network: none
-->
# subscriptions

What you pay for every month, and every year, found in your statements and
emails by the rhythm of the payments, and when each comes round next.

```
python adapters/stdlib/subscriptions/subscriptions.py --box DIR

gym         29.00  monthly  last 2026-04-02  next about 2026-05-02  (4 payments)
netflix     15.99  monthly  last 2026-03-05  next about 2026-04-04  (3 payments, was 12.99)
dropbox    119.88  yearly   last 2026-11-02  next about 2027-11-02  (2 payments)
3 subscriptions: about 44.99 a month, 659.76 a year
```

A payment that comes round on a calendar is a subscription whether or not
anyone called it one. **What counts** is a line that says its own date (a
statement's row does; a sentence under an email's header does not, and a date is
never borrowed from above), with an amount written to the cent (15.99, -15.99,
£1,240.50, $9.00), and some words saying what it was for. The words are the
line's letters without its dates, its numbers and the stock words of a
statement (card, purchase, payment, debit, visa, direct, eftpos, pos, ref,
transaction), the first three kept: "NETFLIX.COM  -15.99  card purchase" is
"netflix". The same words on the same day in two files are one payment.

**A rhythm** is every gap between a thing's payment days being about a month
(26 to 35 days) for three payments or more, or about a year (355 to 375 days)
for two or more. Anything else, however often it is paid, is not called a
subscription: a coffee bought on Fridays and then not for a month is a habit,
not a plan. The amount is the latest paid; an earlier different amount is said
("was 12.99"). "Next about" is the last day plus a month or a year: a guess at
when to look, not a promise from anyone.

Dearest first by what it costs in a year. A line does not say which way money
went, so a deposit that comes round (a wage, a refund) is found as well as a
payment. Amounts are shown without their currency sign, as they stand in the
line, and two currencies are not added. On willow's demo folders it finds
Teodora's direct debits, Hollis's mortgage, insurance and phone, and
Bernadette's Netflix, rego and super; it also finds the odd email's recurring
"paid" line, which is a rhythm all the same.

Nothing is cancelled, and nothing is called a subscription that your files do
not show paid on a rhythm. It only reads. Exit codes, the kernel's: 0
subscriptions found; 42 none; 2 refused.

**Uses:** the kernel's `chunks`, `newest` and `config`, and
[habits](../habits/)' `file_lines`.

**Never:** changes your files; writes anything, even the record; cancels or
contacts anyone.
