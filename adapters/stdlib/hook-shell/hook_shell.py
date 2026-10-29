"""hook_shell.py: a command split the way the shell will split it, before any
rule judges it. Python 3.9+.

    python adapters/stdlib/hook-shell/hook_shell.py split "COMMAND"
    python adapters/stdlib/hook-shell/hook_shell.py run --deny "RULE" [--deny "RULE"...] [--rules FILE]

A rule written against the text of a command is dodged by spelling: `rm`
can be `r""m`, `\\rm`, `/bin/rm`, `$'\\x72m'`, `a=r; b=m; $a$b`, or sit inside
`bash -c '...'`, `eval`, `$(...)` or after `sudo`, `env` and `xargs`. `split`
reads a command the way the shell does and prints each simple command it
would run, words unquoted and variables filled in:

    $ hook_shell.py split 'x=r; sudo "${x}m" -rf /tmp/a && echo $(id)'
    top      rm -rf /tmp/a
    subst    id
    top      echo '$(id)'

The first column says where the command came from: `top` (what was typed),
`subst` (inside $(...) or backticks), or `sh -c` / `eval` (a payload the
shell would run again). A command is listed after the ones inside it. A command word that can't be known before it runs (an
unset variable, a glob, `$(...)`) is marked `dynamic`.

`run` is a PreToolUse hook for Bash. It reads the call on standard input,
splits the command, and refuses it (exit 2) when any command it would run
matches a deny rule, or when a command word is dynamic, since no rule can
judge it. A rule is a command and the words it must hold:

    rm -rf            rm with the flags r and f, in any spelling (-fr, -r -f)
    git push --force  git, push, and the flag --force
    curl              any curl at all

Flags match as a set; words that are not flags must come first in order. A
rule is a command, never a regular expression. `--rules FILE` reads one rule
a line, `#` for comments. Calls to any other tool pass; input that is not a
JSON object is refused.

It splits and judges the text; it never runs it and writes nothing. Exit
codes: 0 allowed (or `split` printed); 2 refused (a bad command line, an
unbalanced quote, a denied command); `run` prints the reason on standard
error.
"""

from __future__ import annotations

import json
import re
import shlex
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

MAX_DEPTH = 5
RESERVED = {
    "if",
    "then",
    "else",
    "elif",
    "fi",
    "do",
    "done",
    "while",
    "until",
    "{",
    "}",
    "!",
    "case",
    "esac",
    "in",
}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "ash", "fish"}
#: wrappers that run another command, and the options of theirs that take a value
WRAPPERS = {
    "env": {"-u", "-C", "-S"}, "sudo": {"-u", "-g", "-h", "-p", "-U", "-C", "-D", "-r", "-t"},
    "doas": {"-u", "-C"}, "command": set(), "builtin": set(), "exec": {"-a"}, "nohup": set(),
    "time": {"-f", "-o"}, "nice": {"-n"}, "timeout": {"-s", "-k"}, "xargs": {"-I", "-n", "-P", "-d", "-L", "-s", "-E", "-a", "-l"},
    "stdbuf": {"-i", "-o", "-e"}, "setsid": set(), "ionice": {"-c", "-n", "-p"},
}  # fmt: skip
ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class Unbalanced(ValueError):
    pass


def ansi_c(body: str) -> str:
    """The text of $'...': escapes decoded as bash decodes them."""
    out, i = [], 0
    simple = {
        "n": "\n",
        "t": "\t",
        "r": "\r",
        "a": "\a",
        "b": "\b",
        "e": "\x1b",
        "E": "\x1b",
        "f": "\f",
        "v": "\v",
        "\\": "\\",
        "'": "'",
        '"': '"',
        "?": "?",
    }
    while i < len(body):
        c = body[i]
        if c != "\\" or i + 1 >= len(body):
            out.append(c)
            i += 1
            continue
        n = body[i + 1]
        if n in simple:
            out.append(simple[n])
            i += 2
        elif n == "x" and re.match(r"[0-9A-Fa-f]{1,2}", body[i + 2 :]):
            h = re.match(r"[0-9A-Fa-f]{1,2}", body[i + 2 :]).group(0)
            out.append(chr(int(h, 16)))
            i += 2 + len(h)
        elif n in "uU" and re.match(r"[0-9A-Fa-f]{1,8}", body[i + 2 :]):
            h = re.match(
                r"[0-9A-Fa-f]{1,%d}" % (4 if n == "u" else 8), body[i + 2 :]
            ).group(0)
            out.append(chr(int(h, 16)))
            i += 2 + len(h)
        elif n in "01234567":
            o = re.match(r"[0-7]{1,3}", body[i + 1 :]).group(0)
            out.append(chr(int(o, 8) % 256))
            i += 1 + len(o)
        else:
            out.append("\\" + n)
            i += 2
    return "".join(out)


