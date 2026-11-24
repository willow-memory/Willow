<!-- willow-addon
section: Trust and proof
line: Proposes setting aside approved answers that no longer hold, each one gone only when you seal it.
source: bot
added: 2026-11-21
version: 0.1.0
writes: record
network: none
role: tools
looks-for: stale-answers
output: report
-->
# retire

Proposes setting aside approved answers that no longer hold, each one gone only when you seal it.

    python adapters/stdlib/retire/retire.py --box DIR [--json]
    python adapters/stdlib/retire/retire.py --box DIR propose SUBJECT --because WHY [--instead SUBJECT] [--now TS]
    python adapters/stdlib/retire/retire.py --box DIR propose --stale [--now TS]

An approved answer stands for its question for good: the kernel serves it
first whenever the same words come again, and a seal can't be declined
afterwards. When one stops being true, this is how you say so, and the
saying is itself a suggestion you seal.

**Propose.** `propose SUBJECT --because WHY` puts one suggestion at the
kernel's door, under the question "retire proposal:&lt;sha256&gt;": set that
answer aside, and why, and with `--instead` the approved answer that stands
in its place. Nothing is aside yet. It waits on your seal like any other
suggestion, and you can decline it; a no is final, as every no is.

    pass  proposal:9c1e…  waiting on your seal
    to set proposal:0a6fde95fa41… aside, seal it with your key:
        python kernel.py seal --box DIR proposal:9c1e…

`propose --stale` asks [stale-answers](../stale-answers/) which approvals
cite a passage that has changed or gone, and proposes setting each aside,
one suggestion each, so you seal or decline them one at a time. One already
aside, waiting or declined is left, and said.

**Report.** With no verb it prints [a report](../ci/README.md#the-report-contract),
the shape every report add-on shares, and `--json` the same as one JSON
object: the answers you have set aside, each with its row and reason; the
ones proposed and waiting on your seal; and the ones that no longer hold and
that nobody has proposed yet.

    retire: populated, 3 approved; 1 set aside; 1 waiting on your seal; 0 no longer hold
    ## set aside
      proposal:0a6fde95fa41…  at row 14: the county moved the date; instead proposal:77b0c1d2e3f4…
    ## waiting on your seal
      proposal:5d21aa0c9e77…  by proposal:c40e11b2a9d3…: its cited passage is no longer in your folder (sun.md:1)

**What counts.** A retirement sets an answer aside only when its path, its
data and the question it was sealed under all name that answer, it was
sealed after the answer was, and it still stands on the bytes you sealed.
So nothing else you approved can be read as one, and none reaches forward to
an answer approved later. A retirement can be set aside too, which brings
its answer back: the latest seal that stands decides.

**What it doesn't do.** The kernel still serves a set-aside answer for its
own words. The kernel reads only its own rows, and skipping one is the
kernel's to learn, not an add-on's to force. Until then:

- an add-on that reads your approvals asks this one which are aside, with
  `set_aside(box, rows)`: each subject, with the retirement, its row, its
  reason and what stands instead;
- anything that asks through the kernel asks "retire proposal:&lt;sha256&gt;"
  and is served the retirement you sealed, or nothing.

**Looks for:** stale-answers, beside it, for `propose --stale` and the
report's last group. Without it the report says so and the rest works.

**Never:** sets anything aside itself, writes anything but the record
through the kernel, reads the key, or goes online.

**Exit codes:** 0 nothing waits (empty, or only answers already aside); 42 a
retirement waits on your seal, an answer no longer holds, or a suggestion
was just made; 2 refused: not a box, a record that doesn't verify, a subject
that isn't an approved answer still standing, one already aside or already
proposed or declined, or no reason given.
