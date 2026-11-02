<!-- willow-addon
section: Ways to use it
line: An exported page of approved answers with its own search built in, no server of its own, served from any static host.
source: box
added: 2026-10-30
needs: Pagefind, its Python package pagefind and its program pagefind-bin; MIT
floor: pagefind 1.3.0, pagefind-bin 1.3.0; the rule names 1.2.0a4 and 1.2.0a5, the first uploads, both alphas; 1.2.0's index differs from build to build, and the card promises the same bytes, which 1.3.0 is the first to keep (40 builds of the same answers, all alike)
writes: to
network: none
-->
# static-search

Your approved answers as a small website with its own search: a page for
each answer and a search box over them, built by Pagefind into plain files
that any static host serves.

    pip install -r adapters/deps/static-search/requirements.txt
    python adapters/deps/static-search/static_search.py --box DIR --to SITE
    python -m http.server --directory SITE --bind 127.0.0.1

Each approved answer is `<SITE>/answers/<N>.html`: the answer, the reason its
suggestion gave, the passages it cited and where, and the day you approved
it. `<SITE>/index.html` is the search and a list of them all. Only approvals
that prove under your key are written (the kernel's `sealed` and
`standing`), as the export add-on does: a forged one never is, and one whose
proposal file has changed since is left out and said.

**Served, not opened as a file.** The pages load only their own files and
nothing online. But a browser won't run Pagefind's search from a `file://`
address (it refuses the module the search is), so the folder is served: by
any static host as it is, or on this machine by Python's own
`http.server`, bound to 127.0.0.1 as above. In Chromium, a search for
"petrak" over two approved answers returned the one about Mr Petrak, at the
pins and at the floor; opened from `file://` it returned nothing.

**The same bytes.** The same answers give the same site, from the same
Pagefind.

**SITE is new.** It must not be there yet, and its folder must: nothing is
overwritten, and no folder above it is made. Pagefind, a program, writes its
index into `<SITE>/pagefind/`, which the guard can't see; it is run with only
`--site SITE`.

**Without Pagefind** it refuses and names the install: exit 2, never a quiet
skip.

**Uses:** `read`, `sealed`, `standing`, and the kernel's exit codes: 0
written; 42 no approved answer to write, or one left out; 2 refused.

**Never:** writes outside SITE, writes the record, reads the key itself, or
goes online.
