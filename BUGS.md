# Known bugs

Each one is a test that shows it, marked as expected to fail, so the list
can't hold a bug nobody can show, or lose one nobody fixed. This file is
made from those tests by `python adapters/stdlib/ci/bugs.py write`, and
`test_docs.py` fails if it's out of date. How to add one, and what fixing
one takes, is in [CONTRIBUTING.md](CONTRIBUTING.md).

| Bug | What goes wrong | The test that shows it |
|---|---|---|
| #54 | a sealed answer is served for the question its proposal file names, not the one the record's bite names | `test_kernel.py::test_a_sealed_answer_belongs_to_the_question_the_record_says` |
| #54 | a sealed answer is served from its proposal file without checking the file still hashes to the sealed subject | `test_kernel.py::test_a_sealed_answer_is_served_only_while_its_bytes_are_the_ones_sealed` |
| #54 | bite crashes with a traceback when a sealed subject's proposal file is gone | `test_kernel.py::test_a_sealed_proposals_file_gone_never_brings_a_bite_down` |
| #54 | verify passes when a sealed subject's proposal file has changed or gone | `test_kernel.py::test_verify_says_when_a_sealed_proposals_file_no_longer_matches` |
