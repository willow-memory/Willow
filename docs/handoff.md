# Handoff: make-it-so and a possible tribute demo

The make-it-so branch, named next3 after the session's branch (two commits on `main` at
`a4db7a1`). This file is a note for the next session. Delete it before the
branch merges.

## State

- **`adapters/stdlib/make-it-so/`** is built, tested and pushed, and no PR is
  open. `plan` writes an order (the question, the command as given, the
  passages it rests on, each cited file's SHA-256) to one file and runs
  nothing; `check` says whether those files still hold what they held.
  12 tests, mutants 6 of 6, ruff clean, a `COMMANDS` row, FILES.md, CHANGELOG
  and the add-on lists done. Run on all four demo folders (plan, then check).
- **To finish it:** open the PR (REST API, see AGENTS.md), write its number
  at the end of the `make-it-so` CHANGELOG entry, then watch CI. The user has
  said they will let the assistant merge a green PR; ask again for this one.
- **Not built:** an add-on that acts (runs commands, changes files). It has
  no promise in today's `writes` vocabulary (nothing, record, to, a named
  file) and the guard cannot see what a program it launches does, so it needs
  a new `kind`, a new `writes` value and a guard decision. The user chose
  propose-only first. Do not build acting without their decision.

## The tribute idea, and what is established about it

The user read that Patrick Stewart had died and wanted a tribute: a demo
over his life from verified sources, and perhaps a more special make-it-so.

**Update, 2026-10-30, later:** the earlier note was out of date. The user
sent a screenshot of Google's top stories (Yahoo, 4 hours ago; NPR, 6 hours
ago). A search then found the death reported by NPR, ABC News, Variety, The
Hollywood Reporter, Deadline and Fox News (from AP): he died on 28 October
2026 at his home in Los Angeles, aged 86. His family gave the cause as
Alzheimer's disease and Lewy body dementia. The pages themselves could not
be opened from the cloud session, because its network policy denies
npr.org and variety.com, so no page is hashed yet. A demo's freeze has to fetch and
hash them where those hosts are allowed.

- NPR: https://www.npr.org/2026/10/29/1230906945/patrick-stewart-dead
- ABC News: https://abcnews.com/GMA/Culture/star-trek-star-patrick-stewart-dies-86/story?id=137684409
- Variety: https://variety.com/2026/tv/news/patrick-stewart-dead-star-trek-picardx-men-xavier-1236934412/
- The Hollywood Reporter: https://www.hollywoodreporter.com/movies/movie-news/patrick-stewart-dead-star-trek-x-men-1236742932/
- Deadline: https://deadline.com/2026/10/patrick-stewart-dead-1237208580/

The user has not yet said whether the demo goes ahead.

## If a demo goes ahead

Follow "A study, like demo/php2shell" in AGENTS.md: freeze first (source
hashes, questions, hit rule, pass rules in a FROZEN.json held by a test,
committed alone), a dry run with nonsense questions, verdicts as kernel rows
in a box outside the repo with `kernel.py verify`, sources that are not the
repo's kept by address, time and SHA-256 and never their text, and what
failed written down beside what held. Facts about a real person come only
from sources named in the freeze, such as his memoir "Making It So" (2023),
official interviews and reference pages, and every claim is cited.
`make-it-so` could be the demo's "what next" step: an order held beside the
passages it rests on. It must still never run the command.

## Rules that bite

Never approve anything, never read the key, never change `kernel.py` for an
add-on, never loosen a check or add to the accepted list of mutants, never hand-edit
the verdicts in `constitution/declarations.json` or the answers in the reach file. Fetch before you push,
never force-push, merge commits only.
