# demo/redteam — a recon composition, frozen

Willow's add-ons each do one small, read-only thing. This demo puts seven of
them together into a single authorized-recon pass over a target with known,
planted weaknesses, and freezes the result so anyone can rerun it and get the
same pass. It is the worked example behind one idea: **a pull request should
not only add an add-on, it should show the add-on working alongside the
others, over a real target, and check whether that combination has been
assembled before.** The second half of that — the novelty check — is a
reusable tool, [novelty.py](../novelty.py), that every demo can run.

Nothing here reaches the network, writes to the target, or exploits anything.
Every add-on in the pass promises `writes: nothing` and `network: none`, so
the whole pass does too. It reads and reports; a person decides what to do.

## The target

`target/` is a small application planted with one weakness per category a
recon pass looks for. It is fixture code, committed and frozen:

- `target/app` — six source files across Python, PHP, JavaScript and Go, each
  holding idiomatic sinks: a shell command built from a request parameter, an
  `unserialize` of post data, a string-formatted SQL query, TLS verification
  turned off, an `eval` of user input, debug left on, a wildcard CORS header,
  and credentials in the clear (a database password, an AWS key, a JWT, a
  connection string).
- `target/package-lock.json`, `target/requirements.txt` — a dependency set
  with a vulnerable `lodash` and `requests`, a misspelled `reqeusts`, an
  abandoned `minimist`, and an unpinned `flask>=2.0`.
- `target/node_modules/evil-pkg/package.json` — a package whose `postinstall`
  script pipes a remote script into a shell.

The intel the pass needs is committed too, under `intel/`: an OSV/GHSA tree,
registry metadata, and a popular-names list. With them frozen and `now` fixed
at 2026-10-25, the pass reads identically every run.

## The pass

[recon.py](recon.py) runs, in an attacker's order of interest:

| # | add-on | what it surfaces on this target |
|---|--------|---------------------------------|
| 1 | `secrets-audit` | the hardcoded AWS key, by file and line, value never shown |
| 2 | `advisories` | `requests 2.19.1` (CVE-2018-18074), `lodash 4.17.4` (CVE-2021-23337) |
| 3a | `install-scripts` | `evil-pkg`'s `postinstall` that would run on install |
| 3b | `typosquat` | `reqeusts`, one edit from the popular `requests` |
| 3c | `pins` | `flask>=2.0`, a range no lockfile pins |
| 4 | `outdated` | `minimist`, last released 2021-04-01, abandoned |
| 5 | `risky-code` | every sink above, grouped by class, cited by file and line |

Run it:

    python demo/redteam/recon.py

`secrets-audit` deliberately flags only the high-confidence secret (the AWS
key) and never prints a value; the other plaintext credentials in the target
are there to show it does **not** chase or echo every string. `risky-code`
(the add-on this study ships alongside) carries the line-level breadth across
all six source files.

## Frozen, and how to check it

[FROZEN.json](FROZEN.json) is the pre-registration. It records the SHA-256 of
every source — the target, the intel, and the pipeline — the finding expected
from each section, and the pass rule. It was committed before the pass was
read. [test_redteam.py](test_redteam.py) holds it: it asserts every source
still hashes to its frozen value (so the target and pipeline cannot drift
without the test failing), runs the pass and checks each planted weakness
surfaces, asserts no secret's value is ever printed, and runs the novelty
check below.

## Novelty — the reusable part

[novelty.py](../novelty.py) asks willow's own search whether this combination
of pieces has been put together before, the same way a new idea is vetted:

    python demo/novelty.py "red team recon composing risky-code advisories outdated secrets typosquat install-scripts pins over a planted-weakness target" --as redteam

Two offline checks: `similar` over the idea pile, and the kernel's own `rank`
over every demo's README. The kernel serves a demo only when it holds half
the description's content words — the same promise that it never answers what
a folder does not have — so serving nothing, with nothing close on the pile,
means the pieces have not been assembled before. BM25 names the nearest demo
(here, `php2shell`, a fix-localization study, not a recon one) as a pointer to
read, never a verdict. The pass rule in FROZEN.json requires this check to
report the composition as novel.

This demo ships its own README, which of course holds its own description, so
the check is run with `--as redteam` to leave that README out: the honest
question is whether any *other* demo, or the idea pile, already assembled
these pieces. That is the discipline the idea is really about — a pull request
runs the check before its demo is in the tree, to see whether the combination
is genuinely new.

## What held, and what did not

Every section surfaced its planted weakness, and no secret value was printed —
both frozen and checked by the test. The one deliberate narrow spot:
`secrets-audit` flags one of four planted credentials, by design; the breadth
of code findings comes from `risky-code`, not from it. The composition scans
as novel against the idea pile and every existing demo.
