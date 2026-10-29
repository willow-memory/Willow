"""instruction-files: for each coding agent the instruction files it would
load for a folder, general first, with size and hash; --at adds the folders
down to it; @imports followed inside the folder only; identical bytes said so;
none found waits on you; a bad command line refused; and nothing written."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "instruction_files.py"
KERNEL = HERE.parents[2] / "kernel.py"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def repo(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        p = tmp_path / "repo" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return tmp_path / "repo"


def section(out: str, agent: str) -> list[str]:
    lines, grab = [], False
    for row in out.splitlines():
        if row and not row.startswith(" "):
            grab = row == agent
        elif grab:
            lines.append(" ".join(row.split()))
    return lines


def sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()[:12]


def test_each_agent_lists_the_files_it_reads_with_size_and_hash(tmp_path):
    r = repo(
        tmp_path,
        {"AGENTS.md": "agents\n", "CLAUDE.md": "claude!\n", "GEMINI.md": "gem\n"},
    )
    got = run("--from", str(r))
    assert got.returncode == 0, got.stderr
    assert section(got.stdout, "claude-code") == [
        f"1 CLAUDE.md 8 B {sha('claude!' + chr(10))}"
    ]
    assert section(got.stdout, "codex-cli") == [
        f"1 AGENTS.md 7 B {sha('agents' + chr(10))}"
    ]
    assert section(got.stdout, "gemini-cli") == [
        f"1 GEMINI.md 4 B {sha('gem' + chr(10))}"
    ]
    assert section(got.stdout, "cline") == ["(none)"]


def test_opencode_takes_agents_md_or_else_claude_md_and_codex_prefers_its_override(
    tmp_path,
):
    r = repo(
        tmp_path, {"CLAUDE.md": "c\n", "AGENTS.override.md": "o\n", "AGENTS.md": "a\n"}
    )
    out = run("--from", str(r)).stdout
    assert [row.split()[1] for row in section(out, "opencode")] == ["AGENTS.md"]
    assert [row.split()[1] for row in section(out, "codex-cli")] == [
        "AGENTS.override.md"
    ]
    (r / "AGENTS.md").unlink()
    (r / "AGENTS.override.md").unlink()
    out = run("--from", str(r)).stdout
    assert [row.split()[1] for row in section(out, "opencode")] == ["CLAUDE.md"]
    assert section(out, "codex-cli") == ["(none)"]


def test_at_adds_each_folder_down_to_it_general_first(tmp_path):
    r = repo(
        tmp_path,
        {
            "AGENTS.md": "top\n",
            "svc/AGENTS.md": "svc\n",
            "svc/api/AGENTS.md": "api\n",
            "other/AGENTS.md": "x\n",
        },
    )
    out = run("--from", str(r), "--at", "svc/api").stdout
    assert [row.split()[1] for row in section(out, "codex-cli")] == [
        "AGENTS.md",
        "svc/AGENTS.md",
        "svc/api/AGENTS.md",
    ]
    assert "other" not in out
    top = run("--from", str(r)).stdout
    assert [row.split()[1] for row in section(top, "codex-cli")] == ["AGENTS.md"]


def test_rule_folders_are_read_for_the_agents_that_use_them(tmp_path):
    r = repo(tmp_path, {
        ".claude/rules/style.md": "s\n", ".cursor/rules/a.mdc": "a\n", ".cursorrules": "legacy\n",
        ".github/copilot-instructions.md": "gh\n", ".github/instructions/py.instructions.md": "py\n",
        ".windsurf/rules/w.md": "w\n", ".windsurfrules": "wr\n", ".clinerules/one.md": "1\n",
    })  # fmt: skip
    out = run("--from", str(r)).stdout
    names = lambda agent: [row.split()[1] for row in section(out, agent)]  # noqa: E731
    assert names("claude-code") == [".claude/rules/style.md"]
    assert names("cursor") == [".cursor/rules/a.mdc", ".cursorrules"]
    assert names("copilot") == [
        ".github/copilot-instructions.md",
        ".github/instructions/py.instructions.md",
    ]
    assert names("windsurf") == [".windsurfrules", ".windsurf/rules/w.md"]
    assert names("cline") == [".clinerules/one.md"]


def test_a_claude_import_is_followed_and_says_so_and_same_bytes_are_noted(tmp_path):
    r = repo(
        tmp_path,
        {
            "CLAUDE.md": "@AGENTS.md\n",
            "AGENTS.md": "see @docs/more.md\n",
            "docs/more.md": "m\n",
        },
    )
    got = run("--from", str(r))
    rows = section(got.stdout, "claude-code")
    assert rows[0].startswith("1 CLAUDE.md")
    assert rows[1].startswith("2 @AGENTS.md (imported)")
    assert rows[2].startswith("3 @docs/more.md (imported)")
    assert "same bytes" not in got.stdout
    (r / "CLAUDE.md").write_text("see @docs/more.md\n")
    assert "same bytes: AGENTS.md, CLAUDE.md" in run("--from", str(r)).stdout


def test_an_import_in_a_code_span_or_block_or_outside_the_folder_or_a_cycle_is_not_followed(
    tmp_path,
):
    text = "`@docs/a.md`\n```\n@docs/a.md\n```\n@../outside.md @CLAUDE.md\n"
    r = repo(tmp_path, {"CLAUDE.md": text, "docs/a.md": "a\n"})
    (tmp_path / "outside.md").write_text("o\n")
    assert len(section(run("--from", str(r)).stdout, "claude-code")) == 1


def test_node_modules_rule_files_are_not_read(tmp_path):
    r = repo(
        tmp_path,
        {".claude/rules/ok.md": "k\n", "node_modules/x/.claude/rules/bad.md": "b\n"},
    )
    assert "node_modules" not in run("--from", str(r)).stdout


def test_no_instruction_file_waits_on_you(tmp_path):
    got = run("--from", str(repo(tmp_path, {"README.md": "x"})))
    assert got.returncode == 42 and "No instruction file would load here." in got.stdout


def test_a_box_is_read_through_its_pile_and_nothing_is_written(tmp_path):
    pile = repo(tmp_path, {"AGENTS.md": "a\n"})
    box = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), "--now", "2026-10-29T00:00:00Z"],
                   check=True, capture_output=True)  # fmt: skip
    before = {p: p.read_bytes() for p in pile.rglob("*") if p.is_file()}
    assert run("--box", str(box)).returncode == 0
    assert before == {p: p.read_bytes() for p in pile.rglob("*") if p.is_file()}


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    r = repo(tmp_path, {"AGENTS.md": "a\n"})
    for argv in ([], ["--from"], ["--from", str(r), "stray"], ["--from", str(r), "--box", str(r)],
                 ["--from", str(r), "--at"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "instruction_files.py" in got.stderr
    for argv in (["--from", str(r / "nope")], ["--from", str(r), "--at", "missing"],
                 ["--from", str(r), "--at", ".."], ["--box", str(tmp_path)]):  # fmt: skip
        assert run(*argv).returncode == 2


def test_sizes_are_shown_in_bytes_kilobytes_and_megabytes(tmp_path):
    r = repo(
        tmp_path,
        {
            "AGENTS.md": "x" * 1023,
            "GEMINI.md": "x" * 2048,
            "CLAUDE.md": "x" * (1 << 20),
        },
    )
    out = run("--from", str(r)).stdout
    assert "1023 B" in out and "2.0 KB" in out and "1.0 MB" in out
    (r / "CLAUDE.md").write_text("x" * ((1 << 20) - 1))
    assert "1024.0 KB" in run("--from", str(r)).stdout
