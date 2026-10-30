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
| #93 | amounts drops a scale word, so $5 billion and $5 million both print as $5 | `adapters/stdlib/amounts/test_amounts.py::test_a_scale_word_is_kept_with_its_sum_or_the_sum_is_refused` |
| #94 | stack counts an add-on's 42 for none found as a flagged step | `adapters/stdlib/stack/test_stack.py::test_a_step_that_found_nothing_is_not_flagged` |
| #95 | a date inside a web address dates the line around it | `test_kernel.py::test_a_date_inside_a_web_address_dates_nothing` |
| #96 | propose exits 0 when every suggestion is refused | `test_kernel.py::test_a_propose_whose_every_suggestion_is_refused_does_not_exit_0` |
| #101 | a sentence opening with a common word, such as If I said, names a speaker | `adapters/stdlib/said/test_said.py::test_a_sentence_opening_with_a_common_word_names_no_speaker` |
| #102 | a GitHub owner/repo the line calls a repo is reported as a missing path | `adapters/stdlib/agents-md-check/test_agents_md_check.py::test_a_name_the_line_calls_a_repo_is_not_a_missing_path` |
| #111 | a page fetched under its default name gets no extension, so the kernel never reads it | `adapters/stdlib/snapshot/test_snapshot.py::test_a_page_fetched_under_its_default_name_is_one_the_kernel_reads` |
| #112 | ligatures come through as glyph names, so /f_inancing is never found as financing | `adapters/deps/pdf/test_pdf.py::test_a_ligature_is_written_as_its_letters_not_its_glyph_name` |
