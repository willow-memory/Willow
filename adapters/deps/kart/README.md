<!-- willow-addon
section: Ways to use it
line: A job someone sent you, run in a sandbox over your own folder only once you seal it, its result yours to seal before it goes back.
source: new
added: 2026-11-03
version: 0.1.7
needs: kartikeya, and the bwrap program (bubblewrap), run not linked; Apache-2.0, LGPL-2.0-or-later
programs: bwrap
floor: kartikeya 0.0.1
writes: record, to
network: none
role: tools
uses: share
-->
# kart

A job someone sent you, run over your own folder in
[Kartikeya](https://github.com/willow-memory/kartikeya)'s sandbox, only
once you seal it; what it found waits on your seal before it goes anywhere.

    pip install -r adapters/deps/kart/requirements.txt    # and: apt install bubblewrap
    python adapters/deps/kart/kart.py policy --box DIR
    python adapters/deps/kart/kart.py take   --box DIR --package FILE --words "your words"
    python adapters/deps/kart/kart.py write  --box DIR --file JOB --words "your words"
    python adapters/deps/kart/kart.py try    --box DIR --file JOB --to FILE [--timeout SECONDS]
    python adapters/deps/kart/kart.py queue  --box DIR --file JOB --db QUEUE
    python adapters/deps/kart/kart.py work   --box DIR --db QUEUE [--timeout SECONDS]
    python adapters/deps/kart/kart.py status --box DIR --db QUEUE --id ID [--to FILE]
    python adapters/deps/kart/kart.py run    --box DIR --job proposal:<sha256> --to FILE [--shape numbers] [--timeout SECONDS]
    python adapters/deps/kart/kart.py gather --box DIR --package FILE[,...] --words "your words"

`take`, `write`, `try`, `run` and `gather` take `--now TS` as the kernel does.

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

**A job of your own.** `write` puts a job in a file of yours at the same
door, with no package: under your own words, citing nothing, its claim
saying you wrote it and naming its text's SHA-256. It is held to what a
received job is: no network line, sealed by you before it runs, the same
sandbox, and its result waiting on a second seal. A file inside the box,
one that isn't text, an empty one and one over 20,000 characters are
refused. Writing a job runs nothing.

**Trying a job of your own.** `try` runs a job in a file of yours with no
seal: nothing leaves by running it. It gets the same sandbox and the same
refusals as any job, its output is written to FILE on your machine, and the
`ran` row names the job by its text's SHA-256 and says `sealed: false`.
Nothing is proposed, so nothing of it is an answer of yours or can be
shared; whoever reads FILE is yours to decide. A job whose result is to go
to someone is written, sealed and run.

**Jobs of your own, run later.** `queue` puts a job in a queue file, which
is Kartikeya's own SQLite queue: its claim is atomic, so two workers never
run one job twice. `work` runs everything queued, one at a time, each as
`try` runs one (the same sandbox, a `ran` row naming the queued id,
`sealed: false`, nothing proposed), for up to 30 minutes each, and stops
when the queue is empty: nothing is left running. A job a worker died
holding is failed, never run again. `status` prints where one job stands
as a line of JSON and, with `--to`, writes what it printed to FILE. The
queue file holds what jobs printed, so it is refused inside the box or your
folder; a job with a network line is refused when queued, and again when
worked.

**The sandbox is Kartikeya's; the policy is willow's.** Kartikeya runs the
job in bubblewrap, and its own scan refuses commands it reads as harmful
(a socket to somewhere, a secret printed) before any sandbox is built. Its
default policy is for a fleet's own workers and binds far more than a
stranger's job should see, so `run` hands it willow's instead, which
`policy` prints:

- your folder, read-only, and the system's /usr, read-only;
- one scratch folder made for this run and removed after;
- a private /tmp, no home, and no environment variable of yours: its
  programs are found on the system's `/usr/bin:/bin`, not your PATH, and
  its locale is `C`, not your LANG, which would change what `sort` and
  `grep -i` say;
- none of a fleet's settings either: a machine that also runs Kartikeya for
  a fleet has `KART_` and `WILLOW_` variables exported, and one of them
  (`WILLOW_ROOT`) would put that fleet's venv on the job's PATH. Kartikeya
  is handed willow's settings and none of those, but the resource group
  (`KART_CGROUP_PARENT`), which is yours to set up;
- none of Kartikeya's own either: it gives a task where it is installed,
  the Python it runs on and a fleet's sender name, which are paths and a
  name of yours. The job starts again under `env -i` with PATH, LANG and
  HOME alone, the last its own empty folder;
- no network: a job naming Kartikeya's `# allow_net`, `# allow_db` or
  `# allow_localhost` is refused before anything runs, and is not even
  taken.

The box and its key are never in it. `test_kart.py` runs a probe through
`run` itself that tries to read the key, list the box, write your folder,
look up a name and read a planted variable, and holds it to finding none.
`{pile}` and `{scratch}` in a job are its two folders, as mounted.

**What it records.** A `ran` row: the job, how it ended, its exit code, its
output's SHA-256, the sandbox engine, the network mode and what was bound,
and `tools`, the SHA-256 of bash and of each program the job names, as found
on that PATH; never the output. How a failed job ended is kept as Kartikeya's
name for it (`exited 3`, `timeout`) and not the line it adds after, which is
the last thing the job printed. What it printed is written to FILE, new, outside the box
and your folder. A job that ended well is proposed as an answer of yours,
citing nothing, waiting on your seal: it came from your files, so nothing
of it leaves but by your seal and `share send`. Its claim names the tools'
hash, so whoever gets it knows what ran it. A job that failed, or that
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
package, waiting on your seal. **One job, two machines' tools:** busybox's
grep and GNU's read `grep -lic` apart, so results that ran on different
tools are still added, but `gather` says how many sets there were, and so
does the totals' claim; read them before you seal. A job written to POSIX's
flags alone counts alike on both.

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

**Exit codes:** 0 the policy printed, a job tried and ended well, a job
queued, the queue worked, or a status given; 42 a job taken or written, a result or a total
proposed, waiting on your seal, or a job that failed or broke its shape; 2
refused (no Kartikeya or bubblewrap, named; a bubblewrap that can't make a
sandbox on this machine, in its own words, before anything runs or is
recorded; a resource group set up for Kartikeya that can't be readied,
likewise, naming the command to run. A reload of systemd empties the
group's `cgroup.subtree_control`, which `kartikeya setup-cgroup` had
written; `kart` writes that one line back when the group is there, and says
so. It writes no unit and reloads nothing; a job not sealed; one asking for the network; a job file
`write` can't take).

**Uses:** [share](../../stdlib/share/) to read packages; the kernel's
`read`, `append`, `sealed`, `standing`, `config`, `h256` and its command
line for the bite and the proposal.

**Never:** seals anything; reads your key; runs a job someone sent that you
didn't seal; proposes or shares what an unsealed job printed;
gives a job the network, your environment, the box or the key; writes but
FILE, the record through the kernel, and its own scratch.
