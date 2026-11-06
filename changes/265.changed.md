`sort-ask` asks through openai-compatible's `ask_model`, which takes a
`seed`, rather than a copy of its own: one request to change, as #259's
`--reasoning` had to be put into both. Its seed is still 7, so its answers
are the ones it gave; it now waits up to fifteen minutes, as
openai-compatible does, rather than ten, and sends `OPENAI_API_KEY` when
it's set, to the server on this machine it already only asks
