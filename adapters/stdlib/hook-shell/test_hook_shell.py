"""hook-shell: a command split as the shell splits it (quotes, escapes, ANSI-C
strings, variables, substitutions, payloads, wrappers), each spelling of a
command reaching the same words; a rule matched on flags as a set; a dynamic
command word and an unreadable command refused; other tools pass; a bad
command line refused; and nothing run or written."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "hook_shell.py"
spec = importlib.util.spec_from_file_location("hook_shell", SCRIPT)
hs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hs)


def words(text: str) -> list[list[str]]:
    return [c["words"] for c in hs.split(text)]


def hook(command: str, *rules: str, tool: str = "Bash") -> subprocess.CompletedProcess:
    argv = [
        sys.executable,
        str(SCRIPT),
        "run",
        *(x for r in rules for x in ("--deny", r)),
    ]
    call = {"tool_name": tool, "tool_input": {"command": command}}
    return subprocess.run(argv, input=json.dumps(call), capture_output=True, text=True)


@pytest.mark.parametrize("spelling", [
    "rm -rf /tmp/a", 'r""m -rf /tmp/a', "r''m -rf /tmp/a", "\\rm -rf /tmp/a", "/bin/rm -rf /tmp/a",
    "$'\\x72m' -rf /tmp/a", "$'\\162m' -rf /tmp/a", "a=r; b=m; $a$b -rf /tmp/a", 'x=rm; "$x" -rf /tmp/a',
    'c="rm -rf"; $c /tmp/a', "sudo -u root rm -rf /tmp/a", "env -i FOO=1 rm -rf /tmp/a",
    "FOO=1 command rm -rf /tmp/a", "nohup time rm -rf /tmp/a", "bash -c 'rm -rf /tmp/a'",
    "sh -lc \"rm -rf /tmp/a\"", 'eval "rm" -rf /tmp/a', "echo x | xargs -n1 rm -rf /tmp/a",
    "ls; (rm -rf /tmp/a)", "if true; then rm -rf /tmp/a; fi", "true && rm -rf /tmp/a", "true || rm -rf /tmp/a",
    "echo $(rm -rf /tmp/a)", "echo `rm -rf /tmp/a`", 'echo "$(rm -rf /tmp/a)"', "timeout 5 rm -rf /tmp/a",
])  # fmt: skip
def test_every_spelling_of_a_command_is_found_as_the_same_words(spelling):
    found = [w for w in words(spelling) if Path(w[0]).name == "rm"]
    assert (
        found and Path(found[0][0]).name == "rm" and found[0][1:] == ["-rf", "/tmp/a"]
    ), words(spelling)


def test_quotes_hold_words_together_and_comments_end_a_line():
    assert words("echo 'a  b' \"c d\" e\\ f # not this") == [
        ["echo", "a  b", "c d", "e f"]
    ]
    assert words("echo a\\\nb") == [["echo", "ab"]]
    assert words("echo one\necho two") == [["echo", "one"], ["echo", "two"]]


def test_a_variable_is_filled_in_and_a_quoted_one_stays_one_word():
    assert words('x="a b"; echo $x "$x" ${x}c') == [
        ["echo", "a", "b", "a b", "a", "bc"]
    ]
    assert words("x=1 echo $x") == [["echo", "$x"]], (
        "an assignment before a command is only its environment"
    )
    assert words("echo $HOME ${NAME}") == [["echo", "$HOME", "${NAME}"]]


def test_the_commands_inside_a_substitution_or_payload_are_listed_with_where_they_came_from():
    got = hs.split("echo $(id) && bash -c 'ls'")
    assert [(c["via"], c["words"][0]) for c in got] == [
        ("subst", "id"),
        ("top", "echo"),
        ("sh -c", "ls"),
        ("top", "bash"),
    ]
    assert [c["via"] for c in hs.split("eval ls")] == ["eval", "top"]


def test_a_redirection_is_not_a_separator():
    assert words("ls 2>&1 | grep x &> /dev/null") == [
        ["ls", "2>&1"],
        ["grep", "x", "&>", "/dev/null"],
    ]
    assert words("sleep 1 & echo hi") == [["sleep", "1"], ["echo", "hi"]]


def test_a_command_word_only_known_at_run_time_is_dynamic_and_an_argument_is_not():
    dyn = lambda t: [c["dynamic"] for c in hs.split(t)]  # noqa: E731
    assert (
        dyn("$UNSET -rf") == [True]
        and dyn("/bin/r? x") == [True]
        and dyn("$(echo rm) x") == [False, True]
    )
    assert dyn("ls *.txt $UNSET") == [False]


def test_an_unclosed_quote_or_substitution_is_not_readable():
    for bad in ("echo 'x", 'echo "x', "echo `x", "echo $(x", "echo ${x", "echo $'x"):
        with pytest.raises(hs.Unbalanced):
            hs.split(bad)


def test_nesting_too_deep_is_refused_not_followed_forever():
    deep = "echo x"
    for _ in range(8):
        deep = "bash -c " + json.dumps(deep)
    with pytest.raises(hs.Unbalanced):
        hs.split(deep)


def test_a_rule_matches_flags_as_a_set_and_the_other_words_in_order():
    assert hs.matches("rm -rf", ["rm", "-fr", "x"]) and hs.matches(
        "rm -rf", ["rm", "-r", "-f", "x"]
    )
    assert not hs.matches("rm -rf", ["rm", "-r", "x"]) and not hs.matches(
        "rm -rf", ["ls", "-rf"]
    )
    assert hs.matches("git push --force", ["git", "push", "--force", "origin"])
    assert hs.matches(
        "git push --force", ["git", "push", "origin", "--force=1"]
    ) and not hs.matches("git push --force", ["git", "pull", "--force"])
    assert hs.matches("curl", ["/usr/bin/curl", "x"]) and not hs.matches(
        "git push", ["git", "status", "push"]
    )
    assert not hs.matches("rm -r", ["rm", "--", "-r"]), "after -- a word is not a flag"


def test_the_hook_refuses_a_denied_command_in_any_spelling_and_says_which():
    got = hook('x=r; sudo "${x}m" -fr /tmp/a', "rm -rf")
    assert got.returncode == 2
    assert "`rm -fr /tmp/a` matches the rule `rm -rf`" in got.stderr
    assert (
        hook("echo hi && git push origin --force", "git push --force").returncode == 2
    )
    assert (
        hook("echo hi", "rm -rf").returncode == 0
        and hook("rm -r x", "rm -rf").returncode == 0
    )


def test_the_hook_refuses_a_command_word_no_rule_can_judge():
    got = hook("$UNSET -rf /", "rm -rf")
    assert got.returncode == 2 and "only known when it runs" in got.stderr


def test_the_hook_refuses_a_command_it_cannot_read_and_input_it_cannot_read():
    got = hook("echo 'x", "rm -rf")
    assert (
        got.returncode == 2 and "can't be read the way the shell reads it" in got.stderr
    )
    for stdin in ("", "no", "[1]"):
        bad = subprocess.run(
            [sys.executable, str(SCRIPT), "run", "--deny", "rm"],
            input=stdin,
            capture_output=True,
            text=True,
        )
        assert bad.returncode == 2 and "can't read" in bad.stderr


def test_other_tools_and_calls_without_a_command_pass():
    assert hook("rm -rf /", "rm -rf", tool="Write").returncode == 0
    ok = subprocess.run(
        [sys.executable, str(SCRIPT), "run", "--deny", "rm"],
        input='{"tool_name": "Bash", "tool_input": {}}',
        capture_output=True,
        text=True,
    )
    assert ok.returncode == 0


def test_rules_come_from_a_file_with_comments(tmp_path):
    f = tmp_path / "rules.txt"
    f.write_text("# no deleting\nrm -rf\n\ncurl\n")
    argv = [sys.executable, str(SCRIPT), "run", "--rules", str(f)]

    def call(c: str) -> int:
        stdin = json.dumps({"tool_name": "Bash", "tool_input": {"command": c}})
        return subprocess.run(
            argv, input=stdin, capture_output=True, text=True
        ).returncode

    assert call("curl x") == 2 and call("rm -rf x") == 2 and call("ls") == 0


def test_split_prints_where_each_command_came_from_and_marks_the_dynamic():
    got = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "split",
            'x=r; sudo "${x}m" -rf /tmp/a && echo $(id); $Y z',
        ],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "top      rm -rf /tmp/a",
        "subst    id",
        "top      echo '$(id)'",
        "top      '$Y' z   dynamic",
    ]


def test_the_command_is_never_run(tmp_path):
    marker = tmp_path / "ran"
    hook(f"touch {marker}", "rm")
    subprocess.run(
        [sys.executable, str(SCRIPT), "split", f"touch {marker}"],
        capture_output=True,
        text=True,
    )
    assert not marker.exists()


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    for argv in ([], ["split"], ["split", "a", "b"], ["run"], ["run", "--deny", ""], ["run", "stray", "--deny", "rm"],
                 ["run", "--rules", str(tmp_path / "missing")], ["nope"]):  # fmt: skip
        got = subprocess.run(
            [sys.executable, str(SCRIPT), *argv],
            input="",
            capture_output=True,
            text=True,
        )
        assert got.returncode == 2, argv
    assert (
        "hook_shell.py"
        in subprocess.run(
            [sys.executable, str(SCRIPT)], capture_output=True, text=True
        ).stderr
    )
    assert (
        subprocess.run(
            [sys.executable, str(SCRIPT), "split", "echo 'x"],
            capture_output=True,
            text=True,
        ).returncode
        == 2
    )


def test_inside_double_quotes_only_a_few_escapes_are_escapes():
    assert words(r'echo "a\"b" "c\\d" "\$x" "\`" "e\f"') == [
        ["echo", 'a"b', "c\\d", "$x", "`", "e\\f"]
    ]
    assert words('echo "a\\\nb"') == [["echo", "ab"]]


def test_arithmetic_is_one_dynamic_word_and_leaves_the_rest_alone():
    got = hs.split("echo $((1 + 2)) x")
    assert [c["words"] for c in got] == [["echo", "$((1 + 2))", "x"]] and got[0][
        "dynamic"
    ] is False


def test_a_quote_with_an_escape_inside_a_substitution_does_not_end_it_early():
    got = hs.split('echo $(echo "x\\")y") z')
    assert [c["words"] for c in got] == [
        ["echo", 'x")y'],
        ["echo", '$(echo "x\\")y")', "z"],
    ]


def test_a_glob_keeps_the_characters_around_it():
    assert words("ls *.txt a?b [ab]c") == [["ls", "*.txt", "a?b", "[ab]c"]]


def test_a_substitution_may_open_with_a_quote():
    got = hs.split('echo $("rm" -rf /tmp/a)')
    assert got[0]["words"] == ["rm", "-rf", "/tmp/a"] and got[0]["via"] == "subst"
