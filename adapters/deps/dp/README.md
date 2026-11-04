<!-- willow-addon
section: Privacy and safety
line: A count of yours, noised by OpenDP before you seal and send it, so your one number doesn't say what your folder holds.
source: new
added: 2026-11-04
needs: opendp; MIT
floor: opendp 0.8.0; the rule names its first release, 0.1.0 from 2021, and before 0.8.0 there is no make_laplace over a vector of whole numbers, the one mechanism noise uses
writes: record
network: none
uses: kart, share
-->
# dp

A [kart](../kart/) result of yours, whole numbers a job printed over your
folder, with [OpenDP](https://opendp.org)'s noise added to each before you
seal and send it.

    pip install -r adapters/deps/dp/requirements.txt
    python adapters/deps/dp/dp.py noise --box DIR --result proposal:<sha256> --epsilon E [--per-item N]
    python adapters/deps/dp/dp.py spent --box DIR

`noise` takes `--now TS` as the kernel does.

**Why.** kart's `--shape numbers` lets only counts leave, but a count still
says something: that your folder holds a name at all is a fact, and a small
count from one person can be telling. Differential privacy is the standard
answer: add noise drawn so that any one item of your folder changes what
anyone can learn by at most a bound you choose, epsilon.

**What it does.** `noise` proposes your result's numbers with OpenDP's
discrete Laplace noise added, as a new answer of yours waiting on your seal.
Seal that one, not the first, and send it with [share](../../stdlib/share/);
the true numbers stay in your box. Its claim keeps the result's tools and job
text, so `kart gather` adds noisy results as it adds any others, and the
total's noise is the sum of everyone's.

- `--epsilon` is the spend: smaller is noisier and safer. 1 is a common
  choice; 0.1 is a lot of noise; at most 10 is taken.
- `--per-item` is how far one item of your folder can move each number, as
  the job counts: 1 for a count of lines, more if one line can count twice.
  OpenDP works out the noise's scale from both (per item, times the lines,
  over epsilon) and checks the spend with its own map, not this file.
- Its claim says how far off each number may be: within a stated distance
  of the truth 95 times in 100, OpenDP's figure.

**Once.** A result is noised once: noised again, the copies average back to
the truth, so a second `noise` of the same result is refused. Each spend is a
`noised` row on your record, never the numbers, and `spent` adds them up, by
job, so you can see what you have given away. A new job over the same files
spends again; what is too much is yours to decide.

**What it can't do.** It can't choose epsilon for you, nor know what one
item of your folder is: `--per-item` is your reading of the job, and if
it's wrong the bound is wrong. The noise can make a count negative; that is
kept, since a total of everyone's adds the noise away more truly than one
of counts cut at zero. The discrete Laplace sits behind OpenDP's `contrib`
flag, which `noise` turns on: OpenDP's mark for a part whose proof hasn't
yet been through its own vetting.

**Exit codes:** 0 what was spent printed; 42 the noisy numbers proposed,
waiting on your seal; 2 refused (no OpenDP; not a kart result of yours, not
numbers, declined or noised already; an epsilon out of range).

**Uses:** [kart](../kart/) for its results' shape and its door, which
reads [share](../../stdlib/share/); the kernel's `read`, `append`,
`declined`, `subject_of` and its command line for the proposal.

**Never:** seals anything; reads your key; noises a result twice; writes
but the record, through the kernel; goes online.
