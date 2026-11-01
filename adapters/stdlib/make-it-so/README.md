<!-- willow-addon
section: Ways to use it
line: Write down what you want done and the passages it rests on; it checks they still hold, and never does it for you.
source: new
added: 2026-10-30
writes: to
network: none
tags: no-install, offline, writes-output, interface
-->
# make-it-so

Say what you want done and what it rests on. This holds the order for you. It
does not do it.

    python adapters/stdlib/make-it-so/make_it_so.py plan --box DIR --to <PLAN>.json --cmd "COMMAND" [--limit N] "what the order rests on"
    python adapters/stdlib/make-it-so/make_it_so.py check --box DIR <PLAN>.json

`plan` asks the box the question as the kernel does, and writes one file: your
words, the COMMAND exactly as you gave it with its SHA-256, and for each passage
that bears on the question its file, line, id and the SHA-256 of the file as it is
now (5 passages unless said, from 1 to 20). It prints the order and stops:

    order: how much sun do tomatoes want
    command (not run): sed -i 's/six/eight/' notes/garden.md
      notes/garden.md:3  Tomatoes want six hours of sun.
    wrote plan.json; nothing was run. The command is yours to run.

The command is a string held for you. It is not run, not parsed and not checked
for anything; nothing here decides whether it is a good idea. Reading the plan and
running the command is your step, and approving it is yours alone.

`check` says whether the order still stands: the command still hashes to what was
written (a plan edited since is refused), and each cited file still holds the bytes
it held. It prints `holds`, or a line for each file that `changed:` or is `gone:`,
so a plan made on Monday is not run on Thursday's files by accident.

The plan is written once, readable only by you, never over a file that exists and
never inside the box or its pile; its folder must already exist. A question's words
are looked up in the box's words list when it has one.

**Exit codes:** 0 planned, or the plan holds; 42 no passage holds the question (no
order is written), or the plan no longer holds; 2 refused (a bad command line, not
a box, a plan that exists or won't read).

**Uses:** the kernel's `rank`, `chunks`, `config`, `read_words` and `now`.

**Never:** runs the command, or anything else; writes a seal or approves; writes
the box or its pile; reads the key; changes an original.

**Not done:** acting. An add-on that runs commands and changes files has no
promise to make in today's `writes` vocabulary (nothing, record, to, or a named
file), and the guard cannot see what a program it starts does; that is a
decision for the maintainer, not a quiet extra here.
