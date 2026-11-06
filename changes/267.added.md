The mirror contract (`adapters/stdlib/ci/README.md`): a reader whose card
says `output: mirror` writes, beside each mirror file, a hidden map of
where each passage came from in the source
(`MIRROR/.places/<path>.txt.json`: `line N`, `lines N-M`, or a named place
such as `page 2`), which the kernel never reads, so the passages keep only
the file's words. `adapters/stdlib/ci/mirrors.py check` holds a mirror to it,
an off-by-one included; test_contract.py and realdata.py hold each such
reader to it on its sample and the demo people's folders. markdown, latex,
org, rst, asciidoc, code-comments and dotfiles keep it, line for line, a
table's header moved onto its rule placed on both lines. `readme` takes
`output` as a list, and `mirror` only on a reader's card
