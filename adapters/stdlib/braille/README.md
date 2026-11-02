<!-- willow-addon
section: Ways to use it
line: Answers as braille-ready files (BRF) for a braille display or embosser.
source: new
added: 2026-10-29
writes: to
network: none
-->
# braille

Your answers on a braille display or an embosser.

A braille-ready file (BRF) is plain ASCII in which each character stands for
one braille cell, laid out in lines and pages. A display or an embosser reads
it directly. This writes one from your approved answers, each with the reason
it was given and the places it cites, or from any text file.

    python adapters/stdlib/braille/braille.py --box DIR --to FILE [--cells N] [--lines N]
    python adapters/stdlib/braille/braille.py --from TEXTFILE --to FILE

    ,six hours of sun4
    ,why3 the garden notes
    ,from3 garden4md3#a

That is uncontracted English braille, grade 1, letter for letter, in North
American Braille ASCII:

| In the text | In the file |
|---|---|
| a capital letter | a comma before it; a word in capitals, two commas before the word |
| a number | a number sign, then the digits as the letters a to j (1 is a, 0 is j) |
| a letter a to j straight after a digit | a semicolon before it |
| a decimal point or a thousands comma inside a number | kept inside the number |
| period, comma, question mark, quotation marks, parentheses | the cells 4, 1, 8, 8 and 0, and a quote-and-angle pair |
| a character the table has no cell for (an accent, another script, a currency sign) | a space, counted and said on standard error |

It is not contracted (grade 2) braille, which is a different and longer table
and best checked by a braille reader; someone who reads grade 2 can read this,
more slowly, but correctly.

Lines are 40 cells (`--cells N`, at least 10) and pages 25 lines (`--lines N`).
Words are cut only if one is longer than a line. Lines end with a carriage
return and a line feed and a page ends with a form feed, as embossers expect,
and each answer, or each paragraph of a text file, starts after a blank line.

An approval is used only while its proof holds under your key (the kernel's
`sealed`, so the key is read there and nowhere here) and its proposal file still
holds the bytes you approved; one that doesn't is left out and said. FILE is
written once, readable only by you, never over a file that exists, and the same
input gives the same bytes. Nothing is sent to a display or an embosser.

Exit codes, the kernel's: 0 written; 42 an approval was left out, or nothing to
write (no approved answer, or an empty file; nothing written); 2 refused (a
record that doesn't verify, a bad command line).

**Uses:** the kernel's `read`, `sealed` and `standing`.

**Never:** reads the key, sends anything to a device, changes the box, or writes anywhere but FILE.
