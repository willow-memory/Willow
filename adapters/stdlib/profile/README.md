<!-- willow-addon
section: For maintainers
line: Where a question's time goes, function by function, from cProfile, per release.
source: new
added: 2026-10-29
writes: nothing
network: none
tags: no-install, offline, read-only, maintainers
-->
# profile

Where a question's time goes.

The kernel answers a question in two steps: read the folder and cut it into
passages, then rank them. This runs both on your folder under cProfile and
says how long each took and which functions the time went to.

    python adapters/stdlib/profile/question_profile.py --box DIR [--top N] [--repeat N] "your question"

    kernel be6e99a1952d, release v0.1.0
    folder: 2,112 passages from 395 files; the question has 4 words
    read and cut the folder     0.041 s
    rank                        0.230 s
    own time, the 6 biggest
         ncalls    own s  total s  function
           2507    0.179    0.447  kernel.py:441 newest
         436402    0.160    0.217  kernel.py:415 _digits
        1361729    0.138    0.139  ~:0 <built-in method builtins.len>

The first line is what makes two runs comparable across releases: `kernel` is
the start of the SHA-256 of kernel.py, the same hash every record row carries
as its version, and the release is the newest versioned heading in
CHANGELOG.md. Run it on each release's kernel with the same folder and the
same question and the table says where a slowdown came from. `--repeat N` runs
both steps N times and reports the shortest, the fairest on a busy machine;
the function table is from one profiled run. `--top N` is how many functions
it lists (10 unless said).

The functions are the ones with the most *own* time, not counting what they
call; a function in the kernel is shown as its file and line and name, a
built-in as such. The file is named question_profile.py rather than profile.py
because a script called profile shadows the standard library's module of that
name, which cProfile imports.

It asks without asking: nothing is written, not even a record row, and the
question's words are not printed, only how many there are. It profiles the
kernel's reading and ranking, not an add-on's own work, and not the model.

Exit codes, the kernel's: 0 profiled; 2 refused.

**Uses:** the kernel's `chunks`, `rank` and `VERSION`.

**Never:** writes anything, or prints the question.
