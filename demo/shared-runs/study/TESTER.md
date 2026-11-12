# Trying it on a machine of your own

For someone asked to try the shared-runs study on their own computer. It
takes about ten minutes, most of it installing. Nothing here is the
study itself: this is its dry run, on six made-up star systems under
nonsense names, and what it finds is not a result. What it tells us is
whether your machine comes to the same bytes as ours, and whether these
instructions can be followed by someone who wasn't there when they were
written. If a step is unclear, that is a finding: say which.

## What you are running, and what it touches

- **Someone else's code.** Two repositories: willow, and a friend's
  simulation, science_bitch. Read what you like of either first. The
  script that does the work is [runner.py](runner.py); [dry.py](dry.py)
  starts it.
- **It writes one folder**, the one you name, and nowhere else. It reads
  no file of yours and reaches no network once the two repositories and
  NumPy are on your machine.
- **It steps a simulation** for under a minute on four cores.

## The steps

You need Python 3.9 or later and git.

1. Fetch willow, and the simulation at the commit the study names:

       git clone https://github.com/willow-memory/willow
       git clone https://github.com/AllHailSeizure/science_bitch
       git -C science_bitch checkout 2fae2f2c4981db7903dfbd9f094ce35718875800

   If willow's study folder is not on its main branch yet, the person who
   asked you will name the branch.

2. Make a Python of its own for this, with the NumPy the study names. A
   machine with another NumPy is refused, so two machines differ by
   their processor and nothing else:

       python -m venv try-env
       try-env/bin/pip install numpy==2.1.3

   On Windows the two programs are under try-env\Scripts, not try-env/bin.

3. Run it, from the folder that holds both repositories:

       try-env/bin/python willow/demo/shared-runs/study/dry.py --plan willow/demo/shared-runs/study/dry-plan.json --work try-out --repo science_bitch --against willow/demo/shared-runs/study/dry/bytes.json

   That is one line.

## What you should see

Two lines saying where things were written, and then three lines like
these, from the machine that wrote this:

    this machine: intel x86_64 avx512, NumPy 2.1.3
    the power rewritten: 30 of 30 jobs the same bytes as the other machine
    the power as written: 30 of 30 jobs the same bytes as the other machine

The first line is what your machine is. The second is the one the study
needs to be 30 of 30 everywhere. The third may well not be: on one
laptop it was a small part, and that difference is the reason one power
in the simulation is written another way for the study. Either way it
is worth knowing, with the job it names.

## What to send back

Those three lines, and the folder try-out/runs, zipped. It holds, for
each of thirteen pretend machines:

- what your machine says of itself: the processor's model name, its
  kind, the system (Linux, Windows, Darwin), and the Python and NumPy
  versions. Not your name, the machine's name, a path or an address;
- what it did, one line a job, each with a SHA-256 and how long it took;
- the states it kept, as numbers.

Look inside before you send it. If anything in it is more than you want
to share, say so and send only the three lines.
