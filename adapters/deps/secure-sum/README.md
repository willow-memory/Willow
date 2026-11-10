<!-- willow-addon
section: Privacy and safety
line: A total of everyone's counts, by Shamir's secret sharing: the one who asked learns the sum, and no one's own count is in any package.
source: new
added: 2026-11-04
version: 0.1.0
needs: shamirs; MIT
floor: shamirs 2.0.0; the rule names 0.1.0.0 from 2018, and before 2.0.0 shares() takes no modulus, so its shares can't be held to one field that every person in a round uses
writes: record
network: none
role: tools
uses: kart, share
-->
# secure-sum

The total of several people's [kart](../kart/) results, worked out so that
no package anyone holds has one person's own count in it, by
[shamirs](https://pypi.org/project/shamirs/)' secret sharing.

    pip install -r adapters/deps/secure-sum/requirements.txt
    python adapters/deps/secure-sum/secure_sum.py split   --box DIR --id IDFILE --result proposal:<sha256> --among KEY,KEY,... [--threshold T]
    python adapters/deps/secure-sum/secure_sum.py combine --box DIR --id IDFILE --package FILE[,...]
    python adapters/deps/secure-sum/secure_sum.py total   --box DIR --among KEY,KEY,... --package FILE[,...]

Each takes `--now TS` as the kernel does.

**Why.** `kart gather` adds the numbers people send back, so whoever asks
sees each person's numbers before adding them. Secret sharing keeps them
from her: each number is cut into shares that say nothing alone, the shares
are added up by the people who hold them, and only the total can be put
back together.

**A round.** Ines asks Walt, Aurelie and Tamsin the same job. She tells each
the round: the three [share](../../stdlib/share/) keys, in one order, and T,
how many of their sums the total needs (all of them, by default). Then:

1. Each runs the job with kart and seals the numbers it printed, as kart
   has them do (or seals [dp](../dp/)'s noisy ones).
2. `split` cuts each number into one share per person, any T of which make
   it again and any fewer say nothing. Each share is proposed as an answer
   of yours, waiting on your seal. Seal each, and send it with `share send`
   **straight to its person, never through the one who asked**: a share
   she held is one she could put together with others. Yours stays in your
   box. A `split` row records the round, never the numbers.
3. `combine` takes the shares the others sent you, one from each, adds them
   to your own, and proposes the sum: a share of everyone's total, waiting
   on your seal. A share that was forwarded on its way is refused, since
   whoever forwarded it held it. That sum goes to the one who asked.
4. `total`, at the one who asked, takes T or more of the sums, each from
   the person at its place in `--among`, and works out the total, waiting
   on her seal. More than T are checked against each other, so a sum
   someone changed or made wrong is caught, not added.

The round is the job text, the keys in order, T and the number of lines,
hashed: a share or sum given a different round is refused, and one result
is split once, into one round (two cuts of one number say more than one).

**What it keeps from whom.** The one who asks learns the total, and no
one's own number, unless T of the people in the round put the shares she
didn't see together with her. Each person sees one share of every other
person's numbers, which alone is noise. With two people, each works out the
other's number from the total, so a round needs three or more.

**What it can't do.** It doesn't carry the packages: share signs them but
doesn't hide them, so a share passed through anyone is theirs to read, and
which way a file goes is the people's choice. It checks that a share came
straight from its maker, not that the files went no other way. It can't
stop a person sending a share made from a number other than their sealed
result; their seal on each share is theirs to answer for. Anyone who drops
out before sending their shares means a new round: `combine` needs one
share from everyone.

**Exit codes:** 42 shares, a sum or a total proposed, waiting on your seal;
2 refused (no shamirs; a result that isn't a sealed kart result of yours,
split already; a key not in the round, a share forwarded, missing or for
someone else; a sum from someone not at its place, or sums that disagree).

**Uses:** [kart](../kart/) for its results' shape and its door, and
[share](../../stdlib/share/) for identities and packages; the kernel's
`read`, `append`, `sealed`, `subject_of` and its command line for the
proposals.

**Never:** seals anything; reads your key; sends a package; writes but the
record, through the kernel; goes online.
