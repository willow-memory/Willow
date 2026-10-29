"""sbom: an SBOM as a heading and a line for each component with its licence; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "sbom.py"
spec = importlib.util.spec_from_file_location("sbom", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'{"bomFormat":"CycloneDX","specVersion":"1.5","metadata":{"component":{"name":"garden-app","version":"1.0"}},"components":['
    b'{"name":"urllib3","version":"2.0.7","purl":"pkg:pypi/urllib3@2.0.7","licenses":[{"expression":"MIT OR Apache-2.0"}]},'
    b'{"name":"requests","version":"2.31.0","purl":"pkg:pypi/requests@2.31.0","licenses":[{"license":{"id":"Apache-2.0"}}]},'
    b'{"name":"legacy-lib"},{"group":"org.x","name":"Tool","version":"3","licenses":[{"license":{"name":"Custom"}},5]}]}'
)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def mirror_of(
    tmp_path: Path, files: dict[str, bytes]
) -> tuple[subprocess.CompletedProcess, Path]:
    src = tmp_path / "src"
    for rel, data in files.items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_bytes(data)
    out = tmp_path / "out"
    return run("mirror", "--from", str(src), "--to", str(out)), out


def test_a_cyclonedx_bill_is_its_heading_then_components_in_name_order():
    assert mod.convert(SAMPLE) == (
        "sbom: garden-app 1.0 (CycloneDX 1.5)\n"
        "legacy-lib: no licence stated\n"
        "requests 2.31.0: Apache-2.0 (pkg:pypi/requests@2.31.0)\n"
        "org.x/Tool 3: Custom\n"
        "urllib3 2.0.7: MIT OR Apache-2.0 (pkg:pypi/urllib3@2.0.7)\n"
    )


def test_an_spdx_bill_uses_the_concluded_licence_else_the_declared_and_the_purl_reference():
    spdx = (
        b'{"spdxVersion":"SPDX-2.3","name":"app","packages":['
        b'{"name":"b","versionInfo":"2","licenseConcluded":"NOASSERTION","licenseDeclared":"MIT","externalRefs":[{"referenceType":"cpe","referenceLocator":"x"},{"referenceType":"purl","referenceLocator":"pkg:npm/b@2"}]},'
        b'{"name":"a","versionInfo":"1","licenseConcluded":"GPL-3.0","licenseDeclared":"MIT"},'
        b'{"name":"c","licenseConcluded":"NONE","licenseDeclared":"NOASSERTION"},{"versionInfo":"9"}]}'
    )
    assert (
        mod.convert(spdx)
        == "sbom: app (SPDX-2.3)\na 1: GPL-3.0\nb 2: MIT (pkg:npm/b@2)\nc: no licence stated\n"
    )


def test_licences_a_cyclonedx_component_may_state():
    assert (
        mod.cdx_licence(
            [
                {"license": {"id": "MIT", "name": "x"}},
                {"license": {"name": "Own"}},
                {"expression": "A OR B"},
                {},
                3,
            ]
        )
        == "MIT, Own, A OR B"
    )
    assert (
        mod.cdx_licence(None) == ""
        and mod.cdx_licence([]) == ""
        and mod.cdx_licence([{"license": {}}]) == ""
    )


def test_a_component_with_no_version_and_a_bill_with_no_name_still_read():
    doc = b'{"bomFormat":"CycloneDX","specVersion":"1.4","components":[{"name":"x"}]}'
    assert mod.convert(doc) == "sbom: (unnamed) (CycloneDX 1.4)\nx: no licence stated\n"
    nameless = b'{"bomFormat":"CycloneDX","components":[{"name":"x","version":"1"}]}'
    assert (
        mod.convert(nameless) == "sbom: (unnamed) (CycloneDX)\nx 1: no licence stated\n"
    )


def test_json_that_is_not_a_bill_is_not_a_result_and_bad_json_is_an_error():
    for other in (
        b"[]",
        b"{}",
        b'{"bomFormat":"CycloneDX"}',
        b'{"bomFormat":"CycloneDX","components":[]}',
        b'{"bomFormat":"X","components":[{"name":"a"}]}',
        b'{"spdxVersion":"SPDX-2.3","packages":[]}',
        b'{"spdxVersion":2,"packages":[{"name":"a"}]}',
        b'{"bomFormat":"CycloneDX","components":[5,{}]}',
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"{nope")
    except ValueError:
        pass
    else:
        raise AssertionError("bad json")


def test_a_json_file_that_is_no_bill_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"a.json": SAMPLE, "b.json": b'{"other": 1}'})
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"bom/sbom.json": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "bom/sbom.json.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "bom/sbom.json": SAMPLE,
            ".hid/bom/sbom.json": SAMPLE,
            ".bom/sbom.json": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["bom/sbom.json.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"bom/sbom.json": SAMPLE})
    before = (tmp_path / "src" / "bom/sbom.json").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "bom/sbom.json.txt").read_bytes() == (
        out / "bom/sbom.json.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "bom/sbom.json").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(tmp_path, {"good.json": SAMPLE, "bad.json": b"{not json"})
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.json.txt").is_file() and not (out / "bad.json.txt").exists()


def test_a_folder_with_nothing_to_read_waits_on_you(tmp_path):
    got, _ = mirror_of(tmp_path, {"notes.md": b"nothing here\n"})
    assert got.returncode == 42 and "wrote 0 files" in got.stdout


def test_a_mirror_inside_the_folder_or_the_folder_inside_it_is_refused(tmp_path):
    (tmp_path / "src").mkdir()
    for to in (tmp_path / "src" / "m", tmp_path):
        got = run("mirror", "--from", str(tmp_path / "src"), "--to", str(to))
        assert got.returncode == 2 and got.stderr.startswith("refused")
    assert (
        run(
            "mirror", "--from", str(tmp_path / "missing"), "--to", str(tmp_path / "m")
        ).returncode
        == 2
    )


def test_a_bad_command_line_says_how_to_run_it():
    for argv in (
        [],
        ["mirror"],
        ["mirror", "--from", "a"],
        ["nope", "--from", "a", "--to", "b"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "sbom.py" in got.stderr
