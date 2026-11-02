<!-- willow-addon
section: Keeping track
line: Spending against the budget you wrote down, month by month, from your statements.
source: new
added: 2026-10-29
writes: nothing
network: none
uses: habits
-->
# budget

Spending against the budget you wrote down, month by month, from your
statements.

```
python adapters/stdlib/budget/budget.py --box DIR

groceries  budget 400.00 a month
  2026-02    312.40 of 400.00   78%  under by 87.60
  2026-03    455.10 of 400.00  114%  over by 55.10
transport  budget 120.00 a month
  2026-03     96.00 of 120.00   80%  under by 24.00
2 categories, 1 month over budget
```

You write a budget in your own words, one line for each category, and the
statements' lines are matched to it by the words you gave:

```
2026-01-01 Budget: groceries £400 a month (tesco, aldi, coles)
```

**The budget** is a line that says its own date and "budget", then the category
(one or two words: groceries, eating out), then an amount, and says "a month",
"per month", "monthly" or "/month", and may give the words that mark the
category's spending in brackets. With no brackets, the category's own words are
the markers. A later budget line for the same category replaces an earlier one.
Budgets are monthly only.

**The spending** is any other line that says its own date, with an amount (a
number with cents, or a sum with a currency sign), and one of a category's
markers as a whole word, any case: "2026-03-04,TESCO STORES 3241,-45.20" is
groceries. Its first amount counts, whichever way the sign points. The same
day, words and amount in two files are one payment. A line that matches two
categories counts for the first budget written. A line that matches none is
left out; no category is guessed for it.

Months with spending are shown, oldest first. Nothing is scolded or advised: a
month is over budget by arithmetic only. On willow's Teodora demo, with a
budget line added for her rent, her bank rows show the same 575.00 under it
every month.

It only reads. Exit codes, the kernel's: 0 a budget found; 42 none; 2 refused.

**Uses:** the kernel's `chunks`, `newest` and `config`, and
[habits](../habits/)' `file_lines`.

**Never:** changes your files; writes anything, even the record.
