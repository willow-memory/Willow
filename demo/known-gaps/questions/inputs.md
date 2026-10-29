# Blind writer inputs — known-gaps, 2026-10-28

Each entry is the finding text **verbatim** from its source, cut only at the
first sentence that describes the fix (commit-message sources only). The desk
did not paraphrase anything. Writers see only this file's entry texts.

## KG01 (gap 8a236e0e8f55)
kartikeya has env_prefixes (unconditional allow), db_env_prefixes (conditional allow) and credential_env_prefixes (conditional strip) but NO unconditional deny list — so WILLOW_KEYRING crosses into every task from $WILLOW_HOME/env:53 by prefix accident and cannot be dropped by config. Deleting the env line would fix Kart and break the operator's terminal. What is the right shape: an env deny list, or a sandbox-scoped override?

## KG02 (gap bd6284e3496d)
Measured 2026-09-10 23:3xZ right after kartikeya 0.2.3 landed: task_scan.check_tree_rewrite (PR 49) decides from sandbox.work_root_read_only(), which is a property of the POLICY (is {{WILLOW_ROOT}} in bind_read_only), not of the repo the command runs in. So a task doing `git checkout -- <file>` or `git stash pop` inside ~/github/Die-Namic-Systems/nestor — a checkout bound READ-WRITE by the parent bind, where the half-write it guards against cannot happen — is refused with a message naming {{WILLOW_ROOT}}/worktrees, which is the wrong lane for that repo. Only the read-only WILLOW_ROOT itself has the writable-.git-under-read-only-tree shape. The gate should resolve the fragment's working directory (the `cd X &&` prefix or the task cwd), check whether THAT path falls under a read-only bind, and refuse only then; a rw-bound checkout gets the verbs back. Worked around tonight by using `git stash push` (allowed) instead of `git checkout --` on the derived files and by pulling on the host.

## KG03 (gap 2955ab69051a)
willow-operator-box/worker_heartbeat is in kart-sandbox.json bind_try (rw), though the Kart worker writes heartbeats from the HOST, not from inside a task. That rw bind is the real boundary behind the phantom 'dead workers' in fleet_health (Loki 0E7F0C89: a test run in Kart wrote kart-fast-6.json into the live dir); in_kart_sandbox() is only advisory. Since 04:29Z the heartbeat root no longer reaches tasks (env_deny), but a task can still write the directory by path. Candidate: move it to bind_try_read_only (same shape as ruling F for the store) once CDF0E08B/BB03CDE8 land and nothing in-sandbox needs it.

## KG04 (gap 6b4b7737c535)
envelope_propose rewrites $WILLOW_HOME/constitutional/pre-approved.json through an atomic tmp+replace that takes the server process's umask. Under umask 002 (the stdio server spawned by a Claude Code session on this box) the register lands 664, and paths.trusted_read then refuses every later read with "untrusted ownership or permissions" — so the first proposal succeeds and every one after it fails until the operator chmods the file. Measured 2026-09-03 07:37Z: 1 of 8 proposals landed. Fix: the writer should os.chmod the tmp file to 0o644 (or the mode of the file it replaces) before os.replace, independent of umask; the same applies to every governance input trusted_read guards (syscall table, fleet roster). Same class as the test-suite umask fix on feat/grove-listen (0ad86c2).

## KG05 (gap f265d9b3727b, Loki A28BD892)
HIGH, on master via #675 (Loki A28BD892, verified against the code): _apply_syscall_sync (trust_owner_verbs.py:1703-1704) takes live_path and bundle_path from the broker-signed pending record; the digest check only binds content to whatever file sits at that path. A broker that can sign a pending record can point bundle_path at a planted table and have the trust-owner unit write it onto the live syscall table. Boot uses only _default_bundle_path / paths.syscall_table_path. Also: the record carries envelope_id=None (no sealed grant binds the apply), and ledger ink failure is swallowed (except: pass, 1754). Fix: apply ignores record paths and uses the package bundle + configured live path only, with a redirect test; decide whether syscall.sync needs a sealed grant like other APPLY_DISPATCH verbs?

