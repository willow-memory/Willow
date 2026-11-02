<!-- willow-addon
section: Reading more kinds of files
line: Commit messages and diffs as a dated pile: "when did we change the retry limit?"
source: new
added: 2026-10-31
writes: to
network: none
-->
# git-history

Commit messages and diffs as a dated pile, so you can ask when something
changed.

    python adapters/stdlib/git-history/git_history.py \
        mirror --from FOLDER --to MIRROR

    commit 9f8e7d6c5b4a3210fedcba9876543210abcdef12
    date: 2026-10-01
    subject: raise the retry limit

     limit.txt | 2 +-
     1 file changed, 1 insertion(+), 1 deletion(-)

Calls the git program (GPL, called, not linked) for each commit in FOLDER.
Each commit becomes one file in MIRROR named for its hash, with its day,
its subject, its body and its diff. The working tree is not read; only
what git already recorded.

A folder that is not a git history, or that has no commit, is nothing
there. Without the git program it refuses and names the install.

Exit codes, the kernel's: 0 wrote some; 42 nothing there; 2 refused.

**Needs:** the git program (GPL, called, not linked). Everything else is
Python's standard library.

**Uses:** the kernel's exit codes.

**Never:** writes inside FOLDER, links git, or reads the key.
