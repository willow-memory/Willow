"""warc: each captured page of a WARC, .warc.gz or .wacz as a passage under
its capture time, address and title; records read by their length; chunked,
gzipped and deflated bodies read; revisits, requests and the rest passed over;
hidden files skipped, an unreadable file skipped and counted, the same bytes
twice, originals unchanged, and MIRROR and FOLDER kept apart."""

from __future__ import annotations

import gzip
import importlib.util
import io
import uuid
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "warc.py"
spec = importlib.util.spec_from_file_location("warc", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

ROOF = (
    b"<!doctype html><html><head><title>The roof &amp; gutters</title>"
    b"<style>p{color:red}</style><script>var x = 'hidden';</script></head>"
    b"<body><h1>Our roof</h1><p>The roof was fixed on Tuesday by Kowalski.</p>"
    b"<p>The gutters are next.</p></body></html>"
)


def record(kind: str, uri: str, date: str, block: bytes, ctype: str = "", version="1.0") -> bytes:  # fmt: skip
    """One WARC record, byte for byte as the spec writes it."""
    head = [f"WARC/{version}", f"WARC-Type: {kind}",
            f"WARC-Record-ID: <urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, kind + uri + date)}>",
            f"WARC-Date: {date}"]  # fmt: skip
    if uri:
        head.append(f"WARC-Target-URI: {uri}")
    if ctype:
        head.append(f"Content-Type: {ctype}")
    head.append(f"Content-Length: {len(block)}")
    return ("\r\n".join(head) + "\r\n\r\n").encode() + block + b"\r\n\r\n"


def response(uri: str, date: str, body: bytes, status="200 OK", extra=(), ctype="text/html; charset=utf-8") -> bytes:  # fmt: skip
    head = [f"HTTP/1.1 {status}", f"Content-Type: {ctype}", *extra]
    if not any(h.lower().startswith("transfer-encoding") for h in extra):
        head.append(f"Content-Length: {len(body)}")
    block = ("\r\n".join(head) + "\r\n\r\n").encode() + body
    return record("response", uri, date, block, "application/http; msgtype=response")


def chunked(data: bytes, size: int = 7) -> bytes:
    out = b""
    for i in range(0, len(data), size):
        piece = data[i : i + size]
        out += f"{len(piece):x}\r\n".encode() + piece + b"\r\n"
    return out + b"0\r\n\r\n"


WARCINFO = record("warcinfo", "", "2024-03-02T08:00:00Z",
                  b"software: test-helper\r\nformat: WARC File Format 1.0\r\n",
                  "application/warc-fields")  # fmt: skip
REQUEST = record("request", "https://example.org/roof", "2024-03-02T08:15:30Z",
                 b"GET /roof HTTP/1.1\r\nHost: example.org\r\n\r\n",
                 "application/http; msgtype=request")  # fmt: skip
REVISIT = record("revisit", "https://example.org/roof", "2024-04-01T09:00:00Z",
                 b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n",
                 "application/http; msgtype=response")  # fmt: skip
GZIPPED = response(
    "https://example.org/garden",
    "2024-03-02T08:20:05Z",
    chunked(gzip.compress(b"<title>Garden</title><p>The tomatoes went in on the third.</p>", mtime=0)),
    extra=("Transfer-Encoding: chunked", "Content-Encoding: gzip"),
)  # fmt: skip
RECORDS = (WARCINFO, REQUEST, response("https://example.org/roof", "2024-03-02T08:15:30Z", ROOF), REVISIT, GZIPPED)  # fmt: skip
WARC = b"".join(RECORDS)


def per_record_gzip(*recs: bytes) -> bytes:
    """A .warc.gz the way crawlers write it: each record its own gzip member."""
    return b"".join(gzip.compress(rec, mtime=0) for rec in recs)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def mirror_of(tmp_path: Path, files: dict[str, bytes]) -> tuple[subprocess.CompletedProcess, Path]:  # fmt: skip
    src = tmp_path / "src"
    for rel, data in files.items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_bytes(data)
    out = tmp_path / "out"
    return run("mirror", "--from", str(src), "--to", str(out)), out


def text_of(data: bytes, tmp_path: Path, name: str = "crawl.warc") -> str:
    got, out = mirror_of(tmp_path, {name: data})
    assert got.returncode == 0, got.stdout + got.stderr
    return (out / (name + ".txt")).read_text(encoding="utf-8")


def test_each_page_is_a_passage_under_its_time_address_and_title(tmp_path):
    text = text_of(WARC, tmp_path)
    assert text == (
        "2024-03-02 08:15 https://example.org/roof\n"
        "The roof & gutters\n"
        "Our roof\n\n"
        "The roof was fixed on Tuesday by Kowalski.\n\n"
        "The gutters are next.\n"
        "\n"
        "2024-03-02 08:20 https://example.org/garden\n"
        "Garden\n"
        "The tomatoes went in on the third.\n"
    )


def test_the_kernel_finds_the_paragraph_and_the_page_by_its_address(tmp_path):
    got, out = mirror_of(tmp_path, {"crawl.warc": WARC})
    pile = kernel.chunks(out)
    hit = kernel.rank(pile, "who fixed the roof")
    assert hit and "Kowalski" in hit[0]["text"]
    first = kernel.rank(pile, "when was example.org/garden captured")
    assert first and first[0]["text"].startswith(
        "2024-03-02 08:20 https://example.org/garden"
    )


def test_revisits_requests_and_warcinfo_are_passed_over_and_said(tmp_path):
    got, out = mirror_of(tmp_path, {"crawl.warc": WARC})
    assert (
        "crawl.warc: 2 pages; left out 1 request, 1 revisit, 1 warcinfo" in got.stdout
    )
    assert "2024-04-01" not in (out / "crawl.warc.txt").read_text()


def test_a_warc_gz_with_one_gzip_member_per_record_reads_the_same(tmp_path):
    gz = per_record_gzip(*RECORDS)
    assert gz.count(b"\x1f\x8b\x08") == 5, "five members, one per record"
    assert gzip.decompress(gz) == WARC, "the standard library reads every member"
    assert text_of(gz, tmp_path, "crawl.warc.gz") == text_of(WARC, tmp_path / "plain")


def test_a_warc_gz_compressed_whole_reads_the_same(tmp_path):
    assert text_of(gzip.compress(WARC, mtime=0), tmp_path, "c.warc.gz") == text_of(WARC, tmp_path / "p")  # fmt: skip


def test_a_wacz_is_read_without_unpacking_its_archives_in_name_order(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("datapackage.json", b"{}")
        zf.writestr("archive/data-2.warc.gz", per_record_gzip(GZIPPED))
        zf.writestr("archive/data-1.warc.gz", per_record_gzip(WARCINFO, response("https://example.org/roof", "2024-03-02T08:15:30Z", ROOF)))  # fmt: skip
        zf.writestr("pages/pages.jsonl", b'{"url": "https://example.org/"}\n')
    text = text_of(buf.getvalue(), tmp_path, "session.wacz")
    assert text.index("example.org/roof") < text.index("example.org/garden")
    assert "Kowalski" in text and "tomatoes" in text


def test_records_are_read_by_their_length_not_by_a_blank_line_inside_them(tmp_path):
    body = (
        b"line one\r\n\r\nWARC/1.0\r\nWARC-Type: response\r\n\r\nstill the same page\n"
    )
    data = response(
        "https://example.org/a.txt", "2024-03-02T08:15:30Z", body, ctype="text/plain"
    )
    text = text_of(data + response("https://example.org/b", "2024-03-03T10:00:00Z", b"<p>Second.</p>"), tmp_path)  # fmt: skip
    assert "still the same page" in text and "WARC-Type: response" in text
    assert text.count("https://example.org/") == 2 and "Second." in text


def test_a_resource_record_has_no_http_envelope(tmp_path):
    data = record("resource", "https://example.org/notes.txt", "2024-05-06T07:08:09.123Z",
                  b"Bins go out on Thursday.\n", "text/plain", version="1.1")  # fmt: skip
    data += record("resource", "urn:pageinfo:https://example.org/", "2024-05-06T07:08:09Z",
                   b'{"pages": 1}', "application/json", version="1.1")  # fmt: skip
    assert text_of(data, tmp_path) == (
        "2024-05-06 07:08 https://example.org/notes.txt\nBins go out on Thursday.\n"
    )


def test_a_status_other_than_2xx_images_scripts_and_styles_are_left_out(tmp_path):
    data = (
        response("https://example.org/gone", "2024-03-02T08:00:00Z", b"<p>Not here</p>", "404 Not Found")
        + response("https://example.org/moved", "2024-03-02T08:00:00Z", b"<p>Moved</p>", "301 Moved Permanently")
        + response("https://example.org/a.png", "2024-03-02T08:00:00Z", b"\x89PNG", ctype="image/png")
        + response("https://example.org/a.js", "2024-03-02T08:00:00Z", b"var a;", ctype="application/javascript")
        + response("https://example.org/a.css", "2024-03-02T08:00:00Z", b"p{}", ctype="text/css")
        + response("https://example.org/ok", "2024-03-02T08:00:00Z", b"<p>Here</p>", "203 Non-Authoritative")
    )  # fmt: skip
    got, out = mirror_of(tmp_path, {"c.warc": data})
    text = (out / "c.warc.txt").read_text()
    assert (
        "Here" in text
        and "Not here" not in text
        and "Moved" not in text
        and "PNG" not in text
    )
    assert "c.warc: 1 pages; left out 2 not 2xx, 3 not text" in got.stdout


def test_deflate_either_way_is_read_and_brotli_is_counted(tmp_path):
    page = b"<p>Deflated words.</p>"
    raw = zlib.compressobj(wbits=-15)
    data = (
        response("https://example.org/z", "2024-03-02T08:00:00Z", zlib.compress(page), extra=("Content-Encoding: deflate",))
        + response("https://example.org/r", "2024-03-02T08:01:00Z", raw.compress(page) + raw.flush(), extra=("Content-Encoding: deflate",))
        + response("https://example.org/b", "2024-03-02T08:02:00Z", b"\x1b\x00\x00", extra=("Content-Encoding: br",))
    )  # fmt: skip
    got, out = mirror_of(tmp_path, {"c.warc": data})
    assert (out / "c.warc.txt").read_text().count("Deflated words.") == 2
    assert "left out 1 br" in got.stdout


def test_a_broken_body_is_left_out_and_the_rest_of_the_file_still_read(tmp_path):
    data = (
        response("https://example.org/badgz", "2024-03-02T08:00:00Z", b"not gzip", extra=("Content-Encoding: gzip",))
        + record("response", "https://example.org/odd", "2024-03-02T08:00:00Z", b"SPDY nonsense\r\n\r\n<p>x</p>", "application/http; msgtype=response")
        + response("https://example.org/good", "2024-03-02T08:01:00Z", b"<p>Good page.</p>")
    )  # fmt: skip
    got, out = mirror_of(tmp_path, {"c.warc": data})
    assert (
        out / "c.warc.txt"
    ).read_text() == "2024-03-02 08:01 https://example.org/good\nGood page.\n"
    assert "c.warc: 1 pages; left out 1 encoding, 1 not http" in got.stdout


def test_a_chunked_body_cut_off_keeps_what_arrived_and_one_stored_joined_is_read_as_stored(
    tmp_path,
):
    data = (
        response("https://example.org/cut", "2024-03-02T08:00:00Z", b"5\r\nHello\r\n9\r\n Wor", extra=("Transfer-Encoding: chunked",))
        + response("https://example.org/joined", "2024-03-02T08:01:00Z", b"<p>Already joined.</p>", extra=("Transfer-Encoding: chunked",))
        + response("https://example.org/ext", "2024-03-02T08:02:00Z", b"4;name=v\nSome\n0\n\n", extra=("Transfer-Encoding: chunked",))
    )  # fmt: skip
    text = text_of(data, tmp_path)
    assert "Hello Wor\n" in text and "Already joined.\n" in text
    assert "Some\n" in text


def test_a_heading_that_repeats_the_title_is_not_written_twice(tmp_path):
    body = b"<title>Example Domain</title><h1>Example Domain</h1><p>Illustrative.</p><h2>Example Domain</h2>"
    text = text_of(
        response("http://example.com/", "2017-03-06T04:02:06Z", body), tmp_path
    )
    assert (
        text
        == "2017-03-06 04:02 http://example.com/\nExample Domain\nIllustrative.\n\nExample Domain\n"
    )


def test_the_charset_comes_from_content_type_then_the_meta_tag_then_utf8(tmp_path):
    latin = "<p>Café Müller</p>".encode("latin-1")
    meta = (
        b'<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">'
        + latin
    )
    data = (
        response("https://example.org/1", "2024-03-02T08:00:00Z", latin, ctype="text/html; charset=ISO-8859-1")
        + response("https://example.org/2", "2024-03-02T08:00:00Z", meta, ctype="text/html")
        + response("https://example.org/3", "2024-03-02T08:00:00Z", b"<p>caf\xc3\xa9 and \xff</p>", ctype="text/html")
    )  # fmt: skip
    text = text_of(data, tmp_path)
    assert text.count("Café Müller") == 2 and "café and �" in text


def test_the_same_address_captured_twice_is_two_passages_with_their_own_dates(tmp_path):
    data = response(
        "https://example.org/news", "2024-03-02T08:00:00Z", b"<p>Old news.</p>"
    )
    data += response(
        "https://example.org/news", "2024-06-09T17:45:59Z", b"<p>New news.</p>"
    )
    text = text_of(data, tmp_path)
    assert "2024-03-02 08:00 https://example.org/news\nOld news." in text
    assert "2024-06-09 17:45 https://example.org/news\nNew news." in text


def test_a_long_page_is_wrapped_for_the_kernel_and_only_its_first_passage_holds_the_address(
    tmp_path,
):
    para = " ".join(f"word{i}" for i in range(300))
    body = (
        "<title>Long</title>" + "".join(f"<p>{i} {para}</p>" for i in range(5))
    ).encode()
    text = text_of(
        response("https://example.org/long", "2024-03-02T08:00:00Z", body), tmp_path
    )
    assert max(len(line) for line in text.splitlines()) <= mod.WIDTH
    got, out = mirror_of(tmp_path / "k", {"c.warc": response("https://example.org/long", "2024-03-02T08:00:00Z", body)})  # fmt: skip
    pile = kernel.chunks(out)
    assert len(pile) > 10 and all(len(c["text"]) <= kernel.MAX_CHUNK for c in pile)
    assert sum("example.org/long" in c["text"] for c in pile) == 1


def test_a_page_past_max_page_is_cut_and_the_cut_is_said_on_the_files_line_not_in_it(
    tmp_path,
):
    body = b"".join(b"<p>" + b"x" * 999 + b"</p>" for _ in range(30))
    got, out = mirror_of(tmp_path, {"c.warc": response("https://example.org/big", "2024-03-02T08:00:00Z", body)})  # fmt: skip
    text = (out / "c.warc.txt").read_text()
    assert text.count("x" * 999) == 20 and text.rstrip().endswith("x" * 999)
    assert "c.warc: 1 pages; left out 1 cut short" in got.stdout


def test_a_mirror_past_the_kernels_max_file_goes_on_in_a_second_file(tmp_path):
    body = b"".join(b"<p>" + b"y" * 900 + b"</p>" for _ in range(20))
    data = b"".join(response(f"https://example.org/{i}", "2024-03-02T08:00:00Z", body) for i in range(60))  # fmt: skip
    got, out = mirror_of(tmp_path, {"c.warc": data})
    first, second = (
        (out / "c.warc.txt").read_bytes(),
        (out / "c.warc.2.txt").read_bytes(),
    )
    assert len(first) <= kernel.MAX_FILE and len(second) <= kernel.MAX_FILE
    assert first.decode().count("https://example.org/") + second.decode().count("https://example.org/") == 60  # fmt: skip
    assert second.startswith(b"2024-03-02 08:00 https://example.org/")
    assert "wrote 2 files" in got.stdout and len(kernel.chunks(out)) > 1000


def test_an_odd_date_is_kept_as_written_and_nothing_stands_in_for_a_missing_address_or_title(
    tmp_path,
):
    data = record("resource", "", "March 2024", b"Plain.\n", "text/plain")
    data += record(
        "resource", "https://example.org/n.txt", "", b"Undated.\n", "text/plain"
    )
    assert (
        text_of(data, tmp_path)
        == "March 2024\nPlain.\n\nhttps://example.org/n.txt\nUndated.\n"
    )


def test_a_header_line_folded_onto_the_next_is_read_as_one():
    assert mod.headers([b"WARC-Target-URI: https://example.org/\r\n", b"  a-long-tail\r\n"]) == {
        "warc-target-uri": "https://example.org/ a-long-tail"
    }  # fmt: skip


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"crawls/day1.warc.gz": per_record_gzip(*RECORDS)})
    assert got.returncode == 0, got.stderr
    assert (out / "crawls/day1.warc.gz.txt").is_file()
    assert got.stdout.strip().splitlines()[-1].endswith("; skipped 0")
    assert "wrote 1 files to" in got.stdout


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path, {"a.warc": WARC, ".hid/a.warc": WARC, ".a.warc": WARC}
    )
    assert sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()) == ["a.warc.txt"]  # fmt: skip


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"a.warc.gz": per_record_gzip(*RECORDS)})
    before = (tmp_path / "src" / "a.warc.gz").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "a.warc.gz.txt").read_bytes() == (
        out / "a.warc.gz.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "a.warc.gz").read_bytes() == before
    assert sorted(p.name for p in (tmp_path / "src").iterdir()) == ["a.warc.gz"]


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    files = {
        "good.warc": WARC,
        "notwarc.warc": b"hello\n",
        "badgz.warc.gz": b"\x1f\x8b\x08\x00garbage",
        "badzip.wacz": b"PK not a zip",
        "only-info.warc": WARCINFO + REVISIT,
        "cut.warc": WARC[:-40],
    }
    got, out = mirror_of(tmp_path, files)
    assert got.returncode == 0, got.stderr
    assert sorted(p.name for p in out.iterdir()) == ["cut.warc.txt", "good.warc.txt"]
    assert "wrote 2 files" in got.stdout and "skipped 4" in got.stdout
    assert "cut.warc: 1 pages; left out 1 request, 1 revisit, 1 unreadable rest, 1 warcinfo" in got.stdout  # fmt: skip


def test_a_folder_with_nothing_to_read_waits_on_you(tmp_path):
    got, _ = mirror_of(tmp_path, {"notes.md": b"nothing here\n"})
    assert got.returncode == 42 and "wrote 0 files" in got.stdout


def test_a_mirror_inside_the_folder_or_the_folder_inside_it_is_refused(tmp_path):
    (tmp_path / "src").mkdir()
    for to in (tmp_path / "src" / "m", tmp_path):
        got = run("mirror", "--from", str(tmp_path / "src"), "--to", str(to))
        assert got.returncode == 2 and got.stderr.startswith("refused")
    got = run(
        "mirror", "--from", str(tmp_path / "missing"), "--to", str(tmp_path / "m")
    )
    assert got.returncode == 2 and got.stderr.startswith("refused")


def test_a_bad_command_line_says_how_to_run_it():
    for argv in ([], ["mirror"], ["mirror", "--from", "a"], ["nope", "--from", "a", "--to", "b"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "warc.py" in got.stderr


def test_an_attribute_holding_a_comment_or_a_bracket_is_not_read_as_text(tmp_path):
    body = (
        b'<title>Heritrix</title><table data-mw=\'{"a":"<!-- x\\n-->","b":"ISO<ref name=\\"s\\"/>"}\'>'
        b'<tr><td>Web crawler</td></tr></table><p title="a > b">Heritrix is the Internet Archive\'s crawler.</p>'
        b"<p class='it's'>broken quote</p>"
    )
    text = text_of(
        response(
            "https://en.wikipedia.org/wiki/Heritrix", "2024-03-02T08:00:00Z", body
        ),
        tmp_path,
    )
    assert text.split("\n")[2:5] == [
        "Web crawler",
        "",
        "Heritrix is the Internet Archive's crawler.",
    ]
    assert "data-mw" not in text and "ref name" not in text and '"b"' not in text


def test_no_word_the_reader_adds_holds_a_question_about_something_absent(tmp_path):
    """Willow's first promise: a word written into passage after passage
    would hold half of a two-word question about anything. Every word in most
    passages is the archive's own, from a WARC-Target-URI or a WARC-Date
    (kept: they are the values a person asks by); none is the reader's, and
    no stand-in the reader could write is served for an absent question."""
    pages = [("roof", "<title>Roof</title><p>Kowalski fixed the roof.</p>"),
             ("garden", "<p>The tomatoes went in.</p><p>Beans next.</p>"),
             ("bins", "<p>Bins go out on Thursday.</p>"),
             ("big", "".join(f"<p>{i} " + "z" * 900 + "</p>" for i in range(30))),
             ("gone", "<p>Not here</p>")]  # fmt: skip
    data = WARCINFO + REQUEST + REVISIT
    for i, (name, html) in enumerate(pages):
        data += response(f"https://example.org/{name}", f"2024-03-0{i + 1}T08:00:00Z", html.encode())  # fmt: skip
    data += record("resource", "", "", b"Loose note.\n", "text/plain")
    got, out = mirror_of(tmp_path, {"c.warc": data})
    pile = kernel.chunks(out)
    heads = [c for c in pile if c["text"][:4] == "2024"]
    count: dict[str, int] = {}
    for c in heads + [c for c in pile if "zzz" not in c["text"]]:
        for w in set(kernel.words(c["text"])) - kernel.FUNCTION:
            count[w] = count.get(w, 0) + 1
    common = {w for w, n in count.items() if n >= len(heads)}
    record_values = {"https", "example", "org", "2024", "03", "08", "00"}
    assert common == record_values, common
    filler = ["title", "untitled", "address", "record", "date", "left", "characters", "rest", "cut", "short", "captured", "page"]  # fmt: skip
    for w in filler:
        assert all(w not in kernel.words(c["text"]) for c in pile), w
        assert kernel.rank(pile, f"volcano {w}") == [], w
    assert "Kowalski" in kernel.rank(pile, "who fixed the roof")[0]["text"]
    assert "Thursday" in kernel.rank(pile, "when do bins go out")[0]["text"]
    assert "tomatoes" in kernel.rank(pile, "what is planted in the garden")[0]["text"]