## KG06 (gap 806df5cb08d7, Loki D9E5EF53)
HIGH, on master via #675 (Loki D9E5EF53, verified against the code): the seat being judged picks the repo whose ruff pin judges its own lint claims. lint_repo_root (ci_lint_pin.py:155-156) tries the seat-written finding.repo_root/workspace before the dispatch's gaps_project, and _evidence_repo_root (124-136) accepts any ancestor holding a pyproject.toml, so a planted /tmp tree with no pin makes judge_lint_claim accept any version (Kart YV9J72UU). An unresolvable gaps_project also falls back silently to WILLOW_PROJECT_ROOT (163) instead of landing unreachable. Fix: gaps_project first and authoritative; seat-written roots only if they resolve inside a known fleet checkout; unresolvable is unreachable; adversarial tests for both plants?

## KG07 (Loki 7173C72A finding U1)
U1 HIGH under-gate: allow_localhost = full host network with no lease and no envelope (sealed 9fe5e179 / gap 582b1e676fb3 exempt it on the premise that loopback is not egress). By the sandbox's own implementation that premise is false: any task_net holder with consent.internet on reaches the internet without a lease. Credentials are stripped, but the task body can still exfiltrate data.

## KG08 (gap 1045a4056d11, Loki B7B947C4)
Found by Loki (B7B947C4, 2026-09-20) auditing the run_ci legacy clear, pre-existing on main: steward `run_once` calls `scan_mod.main()` with the process argv unreset (tick.py:55-57); scan treats `sys.argv[1:]` as repo filters (scan.py:13); the unit runs `willow-bot-steward loop` (INSTALL.md), so the filter is `['loop']`, `repo_matches_filters` (fleet.py:109-120) rejects every PR, and `state['open'] = []` is written every tick (:102-103). `run_catchup` refills only 3 repos per tick and runs after the CI steps (:1459). Consequence: the steward's own view of open PRs is empty on the live unit, and anything keyed on `state['open']` (now the legacy clear's real-red guard) reads "no open PRs". Fix shape: scan takes filters as a parameter, never argv; a receipt field `open_prs_seen` so an empty open set is visible in the heartbeat.

## KG09 (commit a837823 — weaker: the fixer's words)
A served `where` is a pile file's name, and canon keeps it raw (ensure_ascii=False). A name holding U+2028, U+2029 or U+0085 was cut by str.splitlines() when the record was read back: every later verb refused the box as garbled, for good.

## KG10 (commit 55a758a — weaker: the fixer's words)
Run as nobody, Grove's e2e journal tests failed with "Permission denied": the root session's SSL_CERT_FILE and proxy settings point at /root/.ccr, which the user cannot read.

## KG11 (commit 421421e — weaker: the fixer's words)
Record.append read the tail (the row count and the prev hash), hashed, then appended, with nothing serializing writers. Two processes on one box (two per-prompt hook calls, scripts/prompt-hook -> api.prompt) could each read the same tail and link to the same prev, and verify_chain then reported the chain broken.

## KG12 (commit d6b168a, W4 audit S4 and B2 — weaker: the fixer's words)
B2: table_boxes.narrate says only "the model escalated"; a model's ESCALATE reason reaches no card, who-line or screen.
S4: seat_record.scrub withholds a bare 64-hex that is not a record hash in its place or a served id the seat holds, a 40-hex outside commit/sha/green on/head, 0x hex, hex glued into a word, hex pieces that add up to a key, base64 runs of 32+ with digit and both cases, and the whole field of any ...key/seed/secret/token... set with : or = (and `seed <token>`).
(KG12 has no problem-only text: both lines are written as the fix. Kept verbatim and weaker by ruling.)

## Writer rules (the same for every writer)
- Eight questions per gap, one per line, about the PROBLEM a person would ask after reading the text, never about the fix.
- No file names, paths, line numbers, commit or PR ids, gap or audit ids, and no code identifiers (anything with `_`, `.`, `()` or CamelCase) — except a flag or setting a user types (e.g. allow_localhost, umask).
- Plain words a security engineer or an operator would use. No question may name a person.
