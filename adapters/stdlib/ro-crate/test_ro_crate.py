"""ro-crate: a box as an RO-Crate zip: the description naming every file with
its SHA-256, size, kind and licence, the record's tip pinned, the key and the
box's settings left out, hidden files left out, checked before it is kept, the
same bytes twice, never over a file, and refusals; nothing in the box changed."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "ro_crate.py"
KERNEL = HERE.parents[2] / "kernel.py"
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

NOW = ["--now", "2026-10-29T10:00:00Z"]
ZIP = "willow-crate-20261029-100000.zip"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def box(tmp_path: Path, seal: bool = False) -> Path:
    pile = tmp_path / "pile"
    (pile / "notes").mkdir(parents=True)
    (pile / "garden.md").write_text("Tomatoes want six hours of sun.\n")
    (pile / "notes" / "my diary.txt").write_text("Dear diary\n")
    (pile / "scan.pdf").write_bytes(b"%PDF-\0\1\2")
    (pile / ".secret").mkdir()
    (pile / ".secret" / "x.txt").write_text("hidden\n")
    b = tmp_path / "box"
    subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "init",
            "--box",
            str(b),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "keys" / "k"),
            "--now",
            "2026-10-24T00:00:00Z",
        ],
        check=True,
        capture_output=True,
    )
    return b


def crate(
    tmp_path: Path, *extra: str
) -> tuple[subprocess.CompletedProcess, zipfile.ZipFile | None, dict]:
    got = run(
        "--box",
        str(box(tmp_path))
        if not (tmp_path / "box").exists()
        else str(tmp_path / "box"),
        "--to",
        str(tmp_path / "out"),
        *NOW,
        *extra,
    )
    z = (
        zipfile.ZipFile(tmp_path / "out" / ZIP)
        if (tmp_path / "out" / ZIP).exists()
        else None
    )
    return got, z, json.loads(z.read("ro-crate-metadata.json")) if z else {}


def entities(meta: dict) -> dict[str, dict]:
    return {e["@id"]: e for e in meta["@graph"]}


def test_every_file_is_described_with_its_hash_size_kind_and_licence(tmp_path):
    got, z, meta = crate(tmp_path, "--licence", "CC-BY-4.0")
    assert got.returncode == 0, got.stderr
    ents = entities(meta)
    garden = ents["files/garden.md"]
    assert (
        garden["@type"] == "File"
        and garden["name"] == "garden.md"
        and garden["contentSize"] == "32"
    )
    assert (
        garden["sha256"]
        == hashlib.sha256(b"Tomatoes want six hours of sun.\n").hexdigest()
    )
    assert garden["encodingFormat"] == "text/markdown" and garden["license"] == {
        "@id": "https://spdx.org/licenses/CC-BY-4.0.html"
    }
    assert ents["files/scan.pdf"]["encodingFormat"] == "application/pdf"
    assert ents["record.jsonl"]["encodingFormat"] == "application/x-ndjson"
    assert ents["https://spdx.org/licenses/CC-BY-4.0.html"] == {
        "@id": "https://spdx.org/licenses/CC-BY-4.0.html",
        "@type": "CreativeWork",
        "name": "CC-BY-4.0",
    }
    assert (
        f"wrote {tmp_path / 'out' / ZIP}: 4 files, 1 rows; licence: CC-BY-4.0"
        in got.stdout
    )


def test_the_root_is_a_dataset_that_lists_its_parts_and_pins_the_record(tmp_path):
    got, z, meta = crate(tmp_path, "--licence", "CC0-1.0")
    ents = entities(meta)
    descriptor, root = ents["ro-crate-metadata.json"], ents["./"]
    assert descriptor["conformsTo"] == {
        "@id": "https://w3id.org/ro/crate/1.1"
    } and descriptor["about"] == {"@id": "./"}
    assert meta["@context"] == "https://w3id.org/ro/crate/1.1/context"
    assert (
        root["@type"] == "Dataset"
        and root["datePublished"] == "2026-10-29"
        and root["license"] == {"@id": "https://spdx.org/licenses/CC0-1.0.html"}
    )
    assert sorted(p["@id"] for p in root["hasPart"]) == [
        "files/garden.md",
        "files/notes/my%20diary.txt",
        "files/scan.pdf",
        "record.jsonl",
    ]
    rows, _ = kernel.read(tmp_path / "box" / "record.jsonl")
    props = {p["name"]: p["value"] for p in root["additionalProperty"]}
    assert props == {"record rows": 1, "record tip": rows[-1]["hash"]}


def test_a_name_with_a_space_is_a_link_in_the_description_and_a_name_in_the_zip(
    tmp_path,
):
    _, z, meta = crate(tmp_path)
    assert (
        "files/notes/my diary.txt" in z.namelist()
        and "files/notes/my%20diary.txt" in entities(meta)
    )


def test_no_licence_is_none_given_said_and_never_guessed(tmp_path):
    got, z, meta = crate(tmp_path)
    assert (
        got.returncode == 0
        and "licence: none given" in got.stdout
        and "no --licence given" in got.stderr
    )
    assert all("license" not in e for e in meta["@graph"])


def test_a_licence_given_as_a_link_is_used_as_it_is(tmp_path):
    _, _, meta = crate(tmp_path, "--licence", "https://example.org/terms")
    assert entities(meta)["./"]["license"] == {"@id": "https://example.org/terms"}


def test_the_key_the_boxs_settings_and_hidden_files_are_not_in_it(tmp_path):
    _, z, meta = crate(tmp_path)
    names = z.namelist()
    assert "kernel.json" not in names and not any(
        "k" == n.rsplit("/")[-1] for n in names
    )
    assert not any(
        ".secret" in n or "hidden" in z.read(n).decode("latin-1") for n in names
    )
    assert not any(str(tmp_path / "keys") in z.read(n).decode("latin-1") for n in names)


def test_suggestions_and_approved_answers_are_in_it(tmp_path):
    b = box(tmp_path)
    served = json.loads(
        subprocess.run(
            [
                sys.executable,
                str(KERNEL),
                "bite",
                "--box",
                str(b),
                "--now",
                "2026-10-24T00:00:00Z",
                "how much sun do tomatoes want",
            ],
            capture_output=True,
            text=True,
        ).stdout
    )["served"]
    row = {
        "path": "sun.md",
        "data": "Six hours.",
        "cites": [served[0]["id"]],
        "claim": "the garden notes",
    }
    (tmp_path / "r.jsonl").write_text(json.dumps(row) + "\n")
    subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "propose",
            "--box",
            str(b),
            "--file",
            str(tmp_path / "r.jsonl"),
            "--now",
            "2026-10-24T00:00:00Z",
        ],
        capture_output=True,
    )
    subj = (
        "proposal:"
        + hashlib.sha256(
            json.dumps(
                {x: row[x] for x in ("path", "data", "cites", "claim")},
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode()
        ).hexdigest()
    )
    subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "seal",
            "--box",
            str(b),
            subj,
            "--now",
            "2026-10-24T00:00:00Z",
        ],
        capture_output=True,
    )
    _, z, meta = crate(tmp_path)
    assert (
        "written/sun.md" in z.namelist()
        and f"proposals/{subj[9:]}.json" in z.namelist()
    )
    assert (
        entities(meta)["written/sun.md"]["sha256"]
        == hashlib.sha256(b"Six hours.").hexdigest()
    )


def test_the_same_box_and_time_give_the_same_bytes(tmp_path):
    crate(tmp_path)
    first = (tmp_path / "out" / ZIP).read_bytes()
    (tmp_path / "out" / ZIP).unlink()
    run("--box", str(tmp_path / "box"), "--to", str(tmp_path / "out"), *NOW)
    assert (tmp_path / "out" / ZIP).read_bytes() == first


def test_a_crate_is_never_written_over_another(tmp_path):
    crate(tmp_path)
    again = run("--box", str(tmp_path / "box"), "--to", str(tmp_path / "out"), *NOW)
    assert again.returncode == 2 and "already there" in again.stderr


def test_a_folder_inside_the_box_or_the_files_or_the_keys_is_refused(tmp_path):
    b = box(tmp_path)
    (tmp_path / "keys").mkdir(exist_ok=True)
    for bad in (
        b / "out",
        tmp_path / "pile" / "out",
        tmp_path / "keys",
        b,
        tmp_path / "pile",
    ):
        got = run("--box", str(b), "--to", str(bad), *NOW)
        assert got.returncode == 2 and "refused:" in got.stderr, bad
    assert not (b / "out").exists() and not (tmp_path / "pile" / "out").exists()


def test_a_record_that_does_not_verify_is_refused_and_nothing_written(tmp_path):
    b = box(tmp_path)
    rec = b / "record.jsonl"
    rec.write_text(rec.read_text().replace("2026", "2025", 1))
    got = run("--box", str(b), "--to", str(tmp_path / "out"), *NOW)
    assert got.returncode == 2 and not (tmp_path / "out").exists()


def test_the_box_is_not_changed(tmp_path):
    b = box(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    run("--box", str(b), "--to", str(tmp_path / "out"), *NOW)
    after = {
        p: p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file() and "out" not in p.relative_to(tmp_path).parts
    }
    assert after == before


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    b = box(tmp_path)
    to = str(tmp_path / "out")
    for argv in ([], ["--box", str(b)], ["--to", to], ["--box", str(b), "--to", to, "stray"], ["--box", str(b), "--to", to, "--licence"],
                 ["--box", str(b), "--to", to, "--licence", "no spaces allowed"], ["--box", str(tmp_path), "--to", to]):  # fmt: skip
        assert run(*argv).returncode == 2, argv
    assert "ro_crate.py" in run().stderr