class Parser:
    """One pass over a command's text: words, separators, quotes, substitutions."""

    def __init__(
        self, text: str, env: dict[str, str], via: str, depth: int, out: list[dict]
    ):
        self.t, self.env, self.via, self.depth, self.out = text, env, via, depth, out

    def matching(self, i: int, open_: str, close: str) -> int:
        """Index of the close that matches the open just before i."""
        depth, quote = 1, ""
        while i < len(self.t):
            c = self.t[i]
            if quote:
                if c == "\\" and quote == '"':
                    i += 1
                elif c == quote:
                    quote = ""
            elif c in "'\"":
                quote = c
            elif c == "\\":
                i += 1
            elif c == open_:
                depth += 1
            elif c == close:
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        raise Unbalanced(f"no {close} to close {open_}")

    def substitute(self, inner: str) -> None:
        if self.depth >= MAX_DEPTH:
            raise Unbalanced("substitutions nested too deep to read")
        Parser(inner, dict(self.env), "subst", self.depth + 1, self.out).run()

    def run(self) -> None:
        t, i, n = self.t, 0, len(self.t)
        segs: list[tuple[str, bool, bool]] = []  # (text, quoted, splittable)
        dynamic = False
        has_word = False
        words: list[tuple[list[str], bool]] = []

        def end_word():
            nonlocal segs, dynamic, has_word
            if has_word:
                words.append((fields(segs), dynamic))
            segs, dynamic, has_word = [], False, False

        def end_command():
            end_word()
            self.finish(words)
            words.clear()

        while i < n:
            c = t[i]
            if c in " \t":
                end_word()
                i += 1
            elif c == "\n" or c == ";":
                end_command()
                i += 1
            elif c == "&" and (
                (t[i - 1 : i] in ("<", ">") and i) or t[i + 1 : i + 2] == ">"
            ):
                segs.append((c, False, False))  # a redirection, 2>&1 or &>
                has_word = True
                i += 1
            elif c in "&|":
                end_command()
                i += (
                    2
                    if t[i + 1 : i + 2] in (c, ">")
                    and c == "|"
                    or t[i + 1 : i + 2] == c
                    else 1
                )
            elif c in "()":
                end_command()
                i += 1
            elif c == "#" and not has_word:
                while i < n and t[i] != "\n":
                    i += 1
            elif c == "\\":
                if t[i + 1 : i + 2] == "\n":
                    i += 2
                else:
                    segs.append((t[i + 1 : i + 2], True, False))
                    has_word = True
                    i += 2
            elif c == "'":
                j = t.find("'", i + 1)
                if j < 0:
                    raise Unbalanced("a ' is never closed")
                segs.append((t[i + 1 : j], True, False))
                has_word = True
                i = j + 1
            elif c == '"':
                i, text, dyn = self.double(i + 1)
                segs.append((text, True, False))
                dynamic |= dyn
                has_word = True
            elif c == "`":
                j = t.find("`", i + 1)
                if j < 0:
                    raise Unbalanced("a ` is never closed")
                self.substitute(t[i + 1 : j])
                segs.append((t[i : j + 1], False, False))
                dynamic = has_word = True
                i = j + 1
            elif c == "$":
                i, text, dyn, split = self.dollar(i, False)
                segs.append((text, False, split))
                dynamic |= dyn
                has_word = True
            elif c in "*?[":
                segs.append((c, False, False))
                dynamic = has_word = True
                i += 1
            else:
                segs.append((c, False, False))
                has_word = True
                i += 1
        end_command()

    def double(self, i: int) -> tuple[int, str, bool]:
        """Inside "...": (index after the closing quote, its text, dynamic)."""
        t, out, dyn = self.t, [], False
        while i < len(t):
            c = t[i]
            if c == '"':
                return i + 1, "".join(out), dyn
            if c == "\\" and t[i + 1 : i + 2] in ('"', "\\", "$", "`", "\n"):
                if t[i + 1] != "\n":
                    out.append(t[i + 1])
                i += 2
            elif c == "$":
                i, text, d, _ = self.dollar(i, True)
                out.append(text)
                dyn |= d
            elif c == "`":
                j = t.find("`", i + 1)
                if j < 0:
                    raise Unbalanced("a ` is never closed")
                self.substitute(t[i + 1 : j])
                out.append(t[i : j + 1])
                dyn = True
                i = j + 1
            else:
                out.append(c)
                i += 1
        raise Unbalanced('a " is never closed')

    def dollar(self, i: int, quoted: bool) -> tuple[int, str, bool, bool]:
        """At a $: (index after it, its text, dynamic, may split into words)."""
        t = self.t
        nxt = t[i + 1 : i + 2]
        if nxt == "(":
            if t[i + 2 : i + 3] == "(":  # arithmetic
                j = self.matching(i + 2, "(", ")")
                return j + 1, t[i : j + 1], True, False
            j = self.matching(i + 2, "(", ")")
            self.substitute(t[i + 2 : j])
            return j + 1, t[i : j + 1], True, False
        if nxt == "'" and not quoted:
            j = i + 2
            while j < len(t) and t[j] != "'":
                j += 2 if t[j] == "\\" else 1
            if j >= len(t):
                raise Unbalanced("a $' is never closed")
            return j + 1, ansi_c(t[i + 2 : j]), False, False
        if nxt == "{":
            j = self.matching(i + 2, "{", "}")
            name = t[i + 2 : j]
            m = NAME.fullmatch(name)
            if not m:
                return j + 1, t[i : j + 1], True, False
            return self.var(name, j + 1, t[i : j + 1], quoted)
        m = NAME.match(t, i + 1)
        if m:
            return self.var(m.group(0), m.end(), t[i : m.end()], quoted)
        return i + 1, "$", False, False

    def var(self, name: str, end: int, shown: str, quoted: bool):
        if name in self.env:
            return end, self.env[name], False, not quoted
        return end, shown, True, False

    def finish(self, words: list[tuple[list[str], bool]]) -> None:
        """A command's words are complete: assignments, wrappers, payloads."""
        items = [(w, d) for fs, d in words for w in fs]
        k = 0
        while k < len(items) and ASSIGN.match(items[k][0]):
            k += 1
        assigns, items = items[:k], items[k:]
        if not items:
            for a, _ in assigns:
                name, _, val = a.partition("=")
                self.env[name] = val
            return
        self.command([w for w, _ in items], [d for _, d in items])

    def command(self, ws: list[str], dyn: list[bool]) -> None:
        while ws and ws[0] in RESERVED:
            ws, dyn = ws[1:], dyn[1:]
        if not ws:
            return
        while ws:
            name = Path(ws[0]).name
            if name not in WRAPPERS:
                break
            takes, k = WRAPPERS[name], 1
            while k < len(ws):
                w = ws[k]
                if w.startswith("-") and w != "-":
                    k += 2 if w in takes else 1
                elif (name == "env" and ASSIGN.match(w)) or (
                    name == "timeout" and k == 1 and re.match(r"^\d", w)
                ):
                    k += 1
                else:
                    break
            ws, dyn = ws[k:], dyn[k:]
            while ws and ASSIGN.match(ws[0]):
                ws, dyn = ws[1:], dyn[1:]
        if not ws:
            return
        name = Path(ws[0]).name
        if name in SHELLS:
            for k in range(1, len(ws)):
                if (
                    ws[k].startswith("-")
                    and not ws[k].startswith("--")
                    and "c" in ws[k][1:]
                    and k + 1 < len(ws)
                ):
                    self.again(ws[k + 1], "sh -c")
                    break
                if not ws[k].startswith("-"):
                    break
        elif name == "eval" and len(ws) > 1:
            self.again(" ".join(ws[1:]), "eval")
        self.out.append({"via": self.via, "words": ws, "dynamic": bool(dyn[0])})

    def again(self, payload: str, via: str) -> None:
        if self.depth >= MAX_DEPTH:
            raise Unbalanced("payloads nested too deep to read")
        Parser(payload, dict(self.env), via, self.depth + 1, self.out).run()


