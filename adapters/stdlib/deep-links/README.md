<!-- willow-addon
section: Ways to use it
line: Each answer as a link that opens the file at the line (RFC 5147 lines, browser text fragments).
source: new
added: 2026-10-29
writes: nothing
network: none
tags: no-install, offline, read-only, interface
-->
# deep-links

An answer you can click, not a line number to hunt for.

An answer that says "garden.md, line 3" leaves you to find the file. This gives
a link to click, in the two forms a file can be pointed at.

    python adapters/stdlib/deep-links/deep_links.py --box DIR [--base URL]
    python adapters/stdlib/deep-links/deep_links.py --box DIR [--base URL] "your question"

    Six hours of sun.
      garden.md:3   file:///home/ana/notes/garden.md#line=2,4
                    https://example.org/notes/garden.md#:~:text=Tomatoes%20want%20six%20hours%20of%20sun.

| Link | Form | For |
|---|---|---|
| a file link | the path with an RFC 5147 fragment, `#line=2,4`: lines counted from zero, as that standard counts, so a passage on lines 3 and 4 is `line=2,4` | a viewer that understands plain-text line ranges |
| a web link, with `--base URL` | the address your files are published under, then the path, then a text fragment, `#:~:text=START,END`: the first and last four words of the passage's first line (the whole line if it is eight words or fewer) | a browser that scrolls to and marks the words |

In a text fragment the words are percent-encoded as the standard asks, which
includes the comma, the hyphen and the ampersand. A path with a space is made
safe as a link too.

With no question it is each answer you approved, then a link for every passage
it cites. With a question it is the passages your folder holds for it, ranked
the kernel's way, each with its links; asking this way writes nothing, not even
a record row. An approval is listed only while its proof holds under your key
(the kernel's `sealed`, so the key is read there and nowhere here) and its
proposal file still holds the bytes you approved. A cited passage no longer in
your files has no link and is said. Nothing is opened, served or sent.

Exit codes, the kernel's: 0 links given; 42 nothing to link, or an approval or
citation left out; 2 refused (a record that doesn't verify, a bad command line).

**Uses:** the kernel's `read`, `sealed`, `standing`, `chunks` and `rank`.

**Never:** opens, serves or sends anything, reads the key, or writes anything.
