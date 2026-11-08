# Known bugs

Each one is a test that shows it, marked as expected to fail, so the list
can't hold a bug nobody can show, or lose one nobody fixed. This file is
made from those tests by `python adapters/stdlib/ci/bugs.py write`, and
`test_docs.py` fails if it's out of date. How to add one, and what fixing
one takes, is in [CONTRIBUTING.md](CONTRIBUTING.md).

| Bug | What goes wrong | The test that shows it |
|---|---|---|
| #89 | a line's text past its 500th character is never read | `test_kernel.py::test_every_word_of_a_long_line_is_read` |
| #90 | a Grep or recursive Glob over the folder holding the key is allowed | `adapters/stdlib/hook-guard/test_hook_guard.py::test_a_search_of_the_folder_holding_the_key_is_refused` |
| #91 | a command that runs kernel.py seal is allowed, and seal reads the key | `adapters/stdlib/hook-guard/test_hook_guard.py::test_a_command_that_seals_is_refused` |
| #112 | ligatures come through as glyph names, so /f_inancing is never found as financing | `adapters/deps/pdf/test_pdf.py::test_a_ligature_character_is_written_as_its_letters` |
| #112 | ligatures come through as glyph names, so /f_inancing is never found as financing | `adapters/deps/pdf/test_pdf.py::test_a_ligature_is_written_as_its_letters_not_its_glyph_name` |
| #284 | html_text splits a word at an inline tag, so re<span>s</span>t reads as re s t | `test_kernel.py::test_an_inline_tag_inside_a_word_leaves_the_word_whole` |
| #285 | stack adds --json to every step of a report add-on, so predict ask refuses inside a stack | `adapters/stdlib/stack/test_stack.py::test_a_report_add_ons_step_that_prints_no_report_runs_as_written` |
