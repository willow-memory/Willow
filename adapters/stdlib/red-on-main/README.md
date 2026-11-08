<!-- willow-addon
section: For maintainers
line: A pull request's failing checks held to main's last run: red there too is not the pull request's, green there is.
source: new
added: 2026-11-07
writes: nothing
network: none
role: repo
runs-in: repo
-->
# red-on-main

A pull request goes red, and the failure isn't its own: main is red on the
same check. Without a look at main nobody knows which, so the author chases
main's failure as theirs. This holds each failing check to main's last run.

    python adapters/stdlib/red-on-main/red_on_main.py --pr DIR --main DIR [--main-sha SHA] [--json]

    red-on-main: populated, 2 failing; 1 the pull request's, 1 red on main too
    ## the pull request's
      tests:alone       green on main: this change broke it
    ## red on main too
      tests:adapters-6  red on main at a57574e too: not this change's

`--pr` and `--main` are folders of CI records, each `<DIR>/<any>/record.jsonl` under
them at any depth, as a run's `ci-record-*` artifacts download; a gate's
last verdict in them is the one read. A check red on main too is main's to
fix; green on main, the pull request's; one main's record doesn't hold, or
holds as unreachable, is left to a person, said so.

**In CI:** ci.yml's `red-on-main` job runs it when a pull request's run goes
red, with main's newest push run that kept its records, and writes it into
the run's summary.

It prints a report, as every report add-on does (the report contract, in
the [ci](../ci/) add-on's card), and `--json` gives the same report as one
JSON object. It believes a record only when the kernel reads its chain whole.

Exit codes, the kernel's: 0 nothing failing is the pull request's; 42 one
is, or main's record doesn't say; 2 refused (a bad command line, a folder
with no record, a record whose chain doesn't hold).

**Never:** writes anything or goes online; fetching the records is CI's job.
