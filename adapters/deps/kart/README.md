<!-- willow-addon
section: Ways to use it
line: A job someone sent you, run in a sandbox over your own folder only once you seal it, its result yours to seal before it goes back.
source: new
added: 2026-11-03
needs: kartikeya, and the bwrap program (bubblewrap), run not linked; Apache-2.0, LGPL-2.0-or-later
programs: bwrap
floor: kartikeya 0.0.1
writes: record, to
network: none
uses: share
-->
# kart

A job someone sent you, run over your own folder in
[Kartikeya](https://github.com/willow-memory/kartikeya)'s sandbox, only
once you seal it; what it found waits on your seal before it goes anywhere.

    pip install -r adapters/deps/kart/requirements.txt    # and: apt install bubblewrap
    python adapters/deps/kart/kart.py policy --box DIR
    python adapters/deps/kart/kart.py take   --box DIR --package FILE --words "your words"
    python adapters/deps/kart/kart.py run    --box DIR --job proposal:<sha256> --to FILE [--shape numbers] [--timeout SECONDS]
    python adapters/deps/kart/kart.py gather --box DIR --package FILE[,...] --words "your words"

`take`, `run` and `gather` take `--now TS` as the kernel does.

**The computation goes to the folder, never the folder to it.** A job is a
shell task that came to you in a [share](../../stdlib/share/) package:
`grep -rhi johnson {pile} | wc -l`, say. It runs where your files are, and
only what it printed, once you seal it, goes back. That is federated
computing with a person at both doors.

**It never runs because it arrived.** `take` puts a received job, from a
package your record says held, at the kernel's door as a proposal of yours,
under your own words, citing nothing, its claim naming who sent it. Only you
seal it, through the kernel. `run` runs only a job you sealed this way, and
refuses an answer of yours that isn't one.

**The sandbox is Kartikeya's; the policy is willow's.** Kartikeya runs the
job in bubblewrap, and its own scan refuses commands it reads as harmful
(a socket to somewhere, a secret printed) before any sandbox is built. Its
default policy is for a fleet's own workers and binds far more than a
stranger's job should see, so `run` hands it willow's instead, which
`policy` prints:

- your folder, read-only, and the system's /usr, read-only;
- one scratch folder made for this run and removed after;
- a private /tmp, no home, and no environment variable of yours;
- no network: a job naming Kartikeya's `# allow_net`, `# allow_db` or
  `# allow_localhost` is refused before anything runs, and is not even
  taken.

The box and its key are never in it. `test_kart.py` runs a probe through
`run` itself that tries to read the key, list the box, write your folder,
look up a name and read a planted variable, and holds it to finding none.
`{pile}` and `{scratch}` in a job are its two folders, as mounted.

**What it records.** A `ran` row: the job, how it ended, its exit code, its
output's SHA-256, the sandbox engine, the network mode and what was bound,
never the output. What it printed is written to FILE, new, outside the box
and your folder. A job that ended well is proposed as an answer of yours,
citing nothing, waiting on your seal: it came from your files, so nothing
of it leaves but by your seal and `share send`. A job that failed, or that
Kartikeya's scan refused, proposes nothing.

**Only aggregates leave.** `--shape numbers` is yours to set when you run
a job, whatever the job says: its output must be whole numbers, one a line,
at most 100, or nothing is proposed and the `ran` row records that the shape
didn't hold. What it printed stays in FILE, on your machine. A job written
to bring back your files (`cat {pile}/*`), your file names, or a count with
a word beside it proposes nothing. That is federated analytics' rule, kept
by the person whose folder it is.

**Gathering.** `gather` takes the results the people you asked sent back:
each a package that held and that your record received, one kart result of
numbers, naming the job it ran by its text's SHA-256. It refuses results of
different jobs, results whose lines don't line up, and two from one chain
(so a forwarded copy is never counted twice), adds the rest line by line,
and proposes the totals as your answer, citing nothing and naming every
package, waiting on your seal.

**What it can't do.** It can't tell you a job is harmless: the sandbox
holds what it can reach, and your two seals hold what goes in and out. The
output is what your files say through someone else's question, so read it
before you seal it, or hold it to `--shape numbers`; `pii-audit` and
`secrets-audit` are worth a run first on anything else. A count still says
something: that your folder holds a name at all is a fact, and small counts
from one person can be telling.
Resource limits are Kartikeya's (a delegated cgroup if you set one up,
`prlimit` otherwise). And it needs a machine that can make an unprivileged
user namespace, which bubblewrap does; Ubuntu 24.04 keeps that behind
AppArmor unless allowed.

**Exit codes:** 0 the policy printed; 42 a job taken, a result or a total
proposed, waiting on your seal, or a job that failed or broke its shape; 2
refused (no Kartikeya or bubblewrap, named; a bubblewrap that can't make a
sandbox on this machine, in its own words, before anything runs or is
recorded; a job not sealed; one asking for the network).

**Uses:** [share](../../stdlib/share/) to read packages; the kernel's
`read`, `append`, `sealed`, `standing`, `config`, `h256` and its command
line for the bite and the proposal.

**Never:** seals anything; reads your key; runs a job you didn't seal;
gives a job the network, your environment, the box or the key; writes but
FILE, the record through the kernel, and its own scratch.
