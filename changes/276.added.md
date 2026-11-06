`ci`'s `adapters/stdlib/ci/copies.py`: the functions add-ons keep their own
copy of, grouped by name, each group's common version and the copies that
drifted from it, as a report (`survey`), as unified diffs (`diff NAME`), and,
for a pull request, the drift it adds without saying why (`new --base REF`),
which CI's `copies` job writes to the run's summary, a suggestion and never a
gate. A copy that differs on purpose says why in a comment above its def;
sort-ask's `kernel_says`, which alone of four captures stderr so a refusal's
reason reaches its report, is the first. On main it finds 7 functions with a
drifted copy, 58 copies in all
