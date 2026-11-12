# Marisol's island

A fictional teacher's folder, built so each kind of file meets the add-on that
reads it, and so a grant draft with six claims in it can be checked against her
own folder and the real sources. It is a **character and a folder, not yet a
study**: nothing here has been frozen, no question has been asked of it in a
frozen run, and no result is claimed.

- [CHARACTER.md](CHARACTER.md): who she is and how her work writes itself down.
- [PLANTED.md](PLANTED.md): the answer key, written before the generator.
- `python3 demo/marisol/make_life.py` writes `life/` and `names.txt`, the same
  bytes every run; `--check` holds the written files to PLANTED.md.
- [sources.json](sources.json) keeps the real sources by address, time and
  SHA-256, never their text; `python3 demo/marisol/sources.py fetch DIR` gets
  them again and `check DIR` compares hashes offline. One source (a NBC New York
  page) could not be fetched and no claim depends on it.

The real facts are Section 936's phase-out (the 1996 Act scheduled its repeal
for 2005), Hurricane Maria on 2017-09-20, LUMA taking over the grid on
Tuesday, June 1, 2021 (the NBC page is dated June 2), and NSF award 2305699
("NSF Engines - Type 1", 05/15/2023 to 04/30/2025, $999,903). Every other
person, place and number is invented and marked so.

## What a first trial found (not a result)

Run once, by hand, against a pile of the folder and the saved sources:
claim-check finds the draft itself first for each claim, so a run must leave
`grants/` out of the evidence; the NBC page supports "June 2021" only through
its dateline; claim C6, written in English, does not find her Spanish log ("76 days" is not "76 días"), while the same claim in Spanish does: the cross-language gap a sentence-pair add-on would close; and on the first trial the log, with no blank lines, was served
in 500-character runs, so each entry now has its own passage.

## Before anything is claimed

1. A Puerto Rican reader reads the Spanish for what rings false. A model wrote it.
2. The sources' hashes and the PROMESA signing date are confirmed.
3. The study is frozen as the repo's other studies are: sources, questions, hit
   rule and pass rules in one commit, a dry run with nonsense questions first.
