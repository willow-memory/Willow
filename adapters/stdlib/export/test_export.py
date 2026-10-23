"""export: approved answers and the question log, as Markdown or CSV; only
approvals that prove under your key, and counts, never words."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def subject(row: dict) -> str:
    canon = json.dumps({k: row[k] for k in ("path", "data", "cites", "claim")},
                       sort_keys=True, separators=(",", ":"), ensure_ascii=False)  # fmt: skip
    return "proposal:" + hashlib.sha256(canon.encode()).hexdigest()


def approved(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want six hours of sun.\n")
    b = tmp_path / "box"
    run(
        str(KERNEL),
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    )
    got = json.loads(
        run(
            str(KERNEL), "bite", "--box", str(b), *NOW, "how much sun do tomatoes want"
        ).stdout
    )
    row = {"path": "sun.md", "data": "Six hours.", "cites": [got["served"][0]["id"]],
           "claim": "the garden notes"}  # fmt: skip
    (tmp_path / "r.jsonl").write_text(json.dumps(row) + "\n")
    run(
        str(KERNEL),
        "propose",
        "--box",
        str(b),
        "--file",
        str(tmp_path / "r.jsonl"),
        *NOW,
    )
    run(str(KERNEL), "seal", "--box", str(b), subject(row), *NOW)
    run(str(KERNEL), "bite", "--box", str(b), *NOW, "how much sun do tomatoes want")
    run(str(KERNEL), "bite", "--box", str(b), *NOW, "when does the frost come")
    return b


def test_approved_answers_as_markdown_and_csv(tmp_path):
    b = approved(tmp_path)
    md = run(str(HERE / "export.py"), "--box", str(b)).stdout
    assert (
        "## Six hours." in md
        and "reason: the garden notes" in md
        and "cites: garden.md:1" in md
    )
    rows = list(csv.DictReader(io.StringIO(run(str(HERE / "export.py"), "--box", str(b),
                                                "--format", "csv").stdout)))  # fmt: skip
    assert (
        len(rows) == 1
        and rows[0]["answer"] == "Six hours."
        and rows[0]["cites"] == "garden.md:1"
    )


def test_the_log_counts_and_holds_no_words(tmp_path):
    b = approved(tmp_path)
    md = run(str(HERE / "export.py"), "--box", str(b), "--log").stdout
    assert (
        "| 2026-10-23 | 3 | 1 | 1 | 1 |" in md
    )  # asked, by approval, from files, nothing
    assert "frost" not in md and "tomato" not in md.lower()


def test_a_forged_approval_is_never_exported(tmp_path):
    b = approved(tmp_path)
    import importlib.util

    spec = importlib.util.spec_from_file_location("kernel", KERNEL)
    k = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(k)
    fake = {"path": "x.md", "data": "Forged.", "cites": [], "claim": "nobody"}
    subj = subject(fake)
    (b / "proposals" / f"{subj[9:]}.json").write_text(json.dumps(fake))
    k.append(
        b, "2026-10-23T00:00:00Z", "seal", who="human", subject=subj, proof="0" * 64
    )
    md = run(str(HERE / "export.py"), "--box", str(b)).stdout
    assert "Forged." not in md and "Six hours." in md
