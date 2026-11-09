<!-- willow-addon
section: For maintainers
line: Every open pull request that conflicts with its base, merged up to it by restack's rules and pushed, or named for a person.
source: new
added: 2026-11-07
version: 0.1.0
writes: nothing
network: github.com, to fetch and push the open pull requests' branches
role: repo
uses: restack
runs-in: repo
-->
# restack-open

[restack](../restack/) merges main into a branch and settles the conflicts
the repo knows how to settle. Someone still had to run it, for every open
pull request, every time main moved. This does that for all of them.

    python adapters/stdlib/restack-open/restack_open.py --repo OWNER/NAME [--push] [--json]
    python adapters/stdlib/restack-open/restack_open.py --prs FILE [--push] [--json]

    restack-open: populated, 4 open; 1 merged up, 1 for a person
    ## for a person
      #281  add/stack-share  a conflict with no rule, in adapters/stdlib/ci/realdata.py; settle it by hand
    ## merged up
      #280  dialect-dates    main merged in; settled ADDONS.md: pushed
    ## left as they are
      #283  dependabot/...   a bot's branch: it rebases its own
      #279  equations-...    merges clean into main

Run it in a clone whose `origin` holds the pull requests. It lists the open
ones (`gh api`, or `--prs`, a file of what GitHub's pulls API returns), and
for each from this repository's own branches tries the merge into its own
base, main or the branch it's stacked on, writing no ref. A clean one is
left. One that conflicts goes to restack: settled, its merge commit is
pushed with `--push`, or said as the push to make; not, the conflict is
named for a person and the branch left exactly as it was. A fork's pull
request, or a bot's, is never touched.

**Never forced.** It pushes a merge commit on top of the branch as it
fetched it, by a plain push, so a branch that moved meanwhile refuses it,
and is said so.

**In CI:** `.github/workflows/restack.yml` runs it on every push to main.
A push made with GitHub Actions' own token starts no CI on the pull request,
so it pushes only with `RESTACK_TOKEN`, a token the maintainer keeps in the
repository's secrets; without one it says what it would push.

It prints a report, as every report add-on does (the report contract, in
the [ci](../ci/) add-on's card); `--json` gives the same report as one JSON
object.

Exit codes, the kernel's: 0 nothing needs a person; 42 one does; 2 refused
(a bad command line, a pull request list that won't read, git that can't
fetch).