def fields(segs: list[tuple[str, bool, bool]]) -> list[str]:
    """A word's pieces joined, an unquoted variable's value split on blanks."""
    out, cur, started = [], "", False
    for text, quoted, split in segs:
        if not split:
            cur += text
            started = started or quoted or bool(text)
            continue
        if text[:1].isspace() and started:
            out.append(cur)
            cur, started = "", False
        parts = text.split()
        for p, part in enumerate(parts):
            if p:
                out.append(cur)
                cur = ""
            cur += part
            started = True
        if text[-1:].isspace() and started and parts:
            out.append(cur)
            cur, started = "", False
    if started:
        out.append(cur)
    return out


def split(text: str) -> list[dict]:
    out: list[dict] = []
    Parser(unicodedata.normalize("NFC", text), {}, "top", 0, out).run()
    return out


def rule_parts(rule: str) -> tuple[str, set[str], set[str], list[str]]:
    words = shlex.split(rule)
    if not words:
        raise ValueError("an empty rule")
    shorts, longs, plain = set(), set(), []
    for w in words[1:]:
        if w.startswith("--"):
            longs.add(w)
        elif w.startswith("-") and len(w) > 1:
            shorts |= set(w[1:])
        else:
            plain.append(w)
    return Path(words[0]).name, shorts, longs, plain


