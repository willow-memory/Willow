<!-- willow-addon
section: Trust and proof
line: Approved answers, and the question log (counts only, never words), as Markdown or CSV.
source: box
added: 2026-10-23
writes: nothing
network: none
tags: no-install, offline, read-only, trust
-->
# export

Your approved answers, or your question log, as Markdown or CSV.

    python adapters/stdlib/export/export.py --box DIR [--format md|csv] [--log]

The approved answers, oldest first, each with the reason its suggestion gave,
the passages it cited and where they were, and when it was approved. Only
approvals that prove under your key are exported (the kernel's `sealed`): a
forged one never is.

With `--log`, one line per day: questions asked, answered by your approval,
answered from your files, and found nothing. Counts only: the record never
held a question's words, so neither can this.

An approval whose proposal file is missing, or no longer the bytes the key
signed, is left out and counted on standard error, never exported as an
approved answer.

**Exit codes:** 0 done; 42 done, but an approval was left out and waits on
you; 2 refused (a record that doesn't verify).

**Uses:** the kernel's `read`, `sealed` and `standing`.

**Never:** writes anything but to standard output.
