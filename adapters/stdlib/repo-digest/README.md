<!-- willow-addon
section: For maintainers
line: One page of what this repo needs from you: files nothing declares, a ring in what add-ons use, ideas waiting, and the order they build in.
source: new
added: 2026-11-11
version: 0.1.0
writes: nothing
network: none
role: repo
uses: kinds
output: report
runs-in: repo
-->
# repo-digest

One page of what this repo needs from you, and the order its add-ons build in.

    python adapters/stdlib/repo-digest/repo_digest.py page [--json] [--root DIR]

    repo-digest: populated, 219 files nothing declares, 1 ring in what uses what, 190 ideas waiting; 363 add-ons build 6 steps deep
    ## a ring in what uses what: one of the two uses lines is wrong
      readme → similar → readme  each needs the other beside it; 6 add-ons rest on it: against, ci, ci-memo, github, ready, test-impact
    ## nothing declares: a declaration, where its subject lives
      docs/                      20 files, such as docs/agents/add-ons.md
      ports/                     13 files, such as ports/csharp/Kernel.cs
    ## ideas waiting: to build, or to leave
      Trust and proof            25 ideas, such as before-copy
    ## entries waiting: for the next release
      the changelog              115 entries not yet in a release
    ## the order they build in
      on the kernel alone        247 add-ons
      1 step up                  69 add-ons: almanac-keep, apple-mail, and 67 more
      6 steps up                 2 add-ons: pile-serve, pile-sweep
      the longest way down       pile-serve → pile-rungs → pile-rank → pile-store → index-cache → scan → todo
    ## most built on
      habits                     20 add-ons use it

**Why.** Every tool here can say "I don't know", and each says it in its
own place: a file with no kind, an idea not built, an add-on that needs one
that isn't there. A person's folder has [digest](../digest/), one page of
what it needs from them. The repo had none for itself, so each of these was
found by whoever happened to run the tool that knew. This is that page.

**What waits, and where it goes.** Each group's heading says both.

| group | what it is | where it goes |
|---|---|---|
| a ring in what uses what | add-ons whose cards each name the other in `uses`, with the add-ons that rest on the ring | one of the two lines is wrong: a ring has no order to build in |
| uses one that isn't here | a `uses` line naming no built add-on | build it, or take the name off |
| nothing declares | files with no kind, by folder, as [kinds](../kinds/) counts them | a declaration, where the file's subject lives |
| ideas waiting | the ideas list, by section | to build, or to leave: an idea is a seed, not a fault |
| entries waiting | changelog entries not yet in a release | the next release folds them in |

**How the add-ons bridge, and in what order.** A card's `uses` line names
the add-ons it needs beside it. One with no such line rests on the kernel
alone. One that uses those is one step up, and so on: an add-on's step is
one more than the highest it uses. That is the order they have to be there
in, since nothing runs before what it uses. The page says how many add-ons
are at each step, the longest way down from any one, and the five most
built on.

An add-on in a ring, or resting on one, has no step: it is named with the
ring and left out of the order.

**What it does not see.** Only `uses` is read. A step of a stack that takes
an earlier step's output is a bridge too, made when the stack is written,
and no card says it. `looks-for`, which names an add-on used only when it
is there, is not a need and is not counted.

`--root DIR` reads another checkout. `--json` prints
[the report](../ci/README.md#the-report-contract) as one JSON object.

It reads the cards' headers, the ideas list, towncrier.toml and the names of
the files git knows. It writes nothing.

**Exit codes**, the kernel's: 0 nothing that is wrong waits (ideas and
entries waiting are how a repo stands); 42 a ring, a `uses` that leads
nowhere or a file nothing declares, or git couldn't list the files; 2
refused.

**Needs:** the git program (GPL, called, not linked), through kinds.

**Uses:** the kernel's exit codes; the kinds add-on's `census`, `tracked`
and `folder_of`.

**Never:** writes anything, reads the key, or goes online.