def matches(rule: str, words: list[str]) -> bool:
    name, shorts, longs, plain = rule_parts(rule)
    if Path(words[0]).name != name:
        return False
    have_s, have_l, have_p, ended = set(), set(), [], False
    for w in words[1:]:
        if ended or not w.startswith("-") or w == "-":
            have_p.append(w)
        elif w == "--":
            ended = True
        elif w.startswith("--"):
            have_l.add(w.split("=", 1)[0])
        else:
            have_s |= set(w[1:])
    return shorts <= have_s and longs <= have_l and have_p[: len(plain)] == plain


def judge(raw: str, rules: list[str]) -> tuple[int, str]:
    try:
        call = json.loads(raw)
    except ValueError:
        call = None
    if not isinstance(call, dict):
        return (
            2,
            "refused: the hook was sent something it can't read, so it can't say it is safe.",
        )
    if call.get("tool_name") != "Bash":
        return 0, ""
    command = (
        (call.get("tool_input") or {}).get("command")
        if isinstance(call.get("tool_input"), dict)
        else None
    )
    if not isinstance(command, str):
        return 0, ""
    try:
        found = split(command)
    except Unbalanced as e:
        return (
            2,
            f"refused: this command can't be read the way the shell reads it ({e}).",
        )
    for c in found:
        shown = shlex.join(c["words"])
        if c["dynamic"]:
            return (
                2,
                f"refused: `{shown}` has a command word that is only known when it runs, so no rule can judge it.",
            )
        for rule in rules:
            if matches(rule, c["words"]):
                return 2, f"refused: `{shown}` matches the rule `{rule}`."
    return 0, ""


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "split":
        try:
            found = split(argv[1])
        except Unbalanced as e:
            print(f"refused: {e}", file=sys.stderr)
            return kernel.REFUSED
        for c in found:
            print(
                f"{c['via']:<8} {shlex.join(c['words'])}"
                + ("   dynamic" if c["dynamic"] else "")
            )
        return kernel.ALIVE
    if argv[:1] == ["run"]:
        rules, it, rest = [], iter(argv[1:]), []
        for a in it:
            if a == "--deny":
                rules.append(next(it, ""))
            elif a == "--rules":
                f = Path(next(it, ""))
                if not f.is_file():
                    print(f"refused: {f} isn't a file", file=sys.stderr)
                    return kernel.REFUSED
                rules += [
                    x.strip()
                    for x in f.read_text(encoding="utf-8").splitlines()
                    if x.strip() and not x.lstrip().startswith("#")
                ]
            else:
                rest.append(a)
        try:
            for r in rules:
                rule_parts(r)
        except ValueError:
            rest.append("bad rule")
        if rest or not rules:
            print(__doc__.split("\n\n")[1], file=sys.stderr)
            return kernel.REFUSED
        code, why = judge(sys.stdin.read(), rules)
        if why:
            print(why, file=sys.stderr)
        return code
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
