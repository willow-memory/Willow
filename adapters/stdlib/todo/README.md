<!-- willow-addon
section: Keeping track
line: TODO, FIXME and "need to" lines across the folder, oldest first.
source: box
added: 2026-10-23
writes: nothing
network: none
-->
# todo

The things you wrote down to do, across your folder, oldest first.

    python adapters/stdlib/todo/todo.py --box DIR

    2021-05-14  memos/2021-05-14_1502.txt:1  Sold Teo's van. ... Need to call Mesa Mutual and take it off the policy.
    undated     README.md:40                 TODO: fix the install step

A line counts when it says TODO, FIXME, "need to", "don't forget" or "remember
to", or is an open checkbox. Each is dated by the kernel's own date for its
passage (the latest date in it, its file's name, or the log heading above it);
undated ones come last. The oldest open item is often the one that matters: a
thing said once and never done doesn't get newer.

**Exit codes:** 0 found some; 42 none; 2 refused.

**Uses:** the kernel's `chunks`, `dates` and `config`.

**Never:** writes anything.
