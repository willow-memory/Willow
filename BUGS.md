# Known bugs

Each one is a test that shows it, marked as expected to fail, so the list
can't hold a bug nobody can show, or lose one nobody fixed. This file is
made from those tests by `python adapters/stdlib/ci/bugs.py write`, and
`test_docs.py` fails if it's out of date. How to add one, and what fixing
one takes, is in [CONTRIBUTING.md](CONTRIBUTING.md).

| Bug | What goes wrong | The test that shows it |
|---|---|---|
| #89 | a line's text past its 500th character is never read | `test_kernel.py::test_every_word_of_a_long_line_is_read` |
