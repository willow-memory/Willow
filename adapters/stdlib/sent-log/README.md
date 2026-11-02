<!-- willow-addon
section: Privacy and safety
line: Which of your passages went to which online model, read from the record by model card: what left this machine and where to.
source: new
added: 2026-11-01
writes: nothing
network: none
-->
# sent-log

Which of your passages went to which model, and where to, read from the record.

    python adapters/stdlib/sent-log/sent_log.py --box DIR

    row 4  2026-10-23T00:00:00Z  proposal:eb63d0addbe2…
           gemma-3-4b-it at http://127.0.0.1:8080/v1 (this machine)
           went: garden.md:1 63d9b600aca4
    1 proposal(s) on the record; 0 bite(s) served passages and were proposed on by no one, which this cannot see past; 0 refused proposal(s) name nothing

**There is no model card on the record yet.** The idea says "by model card",
but [model-card](../../planned.json) is not built, and nothing the kernel
writes names a model: a `proposal` row holds its subject, verdict and the bite
it answered, and its `who` is the kernel's, whoever made the suggestion. So
this reads the one place a model is named, the proposal's `claim`. For
[openai-compatible](../openai-compatible/) that is "MODEL at URL answered from
N of the M passages served". It is read from the proposal file only when that
file is the bytes the subject hashes (otherwise it's `broken`, not read), and
the passages are the ones the proposal's bite served, minus any marked echo,
which that add-on never sends. `went` is said only when the claim's M equals
that count; otherwise the passages are `served, may have gone`. A loopback
address is `this machine`; any other host is `online: HOST`.

**What it cannot tell**, and prints rather than hides:

- The claim is the proposer's own words, not an attested card. A person's own
  suggestion, or another assistant's with a different claim, shows as
  `model not named` with the claim quoted.
- An ask whose reply cited nothing, or whose endpoint failed, leaves a bite
  and no proposal, though the passages may already have left. Those bites are
  counted ("proposed on by no one"). So the list is a floor, never a clean bill.
- A refused proposal keeps no claim, so it names nothing.

When `model-card` lands and puts a card's hash on each suggestion, this is the
add-on to read it.

**Exit codes**, the kernel's: 0 every proposal names its model and endpoint
(or there are none); 42 one is unnamed or its file is missing or not what was
proposed; 2 refused (a bad command line, a record that doesn't verify).

**Uses:** the kernel's `read`, `subject_of`.

**Never:** writes anything, reads the key, seals, or goes online.
