#!/usr/bin/env python3
"""Write the digital life of Bernadette "Bernie" Halloran (67, Ballarat, Victoria).

    python3 make_life.py            # delete and re-create life/ next to this script
    python3 make_life.py --check    # re-derive in memory, verify life/ and PLANTED facts
    python3 make_life.py --planted  # print the planted-needs table (source of PLANTED.md)

Standard library only, seeded, byte-identical on every run and OS.
"""

import base64
import hashlib
import html
import io
import json
import quopri
import random
import re
import shutil
import sys
import zipfile
from datetime import date, datetime, timedelta, timezone
from email import message_from_bytes, policy
from email.utils import format_datetime
from pathlib import Path

SEED = 19590417
TODAY = date(2026, 10, 24)
HERE = Path(__file__).resolve().parent
LIFE = HERE / "life"
ZIP_TIME = (2026, 10, 24, 9, 0, 0)

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

FILES = {}


def put(path, data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    if path in FILES:
        raise SystemExit("duplicate path: " + path)
    FILES[path] = data


def long_date(d):
    return f"{DAYS[d.weekday()]}, {d.day} {MONTHS[d.month - 1]} {d.year}"


def mel_tz(d):
    m, dd = d.month, d.day
    dst = m in (11, 12, 1, 2, 3) or (m == 10 and dd >= 6) or (m == 4 and dd < 6)
    return timezone(timedelta(hours=11 if dst else 10))


def at(y, mo, d, h=9, mi=0, s=0):
    base = datetime(y, mo, d, h, mi, s)
    return base.replace(tzinfo=mel_tz(base.date()))


def slug(text):
    s = re.sub(r"[^A-Za-z0-9 \-]+", "", text).strip()
    return re.sub(r"\s+", " ", s)[:60].strip()


# ---------------------------------------------------------------- people

ME = "Bernie Halloran <bernie.halloran59@bigpond.com>"
GERRY = "Gerry Halloran <gerryhalloran@bigpond.com>"
SIOBHAN = "Siobhán Pettit <siobhan.pettit@gmail.com>"
COLLEEN = "Colleen Murphy <colleenmurphy.ennis@eircom.net>"
DECLAN = "Declan Halloran <dec.halloran@outlook.com>"
BRENDAN = "Brendan Considine <bconsidine.lahinch@gmail.com>"
PAT = "Pat Kinnane <pat.kinnane@wpbc.org.au>"
MAGS = "Mags Doyle <magsdoyle57@bigpond.com>"
AOIFEB = "Aoife Brennan <aoife.brennan@iinet.net.au>"
COMMITTEE = "WPBC Committee <committee@wpbc.org.au>"

# ---------------------------------------------------------------- email


def hdr(value):
    if value.isascii():
        return value
    return "=?UTF-8?B?" + base64.b64encode(value.encode("utf-8")).decode() + "?="


def addr_hdr(a):
    if "<" in a:
        name, rest = a.split("<", 1)
        name = name.strip()
        if not name.isascii():
            return f"{hdr(name)} <{rest}"
    return a


def html_of(text):
    paras = []
    for block in text.strip("\n").split("\n\n"):
        lines = [html.escape(x) for x in block.split("\n")]
        paras.append("<p>" + "<br>\n".join(lines) + "</p>")
    return (
        '<html><head><meta charset="utf-8"></head><body style="font-family:'
        'Arial,sans-serif;font-size:14px">\n' + "\n".join(paras) + "\n</body></html>\n"
    )


def text_part(body, subtype, qp):
    if not body.endswith("\n"):
        body += "\n"
    if qp:
        payload = quopri.encodestring(body.encode("utf-8")).decode("ascii")
        cte = "quoted-printable"
    else:
        payload = body
        cte = "7bit" if body.isascii() else "8bit"
    return (
        f'Content-Type: text/{subtype}; charset="utf-8"\n'
        f"Content-Transfer-Encoding: {cte}\n\n{payload}"
    )


def multipart(kind, parts, boundary):
    out = [
        f'Content-Type: multipart/{kind}; boundary="{boundary}"\n\n'
        "This is a multi-part message in MIME format.\n"
    ]
    for p in parts:
        out.append(f"--{boundary}\n{p.rstrip(chr(10))}\n")
    out.append(f"--{boundary}--\n")
    return "\n".join(out)


def build_message(
    frm,
    to,
    subject,
    when,
    body,
    html_alt=False,
    qp=False,
    cc=None,
    attach=None,
    mailer=None,
    reply_to_id=None,
):
    seed = f"{frm}|{subject}|{when.isoformat()}"
    hx = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    dom = frm.split("@")[-1].rstrip(">")
    head = [f"From: {addr_hdr(frm)}", f"To: {addr_hdr(to)}"]
    if cc:
        head.append(f"Cc: {addr_hdr(cc)}")
    head += [
        f"Subject: {hdr(subject)}",
        f"Date: {format_datetime(when)}",
        f"Message-ID: <{hx[:24]}@{dom}>",
    ]
    if reply_to_id:
        head.append(f"In-Reply-To: <{reply_to_id}>")
    if mailer:
        head.append(f"X-Mailer: {mailer}")
    head.append("MIME-Version: 1.0")
    inner = text_part(body, "plain", qp)
    if html_alt:
        inner = multipart(
            "alternative",
            [inner, text_part(html_of(body), "html", qp)],
            "=_alt_" + hx[:20],
        )
    if attach:
        name, ctype, data = attach
        b64 = base64.encodebytes(data).decode("ascii")
        att = (
            f'Content-Type: {ctype}; name="{name}"\n'
            f'Content-Disposition: attachment; filename="{name}"\n'
            f"Content-Transfer-Encoding: base64\n\n{b64}"
        )
        inner = multipart("mixed", [inner, att], "=_mix_" + hx[:20])
    return "\n".join(head) + "\n" + inner


def mail(folder, frm, to, subject, when, body, **kw):
    msg = build_message(frm, to, subject, when, body, **kw)
    base = f"Mail/{folder}/{when:%Y-%m-%d} {slug(subject)}"
    path = base + ".eml"
    n = 2
    while path in FILES:
        path = f"{base} ({n}).eml"
        n += 1
    put(path, msg.replace("\n", "\r\n"))
    return path


MBOX = []


def mbox_add(frm, to, subject, when, body, **kw):
    msg = build_message(frm, to, subject, when, body, **kw)
    sender = frm.split("<")[-1].rstrip(">")
    utc = when.astimezone(timezone.utc)
    stamp = (
        f"{DAYS[utc.weekday()][:3]} {MONTHS[utc.month - 1][:3]} "
        f"{utc.day:2d} {utc:%H:%M:%S} {utc.year}"
    )
    lines = []
    for ln in msg.split("\n"):
        if re.match(r">*From ", ln):
            ln = ">" + ln
        lines.append(ln)
    MBOX.append(
        (when, f"From {sender} {stamp}\n" + "\n".join(lines).rstrip("\n") + "\n")
    )


# ---------------------------------------------------------------- zip / office


def zip_bytes(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in entries:
            zi = zipfile.ZipInfo(name, date_time=ZIP_TIME)
            zi.compress_type = zipfile.ZIP_STORED
            zi.create_system = 3
            zi.external_attr = 0o100644 << 16
            z.writestr(zi, data.encode("utf-8") if isinstance(data, str) else data)
    return buf.getvalue()


XML_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
OD_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def core_xml(title, created, modified):
    return (
        XML_HEAD
        + '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/'
        '2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"'
        ' xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/'
        '2001/XMLSchema-instance">'
        f"<dc:title>{html.escape(title)}</dc:title><dc:creator>Bernie Halloran"
        "</dc:creator><cp:lastModifiedBy>Bernie Halloran</cp:lastModifiedBy>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{modified}</dcterms:modified>'
        "</cp:coreProperties>"
    )


def app_xml(app):
    return (
        XML_HEAD + '<Properties xmlns="http://schemas.openxmlformats.org/'
        f'officeDocument/2006/extended-properties"><Application>{app}</Application>'
        "</Properties>"
    )


def docx(title, paragraphs, created, modified):
    """paragraphs: list of str; '# x' heading, '## x' subheading, '' blank."""
    body = []
    for p in paragraphs:
        if p.startswith("## "):
            rpr, text = '<w:rPr><w:b/><w:sz w:val="26"/></w:rPr>', p[3:]
        elif p.startswith("# "):
            rpr, text = '<w:rPr><w:b/><w:sz w:val="34"/></w:rPr>', p[2:]
        else:
            rpr, text = "", p
        if text:
            body.append(
                f'<w:p><w:r>{rpr}<w:t xml:space="preserve">'
                f"{html.escape(text, quote=False)}</w:t></w:r></w:p>"
            )
        else:
            body.append("<w:p/>")
    doc = (
        XML_HEAD + '<w:document xmlns:w="http://schemas.openxmlformats.org/'
        'wordprocessingml/2006/main"><w:body>'
        + "".join(body)
        + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" '
        'w:right="1440" w:bottom="1440" w:left="1440" w:header="708" '
        'w:footer="708" w:gutter="0"/></w:sectPr></w:body></w:document>'
    )
    ctypes = (
        XML_HEAD + '<Types xmlns="http://schemas.openxmlformats.org/package/'
        '2006/content-types"><Default Extension="rels" ContentType="application/'
        'vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml"'
        ' ContentType="application/xml"/><Override PartName="/word/document.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument.'
        'wordprocessingml.document.main+xml"/><Override PartName="/docProps/'
        'core.xml" ContentType="application/vnd.openxmlformats-package.core-'
        'properties+xml"/><Override PartName="/docProps/app.xml" ContentType='
        '"application/vnd.openxmlformats-officedocument.extended-properties+xml"'
        "/></Types>"
    )
    rels = (
        XML_HEAD + f'<Relationships xmlns="{REL_NS}">'
        f'<Relationship Id="rId1" Type="{OD_REL}/officeDocument" '
        'Target="word/document.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/'
        '2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        f'<Relationship Id="rId3" Type="{OD_REL}/extended-properties" '
        'Target="docProps/app.xml"/></Relationships>'
    )
    return zip_bytes(
        [
            ("[Content_Types].xml", ctypes),
            ("_rels/.rels", rels),
            ("word/document.xml", doc),
            ("docProps/core.xml", core_xml(title, created, modified)),
            ("docProps/app.xml", app_xml("Microsoft Office Word")),
        ]
    )


def col(n):
    s = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def num_text(v):
    if isinstance(v, float):
        return repr(round(v, 2))
    return str(v)


def sheet_xml(rows):
    out = []
    for ri, row in enumerate(rows, 1):
        cells = []
        for ci, v in enumerate(row):
            ref = f"{col(ci)}{ri}"
            if v is None or v == "":
                continue
            if isinstance(v, tuple):
                formula, cached = v
                cells.append(
                    f'<c r="{ref}"><f>{html.escape(formula)}</f>'
                    f"<v>{num_text(cached)}</v></c>"
                )
            elif isinstance(v, (int, float)):
                cells.append(f'<c r="{ref}"><v>{num_text(v)}</v></c>')
            else:
                cells.append(
                    f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">'
                    f"{html.escape(str(v), quote=False)}</t></is></c>"
                )
        out.append(f'<row r="{ri}">' + "".join(cells) + "</row>")
    return (
        XML_HEAD + '<worksheet xmlns="http://schemas.openxmlformats.org/'
        'spreadsheetml/2006/main"><sheetData>'
        + "".join(out)
        + "</sheetData></worksheet>"
    )


def xlsx(title, sheets, created, modified):
    n = len(sheets)
    over = "".join(
        f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType='
        '"application/vnd.openxmlformats-officedocument.spreadsheetml.'
        'worksheet+xml"/>'
        for i in range(1, n + 1)
    )
    ctypes = (
        XML_HEAD + '<Types xmlns="http://schemas.openxmlformats.org/package/'
        '2006/content-types"><Default Extension="rels" ContentType="application/'
        'vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml"'
        ' ContentType="application/xml"/><Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml'
        '.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType='
        '"application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"'
        "/>" + over + '<Override PartName="/docProps/core.xml" ContentType='
        '"application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/'
        'vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>'
    )
    rels = (
        XML_HEAD + f'<Relationships xmlns="{REL_NS}">'
        f'<Relationship Id="rId1" Type="{OD_REL}/officeDocument" '
        'Target="xl/workbook.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/'
        '2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        f'<Relationship Id="rId3" Type="{OD_REL}/extended-properties" '
        'Target="docProps/app.xml"/></Relationships>'
    )
    wb_sheets = "".join(
        f'<sheet name="{html.escape(name)}" sheetId="{i}" r:id="rId{i}"/>'
        for i, (name, _) in enumerate(sheets, 1)
    )
    wb = (
        XML_HEAD + '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/'
        f'2006/main" xmlns:r="{OD_REL}"><sheets>{wb_sheets}</sheets></workbook>'
    )
    wb_rels = (
        XML_HEAD
        + f'<Relationships xmlns="{REL_NS}">'
        + "".join(
            f'<Relationship Id="rId{i}" Type="{OD_REL}/worksheet" '
            f'Target="worksheets/sheet{i}.xml"/>'
            for i in range(1, n + 1)
        )
        + f'<Relationship Id="rId{n + 1}" Type="{OD_REL}/styles" '
        'Target="styles.xml"/></Relationships>'
    )
    styles = (
        XML_HEAD + '<styleSheet xmlns="http://schemas.openxmlformats.org/'
        'spreadsheetml/2006/main"><fonts count="1"><font><sz val="11"/><name '
        'val="Calibri"/></font></fonts><fills count="2"><fill><patternFill '
        'patternType="none"/></fill><fill><patternFill patternType="gray125"/>'
        '</fill></fills><borders count="1"><border><left/><right/><top/><bottom/>'
        '<diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" '
        'fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="1">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/>'
        "</cellStyles></styleSheet>"
    )
    entries = [
        ("[Content_Types].xml", ctypes),
        ("_rels/.rels", rels),
        ("xl/workbook.xml", wb),
        ("xl/_rels/workbook.xml.rels", wb_rels),
        ("xl/styles.xml", styles),
    ]
    for i, (_, rows) in enumerate(sheets, 1):
        entries.append((f"xl/worksheets/sheet{i}.xml", sheet_xml(rows)))
    entries += [
        ("docProps/core.xml", core_xml(title, created, modified)),
        ("docProps/app.xml", app_xml("Microsoft Excel")),
    ]
    return zip_bytes(entries)


def odt(title, paragraphs, when):
    ns = (
        'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"'
    )
    body = []
    for p in paragraphs:
        if p.startswith("# "):
            body.append(f'<text:h text:outline-level="1">{html.escape(p[2:])}</text:h>')
        elif p.startswith("## "):
            body.append(f'<text:h text:outline-level="2">{html.escape(p[3:])}</text:h>')
        else:
            body.append(f"<text:p>{html.escape(p)}</text:p>")
    content = (
        XML_HEAD.replace(' standalone="yes"', "")
        + f'<office:document-content {ns} office:version="1.2"><office:body>'
        "<office:text>"
        + "".join(body)
        + "</office:text></office:body></office:document-content>"
    )
    meta = (
        XML_HEAD.replace(' standalone="yes"', "")
        + '<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:'
        'office:1.0" xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" office:version="1.2">'
        f"<office:meta><meta:generator>LibreOffice/7.6</meta:generator><dc:title>"
        f"{html.escape(title)}</dc:title><meta:initial-creator>Bernie Halloran"
        f"</meta:initial-creator><dc:date>{when}</dc:date></office:meta>"
        "</office:document-meta>"
    )
    manifest = (
        XML_HEAD.replace(' standalone="yes"', "")
        + '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:'
        'xmlns:manifest:1.0" manifest:version="1.2"><manifest:file-entry '
        'manifest:full-path="/" manifest:version="1.2" manifest:media-type='
        '"application/vnd.oasis.opendocument.text"/><manifest:file-entry '
        'manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
        '<manifest:file-entry manifest:full-path="meta.xml" manifest:media-type='
        '"text/xml"/></manifest:manifest>'
    )
    return zip_bytes(
        [
            ("mimetype", "application/vnd.oasis.opendocument.text"),
            ("META-INF/manifest.xml", manifest),
            ("content.xml", content),
            ("meta.xml", meta),
        ]
    )


def epub(title, author, uid, chapters):
    container = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<container version="1.0" '
        'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>'
        '<rootfile full-path="OEBPS/content.opf" media-type="application/'
        'oebps-package+xml"/></rootfiles></container>\n'
    )
    items = "".join(
        f'<item id="ch{i}" href="ch{i}.xhtml" media-type="application/xhtml+xml"/>'
        for i in range(1, len(chapters) + 1)
    )
    spine = "".join(f'<itemref idref="ch{i}"/>' for i in range(1, len(chapters) + 1))
    opf = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<package xmlns="http://www.idpf.org/'
        '2007/opf" version="3.0" unique-identifier="bookid"><metadata xmlns:dc='
        '"http://purl.org/dc/elements/1.1/">'
        f'<dc:identifier id="bookid">{uid}</dc:identifier><dc:title>'
        f"{html.escape(title)}</dc:title><dc:creator>{html.escape(author)}"
        "</dc:creator><dc:language>en-AU</dc:language><meta property="
        '"dcterms:modified">2024-09-02T00:00:00Z</meta></metadata><manifest>'
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" '
        f'properties="nav"/>{items}</manifest><spine>{spine}</spine></package>\n'
    )
    nav_li = "".join(
        f'<li><a href="ch{i}.xhtml">{html.escape(t)}</a></li>'
        for i, (t, _) in enumerate(chapters, 1)
    )
    xh = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<html xmlns="http://www.w3.org/1999/'
        'xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><head><title>{t}</title>'
        "</head><body>{b}</body></html>\n"
    )
    entries = [
        ("mimetype", "application/epub+zip"),
        ("META-INF/container.xml", container),
        ("OEBPS/content.opf", opf),
        (
            "OEBPS/nav.xhtml",
            xh.format(
                t="Contents", b='<nav epub:type="toc"><ol>' + nav_li + "</ol></nav>"
            ),
        ),
    ]
    for i, (t, paras) in enumerate(chapters, 1):
        b = f"<h1>{html.escape(t)}</h1>" + "".join(
            f"<p>{html.escape(p)}</p>" for p in paras
        )
        entries.append((f"OEBPS/ch{i}.xhtml", xh.format(t=html.escape(t), b=b)))
    return zip_bytes(entries)


# ---------------------------------------------------------------- pdf


def pdf_escape(s):
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def pdf(lines, title, created):
    """lines: list of (font, size, text); font 'R' or 'B'. One A4 page."""
    ops = ["BT", "72 780 Td", "14 TL"]
    for font, size, text in lines:
        ops.append(f"/F{1 if font == 'R' else 2} {size} Tf ({pdf_escape(text)}) Tj T*")
    ops.append("ET")
    stream = ("\n".join(ops) + "\n").encode("latin-1")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>",
        b"<< /Length "
        + str(len(stream)).encode()
        + b" >>\nstream\n"
        + stream
        + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
        b"/Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold "
        b"/Encoding /WinAnsiEncoding >>",
        (
            "<< /Title (" + pdf_escape(title) + ") /Producer (ScanSnap Manager 7.2) "
            "/CreationDate (D:" + created + ") >>"
        ).encode("latin-1"),
    ]
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R /Info {len(objs)} 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n"
    ).encode()
    return bytes(out)


# ---------------------------------------------------------------- ics / vcf


def ics_esc(s):
    return (
        s.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def fold(line):
    if len(line.encode("utf-8")) <= 75:
        return line
    parts, cur = [], ""
    for ch in line:
        limit = 75 if not parts else 74
        if len((cur + ch).encode("utf-8")) > limit:
            parts.append(cur)
            cur = ""
        cur += ch
    parts.append(cur)
    return "\r\n ".join(parts)


VTZ = """BEGIN:VTIMEZONE
TZID:Australia/Melbourne
BEGIN:STANDARD
DTSTART:19700405T030000
TZOFFSETFROM:+1100
TZOFFSETTO:+1000
RRULE:FREQ=YEARLY;BYMONTH=4;BYDAY=1SU
TZNAME:AEST
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:19701004T020000
TZOFFSETFROM:+1000
TZOFFSETTO:+1100
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=1SU
TZNAME:AEDT
END:DAYLIGHT
END:VTIMEZONE"""


def ics(calname, events, prodid):
    out = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{prodid}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{calname}",
        "X-WR-TIMEZONE:Australia/Melbourne",
    ]
    out += VTZ.split("\n")
    for ev in events:
        uid = hashlib.sha1(
            (calname + ev["summary"] + str(ev["start"])).encode()
        ).hexdigest()[:16]
        out += ["BEGIN:VEVENT", f"UID:{uid}@halloran.home", "DTSTAMP:20261024T000000Z"]
        start = ev["start"]
        if isinstance(start, datetime):
            end = ev.get("end") or start + timedelta(hours=1)
            out.append(f"DTSTART;TZID=Australia/Melbourne:{start:%Y%m%dT%H%M%S}")
            out.append(f"DTEND;TZID=Australia/Melbourne:{end:%Y%m%dT%H%M%S}")
        else:
            end = ev.get("end") or start + timedelta(days=1)
            out.append(f"DTSTART;VALUE=DATE:{start:%Y%m%d}")
            out.append(f"DTEND;VALUE=DATE:{end:%Y%m%d}")
        if ev.get("rrule"):
            out.append("RRULE:" + ev["rrule"])
        for ex in ev.get("exdates", []):
            out.append(f"EXDATE;TZID=Australia/Melbourne:{ex:%Y%m%dT%H%M%S}")
        out.append("SUMMARY:" + ics_esc(ev["summary"]))
        if ev.get("location"):
            out.append("LOCATION:" + ics_esc(ev["location"]))
        if ev.get("desc"):
            out.append("DESCRIPTION:" + ics_esc(ev["desc"]))
        out.append("STATUS:" + ev.get("status", "CONFIRMED"))
        if ev.get("alarm"):
            out += [
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                "DESCRIPTION:Reminder",
                f"TRIGGER:-{ev['alarm']}",
                "END:VALARM",
            ]
        out.append("END:VEVENT")
    out.append("END:VCALENDAR")
    return "\r\n".join(fold(x) for x in out) + "\r\n"


def vcard(c):
    out = ["BEGIN:VCARD", "VERSION:3.0", f"N:{c['n']}", f"FN:{c['fn']}"]
    for key in ("nickname", "org", "title"):
        if c.get(key):
            out.append(f"{key.upper()}:{c[key]}")
    for kind, tel in c.get("tel", []):
        out.append(f"TEL;TYPE={kind}:{tel}")
    if c.get("email"):
        out.append(f"EMAIL;TYPE=INTERNET:{c['email']}")
    if c.get("adr"):
        out.append(f"ADR;TYPE=HOME:{c['adr']}")
    if c.get("bday"):
        out.append(f"BDAY:{c['bday']}")
    if c.get("note"):
        out.append("NOTE:" + ics_esc(c["note"]))
    out.append("END:VCARD")
    return "\r\n".join(fold(x) for x in out) + "\r\n"


# ================================================================ content

CONTACTS = [
    dict(
        n="Halloran;Gerald;Patrick;;",
        fn="Gerry Halloran",
        nickname="Gerry",
        tel=[("CELL", "+61 417 338 205")],
        email="gerryhalloran@bigpond.com",
        adr=";;27 Kellett Street;Lake Wendouree;VIC;3350;Australia",
        bday="1955-08-02",
        note="my husband. Lakeside member no. on the fridge",
    ),
    dict(
        n="Pettit;Siobhán;;;",
        fn="Siobhán Pettit",
        nickname="Shiv",
        tel=[("CELL", "+61 422 901 776")],
        email="siobhan.pettit@gmail.com",
        adr=";;8 Wattle Grove;Brunswick West;VIC;3055;Australia",
        bday="1985-07-19",
    ),
    dict(
        n="Pettit;Tim;;;",
        fn="Tim Pettit",
        tel=[("CELL", "+61 433 120 948")],
        email="tim.pettit@pettitadvisory.com.au",
        org="Pettit Advisory",
        note="Siobhan's Tim",
    ),
    dict(
        n="Pettit;Aoife;;;",
        fn="Aoife Pettit",
        tel=[("CELL", "+61 451 664 203")],
        email="aoife.pettit@student.monash.edu",
        bday="2005-12-12",
        note="granddaughter. Pharmacy at Monash",
    ),
    dict(
        n="Pettit;Kieran;;;",
        fn="Kieran Pettit",
        tel=[("CELL", "+61 468 207 551")],
        email="kpettit07@gmail.com",
        bday="2007-03-02",
        note="grandson - lives with us. Telegram not WhatsApp!",
    ),
    dict(
        n="Halloran;Declan;;;",
        fn="Declan Halloran",
        tel=[("CELL", "+61 409 554 018")],
        email="dec.halloran@outlook.com",
        adr=";;14 Cygnet Way;Fremantle;WA;6160;Australia",
        bday="1988-01-26",
    ),
    dict(
        n="Menon;Raj;;;",
        fn="Raj Menon",
        tel=[("CELL", "+61 410 772 391")],
        note="Declan's partner",
    ),
    dict(
        n="Murphy;Colleen;;;",
        fn="Colleen Murphy",
        tel=[("CELL", "+353 87 241 9930")],
        email="colleenmurphy.ennis@eircom.net",
        adr=";;Cloughleigh Road;Ennis;Co. Clare;V95;Ireland",
        bday="1956-09-08",
        note="my sister",
    ),
    dict(
        n="Considine;Brendan;;;",
        fn="Brendan Considine",
        tel=[("CELL", "+353 86 330 7714")],
        email="bconsidine.lahinch@gmail.com",
        note="cousin, Lahinch. family history",
    ),
    dict(
        n="Doyle;Margaret;;;",
        fn="Mags Doyle",
        nickname="Mags",
        tel=[("CELL", "+61 427 115 860"), ("HOME", "(03) 5339 2207")],
        email="magsdoyle57@bigpond.com",
        adr=";;5 Hertford Street;Sebastopol;VIC;3356;Australia",
        bday="1957-10-30",
    ),
    dict(
        n="Doyle;Terry;;;",
        fn="Terry Doyle",
        tel=[("CELL", "+61 427 115 861")],
        note="Mags's husband",
    ),
    dict(
        n="Brennan;Aoife;;;",
        fn="Aoife Brennan",
        tel=[("CELL", "+61 438 006 512")],
        email="aoife.brennan@iinet.net.au",
        bday="1958-12-03",
        note="bowls - afternoon tea roster",
    ),
    dict(
        n="Kinnane;Pat;;;",
        fn="Pat Kinnane",
        title="President WPBC",
        tel=[("CELL", "+61 419 881 230")],
        email="pat.kinnane@wpbc.org.au",
    ),
    dict(
        n="Walsh;Noreen;;;",
        fn="Noreen Walsh",
        tel=[("CELL", "+61 403 225 117")],
        note="bowls skip",
    ),
    dict(
        n="Lyle;Heather;;;",
        fn="Heather Lyle",
        org="Friends of Ballarat Botanical Gardens",
        tel=[("CELL", "+61 412 090 334")],
        email="heather.lyle@fobbg.org.au",
        note="seed bank coordinator",
    ),
    dict(
        n="Tolley;Hamish;;Dr;",
        fn="Dr Hamish Tolley",
        org="Ballarat Family Medical Centre",
        tel=[("WORK", "(03) 5332 6110")],
    ),
    dict(
        n="Rao;Anjali;;Dr;",
        fn="Dr Anjali Rao",
        org="Lydiard Dermatology",
        tel=[("WORK", "(03) 5331 8842")],
        note="22 Lydiard St North",
    ),
    dict(
        n="Nair;Priya;;Dr;",
        fn="Dr Priya Nair",
        org="Ballarat Endocrine",
        tel=[("WORK", "(03) 5320 4471")],
        note="Gerry's diabetes specialist",
    ),
    dict(
        n="Pollard;Craig;;;",
        fn="Craig Pollard",
        org="Ballarat Roof Restorations",
        tel=[("CELL", "0418 552 907")],
        email="craig@ballaratroofrestorations.com.au",
    ),
    dict(
        n="Vukovic;Leanne;;;",
        fn="Leanne Vukovic",
        org="Corio Bay Property Management",
        tel=[("WORK", "(03) 5229 4180")],
        email="leanne@coriobaypm.com.au",
        note="manages Weller St unit",
    ),
    dict(
        n=";;;;",
        fn="Lakeside Health Fund",
        org="Lakeside Health Fund",
        tel=[("WORK", "1300 525 334")],
        note="member LH-5520913",
    ),
    dict(
        n=";;;;",
        fn="Sturt Street Jewellers",
        org="Sturt Street Jewellers",
        tel=[("WORK", "(03) 5331 2675")],
        email="info@sturtstjewellers.com.au",
        note="Dimitri",
    ),
    dict(
        n="Ferris;Joan;;;",
        fn="Joan Ferris",
        tel=[("HOME", "(03) 5334 1902")],
        note="next door, no. 29. has our spare key",
    ),
    dict(
        n=";;;;",
        fn="Wendouree Auto",
        org="Wendouree Auto",
        tel=[("WORK", "(03) 5339 4410")],
        note="Kevin",
    ),
    dict(
        n="Hehir;Father Liam;;;",
        fn="Fr Liam Hehir",
        org="St Patrick's Cathedral",
        tel=[("WORK", "(03) 5331 2611")],
    ),
]


def build_contacts():
    cards = sorted(CONTACTS, key=lambda c: c["fn"])
    put("Contacts/contacts.vcf", "".join(vcard(c) for c in cards))
    mags = [c for c in CONTACTS if c["fn"] == "Mags Doyle"][0]
    put("Mail/Attachments/Mags Doyle.vcf", vcard(mags))


# ---------------------------------------------------------------- calendar


def build_calendar():
    ev = []
    D = datetime
    ev.append(
        dict(
            summary="Bowls (social)",
            start=D(2022, 1, 4, 13, 0),
            end=D(2022, 1, 4, 16, 30),
            rrule="FREQ=WEEKLY;BYDAY=TU",
            location="Wendouree Park Bowls Club",
            exdates=[D(2023, 5, 2 + 7 * k, 13, 0) for k in range(4)],
        )
    )
    ev.append(
        dict(
            summary="Seed bank – Friends of the Gardens",
            start=D(2022, 2, 3, 9, 30),
            end=D(2022, 2, 3, 12, 0),
            rrule="FREQ=WEEKLY;INTERVAL=2;BYDAY=TH",
            location="Ballarat Botanical Gardens, Robert Clark Centre",
        )
    )
    ev.append(
        dict(
            summary="Coffee w Mags",
            start=D(2023, 3, 1, 10, 30),
            end=D(2023, 3, 1, 11, 30),
            rrule="FREQ=WEEKLY;INTERVAL=2;BYDAY=WE;UNTIL=20260601T000000Z",
            location="Gardens kiosk",
        )
    )
    ev.append(
        dict(
            summary="Gerry – Men's Shed",
            start=D(2022, 1, 3, 9, 0),
            end=D(2022, 1, 3, 12, 0),
            rrule="FREQ=WEEKLY;BYDAY=MO",
        )
    )
    ev.append(
        dict(
            summary="WPBC committee meeting",
            start=D(2022, 1, 11, 19, 0),
            end=D(2022, 1, 11, 21, 0),
            rrule="FREQ=MONTHLY;BYDAY=2TU",
            location="Clubrooms",
        )
    )
    ev.append(
        dict(
            summary="Bins – recycling",
            start=D(2022, 1, 2, 19, 0),
            rrule="FREQ=WEEKLY;INTERVAL=2;BYDAY=SU",
        )
    )
    ev.append(
        dict(
            summary="Car rego due",
            start=date(2022, 11, 3),
            rrule="FREQ=YEARLY",
            alarm="P7D",
            desc="Forester 1XY4KD - renew online before 3 Nov",
        )
    )
    for name, bday in [
        ("Gerry's birthday", date(2022, 8, 2)),
        ("Siobhán's birthday", date(2022, 7, 19)),
        ("Declan's birthday", date(2022, 1, 26)),
        ("Aoife's birthday", date(2022, 12, 12)),
        ("Kieran's birthday", date(2022, 3, 2)),
        ("Colleen's birthday", date(2022, 9, 8)),
        ("Mags's birthday", date(2022, 10, 30)),
        ("Aoife B bday (bowls)", date(2022, 12, 3)),
    ]:
        ev.append(dict(summary=name, start=bday, rrule="FREQ=YEARLY"))
    ev.append(
        dict(
            summary="Ireland!! (Colleen's)",
            start=date(2023, 5, 2),
            end=date(2023, 5, 31),
            desc="QF from Melb 2/5 via Dubai. Back 30th",
        )
    )
    ev.append(
        dict(
            summary="Perth – Declan & Raj",
            start=date(2025, 3, 6),
            end=date(2025, 3, 14),
        )
    )
    for y, m, d in [
        (2022, 5, 10),
        (2022, 11, 8),
        (2023, 5, 16),
        (2023, 11, 14),
        (2024, 5, 14),
        (2024, 11, 12),
        (2025, 5, 13),
        (2025, 11, 11),
        (2026, 5, 12),
        (2026, 11, 10),
    ]:
        ev.append(
            dict(
                summary="Gerry – Dr Nair (diabetes)",
                start=D(y, m, d, 14, 0),
                location="Ballarat Endocrine, Drummond St North",
                desc="bring sugar diary + bloods",
            )
        )
    for y in range(2022, 2027):
        ev.append(
            dict(
                summary="Flu shots both",
                start=D(y, 4, 20 + (y % 3), 10, 0),
                location="Chemist Warehouse",
            )
        )
        ev.append(dict(summary="Christmas at Siobhán's", start=date(y, 12, 25)))
    ev.append(
        dict(
            summary="Gerry – podiatrist",
            start=D(2026, 10, 8, 11, 0),
            location="Ballarat Foot Clinic",
        )
    )
    ev.append(
        dict(
            summary="GP – Dr Tolley (knee + spot on leg)",
            start=D(2026, 2, 11, 10, 15),
            location="Ballarat Family Medical",
        )
    )
    ev.append(
        dict(
            summary="Dr Rao - skin check",
            start=D(2026, 8, 19, 10, 30),
            location="Lydiard Dermatology",
            status="CANCELLED",
            desc="cancelled - pennant final moved to Wed. REBOOK",
        )
    )
    ev.append(
        dict(
            summary="Dermatology – Dr Rao",
            start=D(2026, 11, 5, 9, 15),
            location="Lydiard Dermatology, 22 Lydiard St Nth",
            desc="booked 20/8 by phone. bring referral",
            alarm="P1D",
        )
    )
    ev.append(
        dict(
            summary="Midweek pennant FINAL v Buninyong",
            start=D(2026, 8, 19, 10, 0),
            end=D(2026, 8, 19, 15, 0),
            location="Wendouree Park Bowls Club",
        )
    )
    ev.append(dict(summary="Roofer (Craig) – look at leak", start=D(2026, 5, 14, 8, 0)))
    ev.append(
        dict(
            summary="Roof inspection – Ballarat Roof Restorations",
            start=D(2025, 7, 15, 8, 0),
            status="CANCELLED",
            desc="Gerry says he'll do it himself",
        )
    )
    ev.append(
        dict(
            summary="Terry Doyle funeral",
            start=D(2026, 6, 16, 11, 0),
            end=D(2026, 6, 16, 13, 0),
            location="St Patrick's Cathedral, Sturt St",
        )
    )
    ev.append(
        dict(
            summary="Lunch with Mags (her birthday)",
            start=D(2025, 10, 30, 12, 0),
            location="The Forge Pizzeria",
        )
    )
    ev.append(
        dict(
            summary="Lunch with Mags (her birthday)",
            start=D(2024, 10, 30, 12, 0),
            location="Webster's Market",
        )
    )
    ev.append(dict(summary="TAX DUE (self lodge)", start=date(2025, 10, 31)))
    ev.append(
        dict(
            summary="TAX DUE (self lodge)",
            start=date(2026, 10, 31),
            alarm="P14D",
            desc="myGov. rental schedule!!",
        )
    )
    ev.append(
        dict(
            summary="Aoife's 21st – Lake View Hotel",
            start=D(2026, 12, 12, 18, 0),
            end=D(2026, 12, 12, 23, 0),
            location="Lake View Hotel, Wendouree",
        )
    )
    ev.append(dict(summary="Car service – Wendouree Auto", start=D(2026, 9, 3, 8, 0)))
    ev.append(dict(summary="WPBC AGM", start=D(2025, 7, 27, 14, 0)))
    ev.append(
        dict(summary="Kieran exams", start=date(2026, 11, 2), end=date(2026, 11, 21))
    )
    ev.append(dict(summary="Bowls opening day 2026-27", start=D(2026, 10, 17, 12, 0)))
    ev.sort(key=lambda e: (str(e["start"]), e["summary"]))
    put("Calendar/Home.ics", ics("Home", ev, "-//Apple Inc.//macOS 14.6//EN"))

    fx = []
    opponents = [
        "Sebastopol",
        "Buninyong",
        "Ballarat North",
        "Learmonth",
        "Creswick",
        "Victoria Bowls",
        "Clunes",
        "Ballarat East",
    ]
    d = D(2026, 10, 17, 13, 0)
    for i in range(16):
        opp = opponents[i % len(opponents)]
        home = "H" if i % 2 == 0 else "A"
        fx.append(
            dict(
                summary=f"Pennant Div 3: WPBC v {opp} ({home})",
                start=d,
                end=d + timedelta(hours=4),
                desc="Rink 2: B Halloran (S), N Walsh, A Brennan, J Ferris",
            )
        )
        d += timedelta(days=7 if i != 9 else 21)
    put(
        "Calendar/WPBC Pennant 2026-27.ics",
        ics("WPBC Pennant", fx, "-//Google Inc//Google Calendar 70.9054//EN"),
    )


# ---------------------------------------------------------------- bank

PREMIUMS = [
    ((2022, 1), 368.20),
    ((2022, 4), 375.40),
    ((2023, 4), 381.95),
    ((2024, 4), 396.10),
    ((2025, 4), 404.60),
    ((2026, 4), 412.85),
]
REGO = {2022: 789.40, 2023: 812.60, 2024: 846.30, 2025: 874.10}
REGO_PAID = {2022: 27, 2023: 31, 2024: 30, 2025: 29}
FY26_WEEKS = [5, 4, 4, 5, 4, 4, 5, 4, 4, 5, 4, 4]  # Jul 2025 .. Jun 2026
WEEKLY_RENT = {2021: 370, 2022: 385, 2023: 400, 2024: 405, 2025: 420, 2026: 435}


def premium_for(d):
    val = PREMIUMS[0][1]
    for (y, m), p in PREMIUMS:
        if (d.year, d.month) >= (y, m):
            val = p
    return val


def origin_table(rng):
    t = {}
    for y in range(2022, 2027):
        for m in (1, 4, 7, 10):
            lo, hi = {1: (360, 450), 4: (390, 480), 7: (610, 740), 10: (540, 660)}[m]
            t[(y, m)] = round(rng.uniform(lo, hi), 2)
    return t


def fy_of(d):
    return d.year if d.month >= 7 else d.year - 1


def rent_disbursement(d):
    """Corio Bay pays out on the 5th for the previous month."""
    prev = d.replace(day=1) - timedelta(days=1)
    fy = fy_of(prev)
    if fy == 2025:
        weeks = FY26_WEEKS[(prev.month - 7) % 12]
        rent = weeks * 420
        fee = round(rent * 0.075, 2)
        extra = {(2025, 9): 186.50, (2026, 2): 1980.00}.get((prev.year, prev.month), 0)
        return round(rent - fee - extra, 2)
    rent = WEEKLY_RENT[fy] * 52 / 12
    return round(rent * 0.925, 2)


def build_bank(rng, origin):
    rows = []
    d = date(2022, 1, 1)
    end = date(2026, 10, 23)
    bpens, gpens = 2840.00, 3120.00
    while d <= end:
        if d.month == 7 and d.day == 1:
            bpens = round(bpens * 1.03, 2)
            gpens = round(gpens * 1.03, 2)
        if d.day == 15:
            rows.append((d, bpens, "AUSPRIME SUPER PENSION B M HALLORAN"))
            rows.append((d, gpens, "AUSPRIME SUPER PENSION G P HALLORAN"))
        if d.day == 16:
            rows.append((d, -4000.00, "TRANSFER TO XX4471 NETBANK SAVER"))
        if d.day == 2:
            tel = 89.00 if d < date(2024, 7, 1) else 95.00
            rows.append((d, -tel, "TELSTRA DIRECT DEBIT 3302948817"))
        if d.day == 21:
            nf = 16.99 if d < date(2024, 3, 1) else 18.99
            rows.append((d, -nf, "NETFLIX.COM MELBOURNE AU"))
        if d.day == 28 and d <= date(2026, 7, 28):
            rows.append((d, -premium_for(d), "LAKESIDE HEALTH PREMIUM LH-5520913"))
        if d.day == 5:
            rows.append((d, rent_disbursement(d), "CORIO BAY PM OWNER DISB HALLORAN"))
        if d.day == 25 and d.month in (1, 4, 7, 10):
            rows.append((d, -origin[(d.year, d.month)], "BPAY ORIGIN ENERGY 6631094"))
        if d.day == 15 and d.month in (2, 5, 9, 11):
            rows.append(
                (
                    d,
                    -612.40 if d.year < 2025 else -648.15,
                    "BPAY CITY OF BALLARAT RATES",
                )
            )
        if d.month == 10 and d.year in REGO_PAID and d.day == REGO_PAID[d.year]:
            rows.append((d, -REGO[d.year], "VICROADS REGO 1XY4KD"))
        if d.month == 9 and d.day == 12:
            rows.append((d, -285.00, "WENDOUREE PARK BOWLS CLUB SUBS"))
        if d >= date(2025, 2, 7) and d.weekday() == 4:
            rows.append((d, 100.00, "TRANSFER FROM K PETTIT BOARD"))
        if d.weekday() == 3:
            rows.append(
                (d, -round(rng.uniform(112, 246), 2), "WOOLWORTHS 3350 WENDOUREE AU")
            )
        if d.weekday() == 0 and rng.random() < 0.5:
            rows.append((d, -round(rng.uniform(38, 92), 2), "ALDI STORES BALLARAT AU"))
        if rng.random() < 0.09:
            rows.append((d, -round(rng.uniform(55, 92), 2), "AMPOL WENDOUREE 3350 AU"))
        if rng.random() < 0.06:
            rows.append((d, -round(rng.uniform(9, 28), 2), "GARDENS KIOSK BALLARAT"))
        if d.day == 10:
            rows.append(
                (d, -round(rng.uniform(18, 75), 2), "CHEMIST WAREHOUSE BALLARAT AU")
            )
        if rng.random() < 0.025:
            rows.append(
                (d, -round(rng.uniform(24, 160), 2), "BUNNINGS 382000 WENDOUREE")
            )
        d += timedelta(days=1)
    rows += [
        (date(2024, 5, 6), -1212.40, "INTL TT EUR725.00 C MURPHY ENNIS IE"),
        (date(2025, 11, 14), 642.18, "ATO TAX REFUND 2025"),
        (date(2024, 11, 19), 1180.55, "ATO TAX REFUND 2024"),
        (date(2026, 8, 7), -219.99, "JBHIFI-ONLINE SYDNEY AU"),
        (date(2026, 8, 12), 219.99, "DISPUTE CREDIT REF 88412"),
        (date(2025, 3, 2), -1147.80, "QANTAS AIRWAYS MELB-PER"),
        (date(2023, 3, 20), -3420.00, "EMIRATES MEL-DUB-DUB"),
        (date(2025, 6, 18), -402.00, "LAKEVIEW PLUMBING BALLARAT"),
    ]
    rows.sort(key=lambda r: (r[0], r[2]))
    bal = 18420.55
    with_bal = []
    for d, amt, desc in rows:
        bal = round(bal + amt, 2)
        with_bal.append((d, amt, desc, bal))
    by_fy = {}
    for r in with_bal:
        by_fy.setdefault(fy_of(r[0]), []).append(r)
    for fy in sorted(by_fy):
        lines = [
            f'{d:%d/%m/%Y},"{amt:+.2f}","{desc}","{bal:+.2f}"'
            for d, amt, desc, bal in reversed(by_fy[fy])
        ]
        put(
            f"Bank/CommBank_SmartAccess_FY{fy}-{(fy + 1) % 100:02d}.csv",
            "\r\n".join(lines) + "\r\n",
        )


# ---------------------------------------------------------------- emails


def build_key_emails(origin):
    # N1 / T2: rego notices
    for y, amt, ref in [
        (2024, "$846.30", "4410 1876 2213"),
        (2025, "$874.10", "4410 2034 5518"),
        (2026, "$912.40", "4410 2287 9935"),
    ]:
        mail(
            "Inbox",
            "VicRoads <noreply@vicroads.vic.gov.au>",
            ME,
            "Registration renewal notice – SUBARU FORESTER 1XY4KD",
            at(y, 10, 6 if y == 2026 else 7, 6, 12),
            "Dear BERNADETTE M HALLORAN,\n\nYour vehicle registration is due for "
            f"renewal.\n\nVehicle: 2017 SUBARU FORESTER WAGON\nRegistration number: "
            f"1XY4KD\nRegistration expiry: 03/11/{y}\nAmount payable (12 months): "
            f"{amt}\nRenewal reference: {ref}\n\nRenew online at vicroads.vic.gov.au or"
            " in the myVicRoads app. If you do not renew by the expiry date your "
            "registration will lapse and the vehicle must not be driven on a road.\n\n"
            "This is an automated message, please do not reply.\nVicRoads",
            html_alt=True,
        )
    # N3: card replaced, insurer arrears
    mail(
        "Inbox",
        "CommBank <NetBankNotification@cba.com.au>",
        ME,
        "We've replaced your card",
        at(2026, 8, 8, 16, 41),
        "Hi Bernadette,\n\nWe've noticed some unusual activity and have cancelled your "
        "Debit Mastercard ending 7731 to protect your account.\n\nA replacement card "
        "ending 0458 will arrive by post in 5–7 business days.\n\nImportant: remember "
        "to update any recurring payments linked to your old card (subscriptions, "
        "insurance, utilities). Payments to the old card number will be declined.\n\n"
        "If you didn't make the transaction of $219.99 at JBHIFI-ONLINE we'll be in "
        "touch about a refund.\n\nCommonwealth Bank",
        html_alt=True,
    )
    lake = "Lakeside Health Fund <members@lakesidehealth.com.au>"
    for y, old, new in [
        (2024, "381.95", "396.10"),
        (2025, "396.10", "404.60"),
        (2026, "404.60", "412.85"),
    ]:
        mail(
            "Inbox",
            lake,
            ME,
            f"Your premium from 1 April {y}",
            at(y, 3, 3, 9, 0),
            "Dear Bernadette,\n\nEach year private health insurers adjust premiums. "
            f"From 1 April {y} your monthly premium for Couples Gold Hospital & Top "
            f"Extras will be ${new} (previously ${old}).\n\nYour premium will continue "
            "to be debited from your nominated card on the 28th of each month.\n\n"
            "Membership: LH-5520913\nLakeside Health Fund",
            html_alt=True,
        )
    mail(
        "Inbox",
        lake,
        ME,
        "We couldn't process your premium payment",
        at(2026, 9, 1, 8, 2),
        "Hi Bernadette,\n\nWe were unable to process your premium payment of $412.85 "
        "due 28/08/2026 from the card ending 7731 (card declined).\n\nPlease update "
        "your payment details in the Lakeside app or call us on 1300 525 334.\n\n"
        "Membership: LH-5520913\nLakeside Health Fund",
    )
    mail(
        "Inbox",
        lake,
        ME,
        "Your Lakeside Health policy is in arrears",
        at(2026, 10, 1, 8, 4),
        "Hi Bernadette,\n\nTwo premiums of $412.85 (total $825.70) remain unpaid. Your "
        "cover is currently paid to 28/07/2026.\n\nClaims for services after this date "
        "will be held until your arrears are cleared. Please call 1300 525 334 or "
        "update your card in the app.\n\nMembership: LH-5520913\nLakeside Health Fund",
        html_alt=True,
    )
    mail(
        "Inbox",
        lake,
        ME,
        "FINAL NOTICE – policy suspension LH-5520913",
        at(2026, 10, 22, 8, 1),
        "Dear Mrs Halloran,\n\nYour policy LH-5520913 (Couples Gold Hospital & Top "
        "Extras) is now 86 days in arrears.\n\nAmount required to bring your cover to "
        "28/10/2026: $1,238.55\n\nIf this amount is not paid by 14 November 2026 your "
        "cover will be suspended. While your policy is suspended you and Gerald "
        "Halloran are not covered for hospital or extras, and waiting periods may "
        "apply when cover resumes.\n\nThe card ending 7731 on your account is no "
        "longer valid. Pay now in the Lakeside app or call 1300 525 334 "
        "(Mon–Fri 8am–6pm).\n\nLakeside Health Fund – Member Services",
        html_alt=True,
        qp=True,
    )
    # N2 / T3: dermatology
    derm = "Lydiard Dermatology <reception@lydiarddermatology.com.au>"
    mail(
        "Inbox",
        derm,
        ME,
        "Appointment confirmation – Lydiard Dermatology",
        at(2026, 8, 20, 11, 37),
        "Dear Bernadette,\n\nThis confirms your appointment with Dr Anjali Rao on "
        "Thursday 5 November 2026 at 9:15am.\n\nPlease bring your referral and Medicare"
        " card. A $95 fee applies to cancellations with less than 48 hours' notice.\n\n"
        "Lydiard Dermatology\n22 Lydiard Street North, Ballarat\n(03) 5331 8842",
    )
    mail(
        "Inbox",
        derm,
        ME,
        "Your appointment has been cancelled",
        at(2026, 10, 2, 15, 20),
        "Dear Bernadette,\n\nWe regret that Dr Anjali Rao is on unexpected leave. Your "
        "appointment on Thursday 5 November 2026 at 9:15am has been cancelled.\n\n"
        "Please call us on (03) 5331 8842 to rebook with Dr Rao (from January) or "
        "with Dr Feeney, who has appointments in November.\n\nWe apologise for the "
        "inconvenience.\nLydiard Dermatology",
        html_alt=True,
    )
    # N5: ring promise + jeweller
    mail(
        "Sent",
        ME,
        SIOBHAN,
        "Happy 17th to our Aoife!",
        at(2022, 12, 12, 20, 14),
        "Shiv love,\n\nHappy birthday to our girl — 17! Tell her the card is in the "
        "post, Australia Post willing.\n\nI said it to Aoife on the phone and I'm "
        "saying it to you so it's written down somewhere: when she turns 21 she'll "
        "have Mum's engagement ring — Nana Peg's sapphire. Mum would have wanted it "
        "with a girl who'll wear it, not in a drawer. I promise.\n\nDad says happy "
        "birthday and to stop growing.\n\nLove,\nMum xx",
        mailer="Microsoft Outlook 16.0",
    )
    mail(
        "Inbox",
        "Sturt Street Jewellers <info@sturtstjewellers.com.au>",
        ME,
        "Re: enquiry - sapphire ring claws",
        at(2026, 3, 9, 14, 3),
        "Hi Bernie,\n\nThanks for your enquiry. Re-tipping all four claws and sizing the "
        "band down from N to K would be approx $285 and takes 4–6 weeks (allow longer"
        " from November with the Christmas rush). No appointment needed, just drop it"
        " in and we'll write you a docket.\n\nWarm regards,\nDimitri\nSturt Street "
        "Jewellers\n\n> Hello, I have my late mother's sapphire engagement ring. One "
        "claw\n> is lifting and the stone moves. I'd also like it made smaller for my\n"
        "> granddaughter (size K I think). How long would that take?\n> Bernie "
        "Halloran",
    )
    # N6 / T1 / T4: tax and rental
    eofy = eofy_pdf()
    mail(
        "Inbox",
        "Leanne Vukovic <leanne@coriobaypm.com.au>",
        ME,
        "EOFY owner statement – 2/41 Weller St",
        at(2026, 7, 14, 10, 26),
        "Hi Bernie and Gerry,\n\nPlease find attached your end of financial year "
        "statement for 2/41 Weller Street, Geelong West (1 July 2025 – 30 June 2026)."
        "\n\nGross rent received $21,840.00. Expenses included the smoke alarm "
        "service and the hot water service replacement in February.\n\nNote we don't "
        "hold the depreciation schedule - your accountant or the original quantity "
        "surveyor report should have it.\n\nKind regards,\nLeanne Vukovic\nCorio Bay "
        "Property Management",
        attach=("CorioBay_EOFY_2025-26_Halloran.pdf", "application/pdf", eofy),
    )
    mail(
        "Inbox",
        "Leanne Vukovic <leanne@coriobaypm.com.au>",
        ME,
        "EOFY owner statement – 2/41 Weller St",
        at(2025, 7, 11, 9, 50),
        "Hi Bernie and Gerry,\n\nAttached (well, linked in the owner portal) is your "
        "EOFY statement for 2024-25. Gross rent received $21,060.00.\n\nRent review: "
        "we've agreed $420/wk with the tenants from 1 July.\n\nKind regards,\nLeanne",
    )
    mail(
        "Inbox",
        "Leanne Vukovic <leanne@coriobaypm.com.au>",
        ME,
        "Routine inspection – 2/41 Weller St",
        at(2026, 4, 22, 13, 5),
        "Hi Bernie,\n\nRoutine inspection done today. Tenants (the Nguyens) are keeping "
        "it beautifully. New hot water service working well. Minor: bathroom exhaust "
        "fan noisy, and the side gate latch.\n\nLeanne",
    )
    mail(
        "Inbox",
        "Australian Taxation Office <no-reply@ato-gov-au-refund.com>",
        ME,
        "ATO: You have a pending tax refund of $1,284.60",
        at(2026, 10, 15, 3, 44),
        "Dear Taxpayer,\n\nAfter the last annual calculation of your fiscal activity we "
        "have determined that you are eligible to receive a tax refund of $1,284.60."
        "\n\nPlease submit the tax refund request and allow us 3-5 business days to "
        "process it.\n\nVerify your details here: http://ato-gov-au-refund.com/claim?"
        "id=88213\n\nFailure to verify within 48 hours will result in forfeiture of "
        "your refund.\n\nAustralian Taxation Office\n© 2026 Commonwealth of Australia",
        html_alt=True,
    )
    mail(
        "Inbox",
        "myGov <noreply@my.gov.au>",
        ME,
        "You have a new message in your myGov Inbox",
        at(2026, 7, 3, 7, 30),
        "You have a new message in your myGov Inbox from the Australian Taxation "
        "Office.\n\nSign in to myGov to read it. We will never send you a link to sign "
        "in.\n\nmyGov",
    )
    mail(
        "Inbox",
        "Australia Post <tracking@auspost-redelivery.info>",
        ME,
        "Your parcel could not be delivered",
        at(2025, 11, 20, 2, 10),
        "We attempted to deliver your parcel but no one was home. A $2.99 redelivery "
        "fee applies. Pay now: http://auspost-redelivery.info/pay\n\nAustralia Post",
    )
    # N7: roof
    mail(
        "Inbox",
        "Craig Pollard <craig@ballaratroofrestorations.com.au>",
        ME,
        "Quote Q-2291 – 27 Kellett St",
        at(2026, 5, 20, 17, 48),
        "Hi Bernie and Gerry,\n\nThanks for having me out Thursday. As discussed, the "
        "valley flashing above the back bedroom has rusted through and the ridge "
        "capping needs re-bedding and pointing.\n\nQuote Q-2291\n- Replace valley iron "
        "(approx 6m, Colorbond to match): $1,420.00\n- Re-bed and point ridge capping "
        "(14m): $930.00\nTotal: $2,350.00 inc GST\n\nThis quote is valid 30 days. "
        "Honestly if it's left over another winter you'll likely see the ceiling "
        "plaster go in that room, and that's a bigger job.\n\nCheers,\nCraig Pollard\n"
        "Ballarat Roof Restorations 0418 552 907",
        qp=True,
    )
    mail(
        "Inbox",
        "RACV Insurance <noreply@racv.com.au>",
        ME,
        "Your Home Insurance renewal",
        at(2026, 2, 18, 9, 0),
        "Dear Bernadette,\n\nYour RACV Home and Contents policy HC-7718203 renews on "
        "4 March 2026. Annual premium $2,184.60.\n\nPlease note: the policy does not "
        "cover damage caused by gradual deterioration, wear and tear, or water "
        "leaking over time. See section 4 of the PDS.\n\nRACV Insurance",
        html_alt=True,
    )


def eofy_pdf():
    lines = [
        ("B", 15, "Corio Bay Property Management"),
        (
            "R",
            9,
            "Shop 3, 112 Pakington Street, Geelong West VIC 3218   ABN 41 607 223 918",
        ),
        ("R", 9, ""),
        ("B", 12, "OWNER ANNUAL STATEMENT"),
        (
            "R",
            10,
            "Owners: B M & G P Halloran, 27 Kellett Street, Lake Wendouree VIC 3350",
        ),
        ("R", 10, "Property: 2/41 Weller Street, Geelong West VIC 3218"),
        ("R", 10, "Period: 01/07/2025 to 30/06/2026"),
        ("R", 10, ""),
        ("B", 11, "INCOME"),
        ("R", 10, "Rent received (52 weeks @ $420.00)                    21,840.00"),
        ("R", 10, "Total income                                          21,840.00"),
        ("R", 10, ""),
        ("B", 11, "EXPENDITURE"),
        ("R", 10, "Management fee 7.5%                                    1,638.00"),
        ("R", 10, "Smoke alarm annual service (Sep 2025)                    186.50"),
        ("R", 10, "Hot water service replacement, Geelong Plumbing #5102  1,980.00"),
        ("R", 10, "Total expenditure                                      3,804.50"),
        ("R", 10, ""),
        ("B", 11, "NET PAID TO OWNER                                     18,035.50"),
        ("R", 10, "Disbursed monthly to CBA account ending 4419"),
        ("R", 10, ""),
        (
            "R",
            8,
            "Council rates, water and landlord insurance are paid by the owner and",
        ),
        (
            "R",
            8,
            "are not included in this statement. Please retain for taxation purposes.",
        ),
        ("R", 8, "Statement issued 14/07/2026."),
    ]
    return pdf(lines, "Owner Annual Statement 2025-26", "20260714102200+10'00'")


def referral_pdf():
    lines = [
        ("B", 14, "BALLARAT FAMILY MEDICAL CENTRE"),
        (
            "R",
            9,
            "804 Sturt Street, Ballarat VIC 3350   Ph (03) 5332 6110   Fax (03) 5332 6119",
        ),
        ("R", 10, ""),
        ("R", 10, "11 February 2026"),
        ("R", 10, ""),
        ("R", 10, "Dr Anjali Rao"),
        ("R", 10, "Dermatologist, Lydiard Dermatology"),
        ("R", 10, "22 Lydiard Street North, Ballarat VIC 3350"),
        ("R", 10, ""),
        ("R", 10, "Dear Dr Rao,"),
        ("R", 10, ""),
        ("B", 10, "Re: Mrs Bernadette HALLORAN   DOB 17/04/1959"),
        ("R", 10, "27 Kellett Street, Lake Wendouree VIC 3350   Medicare 2953 61847 1"),
        ("R", 10, ""),
        (
            "R",
            10,
            "Thank you for seeing this 66 year old retired ICU nurse with a pigmented",
        ),
        (
            "R",
            10,
            "lesion on the left calf, approx 7mm, irregular border and two-tone colour.",
        ),
        (
            "R",
            10,
            "She reports it has changed over the past year and is occasionally itchy.",
        ),
        (
            "R",
            10,
            "Dermoscopy: asymmetric with an atypical network. I am concerned and would",
        ),
        ("R", 10, "appreciate your assessment and excision if indicated."),
        ("R", 10, ""),
        (
            "R",
            10,
            "PMHx: osteoarthritis R knee; hypercholesterolaemia. Fair skin, many years",
        ),
        ("R", 10, "outdoors (lawn bowls). Medications: atorvastatin 20mg nocte. NKDA."),
        ("R", 10, ""),
        (
            "R",
            10,
            "If she has not been seen, I have asked her to return for review in 6 months.",
        ),
        ("R", 10, ""),
        ("R", 10, "Kind regards,"),
        ("R", 10, ""),
        ("R", 10, "Dr Hamish Tolley  MBBS FRACGP   Provider No. 2417736B"),
        ("R", 9, "cc: patient"),
    ]
    return pdf(lines, "Referral", "20260211110402+11'00'")


LIB_TITLES = [
    "The Rose Code",
    "Lessons in Chemistry",
    "Bournville",
    "The Dictionary of Lost Words",
    "Small Things Like These",
    "The Thursday Murder Club",
    "Cloudstreet",
    "The Bee Sting",
    "Demon Copperhead",
    "Tomorrow and Tomorrow and Tomorrow",
    "The Lost Flowers of Alice Hart",
    "Trust",
]

COLLEEN_MAILS = [
    (
        (2022, 3, 17, 21, 5),
        "Paddy's Day and Mam's stone",
        "Bernie,\n\nHappy Paddy's Day from a wet Ennis. Parade went ahead, the band from "
        "Kilrush were frozen.\n\nI was up at Drumcliff Sunday. Mam and Dad's headstone "
        "is badly faded, you can hardly read Dad's dates. Cronin's say re-lettering and "
        "a clean would be €1,450. Will we split it? No rush.\n\nLove to Gerry,\nColleen",
    ),
    (
        (2022, 9, 10, 19, 30),
        "Re: thanks for the birthday call",
        "Lovely to hear you, even with the delay on the line. 66! Don't say it.\n\n"
        "Cronin's say spring for the stone, they're backed up. Colleen",
    ),
    (
        (2023, 2, 14, 18, 2),
        "May!!",
        "Bernie, I can't believe you're actually coming. I've the back room done up. "
        "We'll do Lahinch and Brendan will bore you with the family tree. Bring a "
        "proper coat, it's not Australia.\nC x",
    ),
    (
        (2023, 6, 4, 20, 11),
        "The house is too quiet",
        "You were barely gone and I'd the kettle on for two. Thank you for coming. Mam "
        "would have loved seeing the two of us at the grave together, even arguing "
        "over the flowers.\nColleen",
    ),
    (
        (2024, 4, 22, 17, 45),
        "Stone done – photos",
        "It's done! Cronin's did a grand job, you can read every word. Photos attached "
        "(well, Siobhan says they never come through, I'll WhatsApp them). Your half "
        "is €725 when you're ready, no rush at all.\nC",
    ),
    (
        (2025, 1, 3, 12, 0),
        "Happy New Year",
        "Happy New Year to you all. Christmas was quiet, the Murphys came for the "
        "dinner and stayed till Stephen's Day. How is Gerry's sugar? And Kieran, is he "
        "still eating you out of house and home?\nColleen",
    ),
    (
        (2025, 8, 19, 22, 14),
        "Brendan and his DNA",
        "Brendan has the whole parish spitting into tubes. He says there's a "
        "Considine in Boston we never knew about. I'll leave him to tell you.\nC x",
    ),
    (
        (2026, 6, 10, 9, 20),
        "So sorry about Terry",
        "Bernie, Siobhan told me about Terry. I remember him at the barbecue when I "
        "visited, the size of him and the laugh. Give Mags my love. Mind yourself too.\n"
        "Colleen",
    ),
    (
        (2026, 9, 29, 21, 2),
        "Are you alright?",
        "You've gone very quiet. Siobhan says you're run off your feet. Ring me when "
        "you've a minute, I don't mind the hour.\nC x",
    ),
]

DECLAN_MAILS = [
    (
        (2023, 1, 9, 19, 2),
        "Perth?",
        "Mum, any chance you and Dad come over in March? "
        "Raj says we can do the Rottnest day. Dx",
    ),
    (
        (2025, 2, 2, 20, 40),
        "Flights",
        "Booked you on QF779 Thu 6 March, back on the "
        "13th. Don't argue, it's done. Dec",
    ),
    (
        (2025, 3, 15, 10, 5),
        "Thanks for coming",
        "Raj's mum loved meeting you. Dad still owes me a rematch at the pub. x",
    ),
    (
        (2026, 5, 3, 18, 30),
        "Raj's mum",
        "Quick one: Raj's mum is in hospital in "
        "Kochi, he's flying over. We're ok. Will call Sunday. Dec",
    ),
]

BRENDAN_MAILS = [
    (
        (2023, 8, 2, 11, 10),
        "1911 census – found them",
        "Bernie, found our grandfather Patrick in the 1911 census, Kilmurry Ibrickane, "
        "age 17, farm labourer, living with his widowed mother Honora. Spreadsheet "
        "attached-ish (I typed it out). Brendan",
    ),
    (
        (2024, 10, 14, 15, 30),
        "Kilrush workhouse",
        "The Kilrush Union minute books are digitised. There's a Considine family "
        "admitted 1849, Michael and five children. Could be ours, could be any of a "
        "hundred Considines. Brendan",
    ),
    (
        (2025, 8, 20, 9, 45),
        "DNA match in Boston",
        "Strong match with a Thomas Considine in Dorchester MA. Second cousin, they "
        "reckon. His great-grandfather left Miltown Malbay in 1888. B",
    ),
    (
        (2026, 4, 2, 20, 0),
        "The book",
        "How's the book going? You said the cousins would have it by Christmas. No "
        "pressure ;) B",
    ),
]


GENERA = [
    "Acacia",
    "Banksia",
    "Correa",
    "Eucalyptus",
    "Grevillea",
    "Hakea",
    "Leptospermum",
]


def build_filler_emails(rng, origin):
    for y, m in sorted(origin):
        if y < 2024 or (y, m) > (2026, 10):
            continue
        amt = origin[(y, m)]
        due = date(y, m, 25)
        mail(
            "Inbox",
            "Origin Energy <noreply@originenergy.com.au>",
            ME,
            "Your Origin bill is ready",
            at(y, m, 12, 6, 30),
            f"Hi Bernadette,\n\nYour electricity and gas bill for 27 Kellett St is "
            f"ready.\n\nAmount due: ${amt:,.2f}\nDue date: {due.day} {MONTHS[m - 1]} "
            f"{y}\nAccount: 6631094\n\nYou pay by BPAY. View your bill in the Origin "
            "app.\n\nOrigin Energy",
            html_alt=True,
        )
    picks = sorted(rng.sample(range(0, 1700), 8))
    for i, off in enumerate(picks):
        d = date(2022, 3, 1) + timedelta(days=off)
        title = LIB_TITLES[i % len(LIB_TITLES)]
        mail(
            "Inbox",
            "Ballarat Libraries <noreply@ballarat.vic.gov.au>",
            ME,
            "Your hold is ready to collect",
            at(d.year, d.month, d.day, 8, 15),
            f"Dear BERNADETTE HALLORAN,\n\nThe following item is ready for collection "
            f"at Ballarat Library, Camp Street:\n\n  {title}\n\nPlease collect by "
            f"{(d + timedelta(days=7)):%d/%m/%Y}.\n\nBallarat Libraries",
        )
    for i, off in enumerate(sorted(rng.sample(range(0, 1700), 7))):
        d = date(2022, 2, 1) + timedelta(days=off)
        mail(
            "Inbox",
            "Heather Lyle <heather.lyle@fobbg.org.au>",
            ME,
            "Seed bank roster",
            at(d.year, d.month, d.day, 19, 20),
            "Hi all,\n\nRoster for the next eight weeks is on the noticeboard. Bernie "
            "and Ted on alternate Thursdays as usual. We're cleaning "
            f"{GENERA[i]} seed this round.\n\nThanks,\nHeather",
        )
    for i, off in enumerate(sorted(rng.sample(range(0, 1700), 5))):
        d = date(2022, 2, 1) + timedelta(days=off)
        mail(
            "Inbox",
            "Chemist Warehouse <scripts@chemistwarehouse.com.au>",
            ME,
            "Prescription reminder",
            at(d.year, d.month, d.day, 10, 0),
            "Hi Bernadette,\n\nA repeat prescription for GERALD HALLORAN (metformin "
            "1000mg) is due for refill. Order online or in store.\n\nChemist "
            "Warehouse Ballarat",
        )
    for i, off in enumerate(sorted(rng.sample(range(0, 1600), 4))):
        d = date(2022, 6, 1) + timedelta(days=off)
        mail(
            "Inbox",
            "Ancestry <hints@ancestry.com.au>",
            ME,
            "New hints for Patrick Considine",
            at(d.year, d.month, d.day, 4, 0),
            f"You have {3 + i} new hints in Halloran-Considine Family Tree.\n\n"
            "Patrick Considine (1894-1961) - Ireland, Civil Registration Births\n\n"
            "Ancestry",
            html_alt=True,
        )
    for (y, m, d, h, mi), subj, body in COLLEEN_MAILS:
        mail("Inbox", COLLEEN, ME, subj, at(y, m, d, h, mi), body, qp=True)
    for (y, m, d, h, mi), subj, body in DECLAN_MAILS:
        mail("Inbox", DECLAN, ME, subj, at(y, m, d, h, mi), body)
    for (y, m, d, h, mi), subj, body in BRENDAN_MAILS:
        mail("Inbox", BRENDAN, ME, subj, at(y, m, d, h, mi), body)
    mail(
        "Sent",
        ME,
        COLLEEN,
        "Re: Stone done – photos",
        at(2024, 5, 6, 21, 30),
        "Colleen, sent the €725 today, should be there by Friday. The photos made me "
        "cry. Thank you for doing all the running around. B x",
    )
    mail(
        "Sent",
        ME,
        BRENDAN,
        "Re: The book",
        at(2026, 4, 5, 19, 12),
        "Chapter 3 nearly there — the workhouse one. Christmas is ambitious but I'll "
        "try. Bernie",
    )
    mail(
        "Inbox",
        SIOBHAN,
        ME,
        "Christmas roster",
        at(2024, 11, 18, 21, 0),
        "Mum — Christmas at ours again. You're on pudding and brandy butter, Dad's on "
        "not falling asleep before the pudding. Tim's doing the ham. S x",
    )
    mail(
        "Inbox",
        SIOBHAN,
        ME,
        "Photos from Christmas",
        at(2025, 12, 28, 10, 40),
        "Link to the album: https://photos.app.goo.gl/x8Kq2 — the one of Dad in the "
        "paper hat is going in the frame. S",
    )
    for i, (y, m, d) in enumerate([(2023, 9, 2), (2024, 11, 30), (2025, 10, 4)]):
        mail(
            "Inbox",
            "Bunnings <orders@bunnings.com.au>",
            ME,
            "Your Click & Collect order is ready",
            at(y, m, d, 11, 0),
            f"Order {770410 + i * 3311} is ready at Bunnings Wendouree. Bring your order "
            "confirmation and photo ID.",
            html_alt=True,
        )


def build_mbox(rng):
    agenda = [
        "Green maintenance quote",
        "Bar roster",
        "Raffle results",
        "Pennant selection",
        "New members",
        "Bowls Victoria levy",
        "Christmas break-up",
        "Clubroom heating",
        "Treasurer's report",
        "Grant application (shade sails)",
    ]
    d = date(2022, 2, 1)
    while d < date(2026, 10, 15):
        # second Tuesday of the month
        first = d.replace(day=1)
        tue = first + timedelta(days=(1 - first.weekday()) % 7 + 7)
        items = rng.sample(agenda, 3)
        mbox_add(
            ME,
            COMMITTEE,
            f"Committee meeting Tuesday {tue.day} {MONTHS[tue.month - 1]}",
            at(tue.year, tue.month, tue.day - 6, 20, rng.randrange(0, 59)),
            f"Hi all,\n\nCommittee meeting Tuesday {tue.day} {MONTHS[tue.month - 1]}, "
            "7pm in the clubrooms.\n\nAgenda:\n1. Minutes of last meeting\n"
            + "".join(f"{i}. {x}\n" for i, x in enumerate(items, 2))
            + "5. General business\n\nBernie\nHon. Secretary, WPBC",
        )
        m = d.month + 2
        d = date(d.year + (m - 1) // 12, (m - 1) % 12 + 1, 1)
    mbox_add(
        MAGS,
        ME,
        "Raffle",
        at(2024, 3, 6, 9, 12),
        "Bernie, I've the raffle tickets and the meat tray is sorted with Mick at "
        "the butcher. Terry will drive me down Saturday. Mags",
    )
    mbox_add(
        MAGS,
        ME,
        "Re: pennant team",
        at(2025, 2, 11, 19, 3),
        "Happy to play lead again. Terry says I should skip but I like being first "
        "on the mat. Mags x",
    )
    mbox_add(
        MAGS,
        ME,
        "Saturday",
        at(2026, 5, 7, 21, 40),
        "Terry's not great this week, chest again. I might miss Saturday. Sorry "
        "love. M",
    )
    mbox_add(
        AOIFEB,
        COMMITTEE,
        "Afternoon tea roster",
        at(2025, 9, 30, 14, 0),
        "Roster for the new season attached as text below:\n17 Oct - Aoife B & "
        "Noreen\n24 Oct - Joan & Bernie\n31 Oct - Mags & Pat's Helen\n\nAoife Brennan",
    )
    mbox_add(
        PAT,
        COMMITTEE,
        "Sad news – Terry Doyle",
        at(2026, 6, 9, 8, 30),
        "Dear members,\n\nIt is with great sadness that I let you know Terry Doyle, "
        "husband of our Mags and a life member of this club, passed away yesterday."
        " Funeral details to follow.\n\nPat Kinnane, President",
    )
    mbox_add(
        PAT,
        COMMITTEE,
        "Midweek pennant final moved to Wednesday",
        at(2026, 8, 14, 17, 2),
        "All, Bowls Ballarat has moved the midweek final v Buninyong to Wednesday "
        "19 August, 10am, at our green. Pat",
    )
    mbox_add(
        PAT,
        COMMITTEE,
        "Pennant team changes",
        at(2026, 8, 21, 18, 15),
        "Hi all,\n\nFor the 2026-27 Saturday pennant: Mags Doyle has stepped back "
        "from Pennant this season. We all send her our love and the door is open "
        "whenever she's ready.\n\nAoife Brennan moves to lead on Bernie's rink.\n\n"
        "Pat",
    )
    mbox_add(
        PAT,
        COMMITTEE,
        "Opening day Saturday 17 October",
        at(2026, 10, 9, 10, 0),
        "Opening day for the 2026-27 season is Saturday 17 October, 12 noon. "
        "Whites please. Pat",
    )
    mbox_add(
        ME,
        PAT,
        "Re: Pennant team changes",
        at(2026, 8, 21, 20, 44),
        "Thanks Pat. I'll call in on her. Bernie",
    )
    MBOX.sort(key=lambda x: x[0])
    put("Mail/Local Folders/WPBC.mbox", "\n".join(m for _, m in MBOX))


# ---------------------------------------------------------------- chats


def wa_stamp(dt):
    h = dt.hour % 12 or 12
    ap = "am" if dt.hour < 12 else "pm"
    return f"{dt.day:02d}/{dt.month:02d}/{dt.year}, {h}:{dt.minute:02d} {ap}"


def filler_chat(rng, start, end, n, pool):
    span = (end - start).days
    out = []
    for _ in range(n):
        d = start + timedelta(days=rng.randrange(span))
        t = datetime(d.year, d.month, d.day, rng.randrange(7, 22), rng.randrange(60))
        who, text = pool[rng.randrange(len(pool))]
        out.append((t, who, text))
    return out


def whatsapp(name, msgs):
    msgs = sorted(msgs, key=lambda m: (m[0], m[1], m[2]))
    first = msgs[0][0] - timedelta(minutes=3)
    lines = [
        f"{wa_stamp(first)} - Messages and calls are end-to-end encrypted. No one "
        "outside of this chat, not even WhatsApp, can read or listen to them. Tap "
        "to learn more."
    ]
    for t, who, text in msgs:
        lines.append(f"{wa_stamp(t)} - {who}: {text}")
    put(f"Chats/WhatsApp Chat with {name}.txt", "\n".join(lines) + "\n")


def dt(y, mo, d, h, mi):
    return datetime(y, mo, d, h, mi)


def build_chats(rng):
    shiv_pool = [
        ("Siobhán", "<Media omitted>"),
        ("Siobhán", "Aoife got a HD in her pharmacology exam!!"),
        ("Bernie", "Clever girl! Gets it from her nana"),
        ("Siobhán", "How's Kieran behaving? Is he eating you out of house and home"),
        ("Bernie", "Two dinners a night. Grand lad"),
        ("Siobhán", "Tim's doing the ham again, don't bring one"),
        ("Bernie", "Dad says hello"),
        ("Siobhán", "Can you send me your scone recipe again"),
        ("Bernie", "Ring you Sunday x"),
        ("Siobhán", "Traffic on the Western Hwy is a nightmare, be there by 1"),
        ("Bernie", "Saw the photos, she's the image of Mum"),
        ("Siobhán", "Did Dad get his eyes tested?"),
        ("Bernie", "👍"),
        ("Siobhán", "Love you Mum x"),
    ]
    shiv = filler_chat(rng, date(2022, 2, 1), date(2026, 10, 20), 70, shiv_pool)
    shiv += [
        (
            dt(2026, 6, 8, 9, 2),
            "Siobhán",
            "So sorry about Terry Mum. Give Mags our love",
        ),
        (dt(2026, 8, 9, 18, 30), "Siobhán", "How's Mags doing?"),
        (dt(2026, 8, 9, 18, 41), "Bernie", "Haven't seen her much. I should go round"),
        (
            dt(2026, 9, 14, 20, 11),
            "Siobhán",
            "Mum did you ever get that mole on your "
            "leg looked at? You said Hamish wanted it seen",
        ),
        (
            dt(2026, 9, 14, 20, 15),
            "Bernie",
            "It's grand love, I'm booked in for November",
        ),
        (dt(2026, 9, 14, 20, 15), "Siobhán", "Promise?"),
        (dt(2026, 9, 14, 20, 16), "Bernie", "Yes yes"),
        (
            dt(2026, 10, 11, 19, 3),
            "Siobhán",
            "Booked the Lake View for Aoife's 21st! "
            "Sat 12 Dec, 6pm. Can you and Dad do a little toast?",
        ),
        (dt(2026, 10, 11, 19, 9), "Bernie", "Of course!! Our girl 21 😭"),
        (
            dt(2026, 10, 11, 19, 10),
            "Bernie",
            "I have something for her too, remind me to tell you",
        ),
        (
            dt(2026, 10, 18, 17, 22),
            "Siobhán",
            "Have you and Dad done the tax yet? Tim "
            "says he can look over the rental bit Sunday if you send it",
        ),
        (dt(2026, 10, 18, 17, 40), "Bernie", "Next week, it's on the list"),
        (dt(2026, 10, 18, 17, 41), "Siobhán", "Mum it's due the 31st 🙄"),
    ]
    whatsapp("Siobhán", shiv)

    g_pool = [
        ("Gerry", "Milk?"),
        ("Bernie", "Got it"),
        ("Gerry", "At the Shed, back by 1"),
        ("Gerry", "Sugar 6.9 this morning 👍"),
        ("Bernie", "Kieran's not home for tea"),
        ("Gerry", "Where did you put the good secateurs"),
        ("Bernie", "Bowls running late, put the spuds on"),
        ("Gerry", "Biscuit's been sick on the mat again"),
        ("Gerry", "Footy's on at 7:50"),
        ("Bernie", "Shed in the shed"),
        ("Gerry", "Bought the wrong bread"),
        ("Bernie", "Pick up your script at the chemist"),
    ]
    gerry = filler_chat(rng, date(2022, 1, 10), date(2026, 10, 15), 45, g_pool)
    gerry += [
        (
            dt(2026, 10, 10, 12, 31),
            "Gerry",
            "Podiatrist says the health fund knocked "
            "back the claim. Something about our account? Can you ring them",
        ),
        (dt(2026, 10, 10, 12, 50), "Bernie", "Probably their system. I'll ring Monday"),
        (
            dt(2026, 10, 19, 9, 5),
            "Gerry",
            "Did you do the rego love? Notice is on the fridge",
        ),
        (dt(2026, 10, 19, 9, 30), "Bernie", "Doing it tonight"),
        (dt(2026, 10, 23, 16, 2), "Gerry", "Rego??"),
        (dt(2026, 10, 23, 16, 20), "Bernie", "Tomorrow, promise"),
        (
            dt(2026, 5, 21, 18, 2),
            "Gerry",
            "I can do that valley myself, $2,350 is daylight robbery",
        ),
        (dt(2026, 5, 21, 18, 5), "Bernie", "You are not going up on that roof Gerald"),
    ]
    whatsapp("Gerry", gerry)

    m_pool = [
        ("Mags", "Coffee Wednesday? My shout"),
        ("Bernie", "Yes! Kiosk at 10.30?"),
        ("Mags", "Did you see Noreen's hat at pennant 😂"),
        ("Bernie", "Bringing the lemon slice — your recipe, don't tell anyone"),
        ("Mags", "Raffle tickets are in my car if you need them"),
        ("Bernie", "Won by 4! Your lead was the difference x"),
        ("Mags", "Terry says Gerry owes him $10 from the footy"),
        ("Mags", "Terry's chest is bad again, specialist Friday"),
        ("Bernie", "Thinking of you both x"),
        ("Mags", "Running 10 min late love"),
        ("Mags", "That book you lent me, I cried on the bus"),
    ]
    mags = filler_chat(rng, date(2023, 1, 5), date(2026, 5, 30), 55, m_pool)
    mags += [
        (
            dt(2026, 6, 8, 5, 52),
            "Mags",
            "Terry's gone Bernie. About half 5. Can you come",
        ),
        (dt(2026, 6, 8, 5, 53), "Bernie", "On my way"),
        (dt(2026, 6, 20, 15, 10), "Bernie", "How are you going love?"),
        (
            dt(2026, 6, 20, 19, 44),
            "Mags",
            "Up and down. House is very quiet. Thanks for the casserole x",
        ),
        (dt(2026, 7, 12, 10, 1), "Bernie", "Coffee Wednesday?"),
        (dt(2026, 7, 12, 16, 30), "Mags", "Maybe next week love, the kids are here"),
        (
            dt(2026, 8, 23, 17, 8),
            "Bernie",
            "Pat told us you're having a break from pennant. Completely understand x",
        ),
        (dt(2026, 8, 24, 21, 15), "Mags", "Can't face it yet."),
        (
            dt(2026, 9, 20, 20, 2),
            "Mags",
            "Don't worry about me love, you're busy with everything.",
        ),
        (dt(2026, 9, 27, 11, 40), "Bernie", "Thinking of you. Coffee soon x"),
    ]
    whatsapp("Mags Doyle", mags)

    k_pool = [
        ("Kieran", "home late, dont wait up"),
        ("Kieran", "can u get more weetbix"),
        ("Bernie", "There's lasagne in the fridge"),
        ("Kieran", "thanks nana ❤️"),
        ("Kieran", "exam went ok i think"),
        ("Kieran", "grandad asleep in the chair again lol"),
        ("Bernie", "Feed Biscuit if you're up first"),
        ("Kieran", "ok"),
        ("Kieran", "staying at Jess's tonight"),
        ("Bernie", "Text when you're home safe"),
    ]
    kier = filler_chat(rng, date(2025, 2, 10), date(2026, 10, 20), 40, k_pool)
    kier += [
        (dt(2025, 4, 17, 7, 1), "Kieran", "happy birthday nana!!! 🎂"),
        (dt(2026, 4, 17, 7, 3), "Kieran", "happy birthday nana 🎉 67!!"),
        (
            dt(2025, 6, 3, 21, 14),
            "Kieran",
            "nana there's water coming through my ceiling??",
        ),
        (
            dt(2025, 6, 3, 21, 20),
            "Bernie",
            "Put the blue bucket under it, Grandad will look Saturday",
        ),
        (
            dt(2026, 6, 20, 22, 3),
            "Kieran",
            "theres a brown patch above my bed lol is that bad",
        ),
        (
            dt(2026, 10, 9, 7, 12),
            "Kieran",
            "nana the ceilings dripping again, i moved my desk + put the bucket",
        ),
        (
            dt(2026, 10, 24, 8, 40),
            "Kieran",
            "can i borrow the forester sat 7th? going to geelong for jess's thing",
        ),
        (dt(2026, 10, 24, 8, 52), "Bernie", "Ask your grandfather. Probably yes"),
    ]
    kier.sort(key=lambda m: (m[0], m[1], m[2]))
    out = []
    for i, (t, who, text) in enumerate(kier, 1):
        aware = t.replace(tzinfo=mel_tz(t.date()))
        out.append(
            {
                "id": 3000 + i,
                "type": "message",
                "date": t.isoformat(),
                "date_unixtime": str(int(aware.timestamp())),
                "from": who,
                "from_id": "user5238811042" if who == "Kieran" else "user801276654",
                "text": text,
                "text_entities": [{"type": "plain", "text": text}],
            }
        )
    export = {
        "name": "Kieran",
        "type": "personal_chat",
        "id": 5238811042,
        "messages": out,
    }
    put(
        "Chats/Telegram/ChatExport_2026-10-24/result.json",
        json.dumps(export, indent=1, ensure_ascii=False) + "\n",
    )


# ---------------------------------------------------------------- notes vault

WEATHER = [
    "Frost on the car, -2 at 7am.",
    "Grey and drizzly, typical Ballarat.",
    "Lovely still morning, lake like glass.",
    "Wind off the lake would cut you in two.",
    "Warm one, 31. Watered the pots twice.",
    "Fog till eleven.",
    "Rain on and off all day.",
    "Blue sky, cold as charity.",
    "Hailed at 4pm!",
]
BITS = [
    "Bowls this arvo — won 18-11 with Noreen skipping. [[Bowls]] #bowls",
    "Seed bank shift at the Gardens, cleaned Banksia seed with Ted. [[Seed bank]] "
    "#garden",
    "Gerry's sugars 7.9 this morning. He had the custard tart anyway. [[Gerry]]",
    "Kieran home late, ate two dinners. [[Kieran]]",
    "Made brown bread. [[Recipes/Brown bread]]",
    "Wrote 600 words of chapter 3 — the Kilrush workhouse bit. [[Family History]] "
    "#writing",
    "Rang Colleen. Raining in Ennis too, she says, as if that's news.",
    "Read in bed, Middlemarch again. #reading",
    "Pruned the roses by the side fence. #garden",
    "Gerry at the Men's Shed all morning, came home with a birdhouse nobody asked for.",
    "Mass at St Pat's then coffee at the kiosk.",
    "Woolies, chemist, post office. Errand day.",
    "Committee minutes typed and sent. #bowls",
    "Knee bad on the stairs. Voltaren and a hot pack. [[Health]]",
    "Video call with Declan & Raj, Perth 29 degrees, show-offs.",
    "Siobhán rang about Christmas.",
    "Walked the lake loop, 6.2km, knee held up.",
    "Found a Considine baptism in the Kilmurry register online! [[Family History]]",
    "Gerry asleep in the chair by 8. Normal service.",
    "Repotted the Correa cuttings. #garden",
    "Library: picked up two holds. [[Books to read]]",
    "Biscuit brought in a mouse. Alive. Gerry chased it for twenty minutes.",
    "Scones for afternoon tea roster. [[Recipes/Scones]]",
    "Lost at bowls, badly. Blame the green.",
    "Kieran fixed the printer. Genius child.",
]
TASKS = [
    "- [ ] gutters",
    "- [x] pay Telstra",
    "- [ ] library books back",
    "- [x] bowls minutes",
    "- [ ] Christmas cards to Ireland",
    "- [ ] seed labels",
    "- [x] Gerry's script",
    "- [ ] photo albums for Siobhán",
]

FORCED = {
    date(2024, 6, 9): [
        "Found Mum's ring in the blue box at the top of the wardrobe — "
        "Nana Peg's sapphire. One of the claws is lifting, the stone "
        "moves a bit. Must get it seen to before it's needed. #family"
    ],
    date(2025, 6, 3): [
        "Drip in Kieran's room after the storm — bucket under it. Gerry "
        "up the ladder Saturday maybe. [[House]]"
    ],
    date(2025, 10, 28): [
        "Lodged the tax on myGov at 10pm, three days to spare. Never "
        "again. Note to self: start in August next year."
    ],
    date(2025, 10, 29): ["Paid the rego online, $874.10 — up again."],
    date(2025, 10, 30): [
        "Lunch with Mags for her birthday at The Forge. She laughed so "
        "hard at Gerry's Shed stories she cried."
    ],
    date(2026, 2, 11): [
        "GP — Hamish had a look at the spot on my left calf. Wants a "
        "dermatologist to see it, referral to [[Dr Rao]] at Lydiard St. "
        "'Don't sit on it, Bernie.' [[Health]]"
    ],
    date(2026, 3, 8): [
        "Emailed Sturt St Jewellers about Mum's ring. Haven't told Shiv."
    ],
    date(2026, 5, 14): [
        "Craig from Ballarat Roof Restorations up on the roof. Says the "
        "valley flashing's rusted through over Kieran's room. Quote to "
        "come. [[House]]"
    ],
    date(2026, 5, 21): [
        "Roof quote came — $2,350. Gerry says he can do it himself. He's 70."
    ],
    date(2026, 6, 8): [
        "Terry Doyle died this morning. Mags rang at 6. I went straight "
        "round. Forty-four years married."
    ],
    date(2026, 6, 16): [
        "Terry's funeral. St Pat's packed. Mags held up until the hearse."
    ],
    date(2026, 6, 21): [
        "Ceiling stain in Kieran's room is bigger — brown ring the size "
        "of a dinner plate."
    ],
    date(2026, 6, 22): [
        "Rang RACV about the roof — gradual leaks not covered, only "
        "sudden storm damage. So that's that. Need it fixed before the "
        "plaster goes. [[House]]"
    ],
    date(2026, 7, 5): ["- [ ] ring Mags"],
    date(2026, 7, 14): ["Corio Bay sent the EOFY statement. Filed it. [[Tax 2025-26]]"],
    date(2026, 8, 2): [
        "Must ring Mags. Keep putting it off. What do I even say to her."
    ],
    date(2026, 8, 9): [
        "Card got skimmed — $219.99 at some online electronics place in "
        "Sydney. Bank cancelled it, new one coming. [[Money]]"
    ],
    date(2026, 8, 15): [
        "New card came (ending 0458). Update the autopays:",
        "    - [x] Netflix",
        "    - [x] Origin",
        "    - [x] Telstra",
        "    - [ ] Lakeside",
    ],
    date(2026, 8, 18): [
        "Cancelled Dr Rao tomorrow — midweek pennant final got moved to "
        "Wednesday. I'll rebook."
    ],
    date(2026, 8, 19): ["Lost the final by two shots. Should have gone to the doctor."],
    date(2026, 8, 20): ["Rebooked Rao — November, earliest they had."],
    date(2026, 9, 6): [
        "Saw Mags across the car park at Woolies. Waved. She waved. "
        "Didn't go over. Coward.",
        "- [ ] ring Mags",
    ],
    date(2026, 10, 4): ["- [ ] ring Mags"],
    date(2026, 10, 9): [
        "Rain all night. Bucket in Kieran's room half full by morning. "
        "Gerry says it's the valley flashing, like Craig said in May."
    ],
    date(2026, 10, 12): [
        "That spot on my calf caught on the towel and bled a bit. "
        "Plaster on it. Probably nothing."
    ],
    date(2026, 10, 17): [
        "Started the tax. Got as far as the rental. Where is the "
        "depreciation schedule?? Gerry thinks the filing cabinet. "
        "[[Tax 2025-26]]",
        "Opening day at bowls. No Mags.",
    ],
    date(2026, 10, 21): ["Gerry asked about the rego again. On the list."],
    date(2026, 10, 24): ["Saturday. Kieran wants the Forester for Geelong on the 7th."],
}

PAGES = {
    "Gerry.md": "# Gerry\n\nGerald Patrick Halloran, b. 2 Aug 1955. Retired surveyor "
    "(Shire of Ballarat, then private). Type 2 diabetes since 2014 — [[Health]].\n\n"
    "- Men's Shed Mondays\n- Dr Nair every 6 months (May/Nov)\n- Will not wear his "
    "hearing aids\n- Thinks he can fix the roof himself #house\n",
    "Kieran.md": "# Kieran\n\nGrandson, b. 2 March 2007. Living with us since Feb 2025 "
    "while he does Engineering at Federation Uni (Mt Helen). Pays $100/wk board.\n\n"
    "- Telegram, not WhatsApp\n- Girlfriend Jess (Geelong)\n- Room = back bedroom "
    "(see [[House]])\n",
    "Bowls.md": "# Bowls\n\nWendouree Park Bowls Club (WPBC). I'm Hon. Secretary since "
    "2021. Social Tuesdays, Saturday pennant Div 3, midweek pennant in winter.\n\n"
    "- Committee: 2nd Tuesday, 7pm\n- Rink: me (skip), Noreen, Aoife B, Joan\n"
    "- [[Mags]] played lead for years #bowls\n",
    "Seed bank.md": "# Seed bank\n\nFriends of Ballarat Botanical Gardens. Alternate "
    "Thursdays 9:30–12 with Ted. Heather Lyle coordinates.\n\nLog: "
    "`Garden/seedbank_log_2026.csv` #garden\n",
    "Family History.md": "# Family History — The Considines of Clare\n\nFor the cousins."
    " Brendan does the records, I do the writing.\n\n## Chapters\n1. Kilmurry "
    "Ibrickane (done)\n2. Patrick and Honora (done)\n3. The workhouse years "
    "(drafting)\n4. Mam and Dad — Ennis\n5. Coming to Australia, 1983\n\nSee "
    "[[Ireland 2023]]. #writing\n",
    "Ireland 2023.md": "# Ireland 2023\n\n2–30 May. Colleen's in Ennis. Drumcliff "
    "graveyard, Lahinch with Brendan, Kilrush heritage centre. Mam and Dad's stone "
    "needed re-lettering — Colleen organised Cronin's, my half €725 (paid May 2024).\n",
    "Health.md": "# Health\n\n## Me\n- Knee (R) osteoarthritis — physio said "
    "strengthening, ha\n- Atorvastatin 20mg\n- Skin: see [[Dr Rao]]\n\n## Gerry\n"
    "- HbA1c 7.4 (May 2025), 7.1 (May 2026)\n- Metformin, empagliflozin, atorvastatin "
    "40, ramipril\n- Podiatrist yearly\n",
    "Dr Rao.md": "# Dr Rao\n\nDr Anjali Rao, dermatologist. Lydiard Dermatology, 22 "
    "Lydiard St North. (03) 5331 8842.\nReferral from Hamish Feb 2026 (valid 12 "
    "months).\n",
    "House.md": "# House\n\n27 Kellett Street. Bought 1991.\n\n- Roof: leak over "
    "Kieran's room since 2025. Craig Pollard (Ballarat Roof Restorations) 0418 552 907\n"
    "- Hot water: replaced 2019\n- Gutters every autumn\n- RACV home & contents "
    "HC-7718203, renews March\n#house\n",
    "Money.md": "# Money\n\n- CommBank Smart Access (joint) — everything goes through "
    "it. Debit Mastercard.\n- NetBank Saver xx4471\n- AusPrime Super — both on "
    "account-based pensions\n- Weller St unit (Geelong West) — Corio Bay, Leanne "
    "Vukovic\n- Lakeside Health — Couples Gold Hospital & Top Extras, member "
    "LH-5520913, comes off the card on the 28th\n- Origin (BPAY), Telstra (DD), "
    "Netflix (card)\n",
    "Tax 2025-26.md": "# Tax 2025-26\n\nDoing it ourselves on myGov again. Deadline "
    "31 Oct if no agent. Last year lodged 28/10/2025 — NEVER AGAIN.\n\n"
    "- [x] super pension statements (prefilled)\n- [x] Corio Bay EOFY statement "
    "(14/7)\n- [ ] depreciation schedule — Gerry? BMT report 2019? filing cabinet?\n"
    "- [ ] Geelong council rates\n- [ ] Barwon Water\n- [ ] landlord insurance\n"
    "- [ ] hot water service $1,980 — repair or capital?? ask Tim\n\nSpreadsheet: "
    "Documents/Rental unit 2025-26.xlsx\n#tax #money\n",
    "Books to read.md": "# Books to read\n\n- Small Things Like These\n- The Bee Sting\n"
    "- Demon Copperhead (Mags says devastating)\n- Middlemarch again, always\n#reading\n",
    "Christmas 2025.md": "# Christmas 2025\n\nAt Siobhán's. Me: pudding + brandy butter. "
    "Gifts: Aoife — perfume (done). Kieran — headphones (done). Declan & Raj — "
    "voucher. Colleen — calendar of Ballarat posted 18 Nov.\n",
    "Recipes/Brown bread.md": "# Brown bread (Mam's)\n\n- 450g wholemeal\n- 100g "
    "plain flour\n- 1 tsp bread soda\n- 1 tsp salt\n- 1 egg\n- 450ml buttermilk\n\n"
    "Mix, don't knead. Cross on top 'to let the fairies out'. 200C for 45 min.\n"
    "#recipe\n",
    "Recipes/Scones.md": "# Scones\n\n3 cups SR flour, 1 cup cream, 1 cup lemonade. "
    "Pat out, don't roll. 220C, 12–15 min. (Yes, lemonade. Mags's trick.)\n#recipe\n",
}


def build_notes(rng):
    root = "Notes/Bernie's Vault/"
    put(
        root + ".obsidian/app.json",
        json.dumps({"alwaysUpdateLinks": True, "showLineNumber": False}, indent=2),
    )
    put(
        root + ".obsidian/daily-notes.json",
        json.dumps(
            {"folder": "Daily", "format": "YYYY-MM-DD", "template": ""}, indent=2
        ),
    )
    for name in sorted(PAGES):
        put(root + name, PAGES[name])
    start = date(2024, 2, 1)
    span = (TODAY - start).days
    picks = {start + timedelta(days=x) for x in rng.sample(range(span), 120)}
    for d in sorted(picks | set(FORCED)):
        lines = [
            "---",
            f"date: {d.isoformat()}",
            "tags: [daily]",
            "---",
            f"# {long_date(d)}",
            "",
            "- " + WEATHER[rng.randrange(len(WEATHER))],
        ]
        for b in rng.sample(BITS, rng.randrange(1, 4)):
            lines.append("- " + b)
        for f in FORCED.get(d, []):
            lines.append(f if f.startswith(("- [", "    ")) else "- " + f)
        if rng.random() < 0.3:
            lines.append(TASKS[rng.randrange(len(TASKS))])
        put(root + f"Daily/{d.isoformat()}.md", "\n".join(lines) + "\n")


# ---------------------------------------------------------------- documents


def build_documents():
    put(
        "Documents/Will - draft (2021).docx",
        docx(
            "Will draft",
            [
                "# LAST WILL AND TESTAMENT — DRAFT",
                "This is the last will of me, BERNADETTE MARY HALLORAN of 27 Kellett Street, "
                "Lake Wendouree in the State of Victoria, retired nurse.",
                "1. I revoke all earlier wills.",
                "2. I appoint my husband GERALD PATRICK HALLORAN as executor, or if he does "
                "not survive me, my children SIOBHÁN PETTIT and DECLAN HALLORAN jointly.",
                "3. I give my interest in 2/41 Weller Street, Geelong West to my husband, or if "
                "he does not survive me, to my children in equal shares.",
                "4. I give my jewellery to my daughter Siobhán, to share with my "
                "granddaughter as she sees fit.",
                "5. I give the residue of my estate to my husband, or if he does not survive "
                "me, to my children in equal shares.",
                "",
                "[DRAFT 2 March 2021 — not signed. Ask Mr Barker about the unit and the "
                "super death benefit nomination.]",
            ],
            "2021-03-02T10:14:00Z",
            "2021-03-09T16:40:00Z",
        ),
    )

    put(
        "Documents/Family History/The Considines of Clare - Chapter 3.docx",
        docx(
            "The Considines of Clare - Chapter 3",
            [
                "# Chapter 3 — The Workhouse Years",
                "In the winter of 1849 the Kilrush Union minute book records the admission "
                "of a Michael Considine and five children from the townland of Doonbeg. "
                "Brendan believes, and I have come to believe, that these are ours.",
                "The record does not give a wife's name. It gives only the children's ages "
                "— eleven, nine, six, four and an infant — and the word 'destitute', "
                "written in a clerk's steady hand as if it were the weather.",
                "## What the records say",
                "The 1901 census finds a Honora Considine, widow, in Kilmurry Ibrickane "
                "with her son Patrick, aged seven. By 1911 Patrick is seventeen and a farm "
                "labourer. He is our grandfather, the man Mam called 'Daddo', who died in "
                "1961, two years after I was born.",
                "## What the records don't say",
                "Nobody wrote down what it cost Honora to keep the boy out of the "
                "workhouse her husband's people had gone into. We have to imagine it, "
                "and I find I don't want to imagine it too kindly.",
                "[Bernie — check the Doonbeg townland with Brendan before the cousins see "
                "this. Draft 4, Oct 2026.]",
            ],
            "2024-11-02T09:00:00Z",
            "2026-10-03T21:12:00Z",
        ),
    )

    put(
        "Documents/Bowls/WPBC Secretary's report AGM 2025.docx",
        docx(
            "Secretary's report 2025",
            [
                "# Wendouree Park Bowls Club — Secretary's Report",
                "Annual General Meeting, Sunday 27 July 2025",
                "Membership stands at 112 (playing 86, social 26), up six on last year.",
                "The committee met eleven times. Highlights: the shade sail grant ($8,400, "
                "Bowls Victoria), new bar fridge, and the return of the Christmas twilight "
                "triples.",
                "Our Saturday Div 3 side finished fourth; midweek reached the semi-final.",
                "Thanks to Mags Doyle for the raffle (again), Aoife Brennan for the "
                "afternoon tea roster, and to Pat for putting up with my minutes.",
                "Bernie Halloran, Hon. Secretary",
            ],
            "2025-07-20T15:00:00Z",
            "2025-07-26T20:31:00Z",
        ),
    )

    put(
        "Documents/Bowls/Committee minutes 11-08-2026.odt",
        odt(
            "Committee minutes August 2026",
            [
                "# WPBC Committee Meeting — Minutes",
                "Tuesday 11 August 2026, 7pm, clubrooms.",
                "Present: P Kinnane (chair), B Halloran (sec), N Walsh, H Kinnane, "
                "A Brennan, J Ferris. Apologies: M Doyle.",
                "## 1. Correspondence",
                "Bowls Ballarat: midweek pennant final v Buninyong likely moved to Wed 19 "
                "Aug (confirmation to come).",
                "## 2. Treasurer's report",
                "Balance $14,212.08. Shade sail grant acquitted.",
                "## 3. Pennant selection 2026-27",
                "President noted Mags Doyle would step back from pennant this season. "
                "Committee sent condolences again on Terry's passing.",
                "## 4. General business",
                "Opening day Sat 17 October. Afternoon tea roster to A Brennan.",
                "Meeting closed 8:40pm.",
            ],
            "2026-08-12T09:22:00",
        ),
    )

    months = [
        "Jul-25",
        "Aug-25",
        "Sep-25",
        "Oct-25",
        "Nov-25",
        "Dec-25",
        "Jan-26",
        "Feb-26",
        "Mar-26",
        "Apr-26",
        "May-26",
        "Jun-26",
    ]
    rent_rows = [
        ["Rental unit 2/41 Weller St — FY 2025-26"],
        [],
        ["Month", "Weeks", "Rent received", "Notes"],
    ]
    for i, m in enumerate(months):
        w = FY26_WEEKS[i]
        rent_rows.append([m, w, w * 420, "$420/wk"])
    total = sum(w * 420 for w in FY26_WEEKS)
    rent_rows.append(
        [
            "TOTAL",
            ("SUM(B4:B15)", 52),
            ("SUM(C4:C15)", total),
            "matches Leanne's statement",
        ]
    )
    exp_rows = [
        ["Expenses FY 2025-26"],
        [],
        ["Item", "Amount", "Notes"],
        ["Management fees", 1638.0, "Corio Bay 7.5%"],
        ["Smoke alarm service", 186.5, "Sep 25"],
        ["Hot water service", 1980.0, "repair or capital? ask Tim"],
        ["Landlord insurance", 489.0, "Terri Scheer"],
        ["Council rates (Geelong)", "", "find notice"],
        ["Water (Barwon)", "", ""],
        ["Depreciation", "", "?? BMT report 2019 - ask Gerry"],
        ["TOTAL", ("SUM(B4:B10)", 4293.5), ""],
    ]
    put(
        "Documents/Rental unit 2025-26.xlsx",
        xlsx(
            "Rental unit 2025-26",
            [("Rent", rent_rows), ("Expenses", exp_rows)],
            "2026-07-15T10:00:00Z",
            "2026-10-17T21:48:00Z",
        ),
    )

    budget = [["Household budget 2026"], [], ["Category", "Monthly", "Annual", "Notes"]]
    items = [
        ("Groceries", 780),
        ("Electricity & gas (Origin)", 215),
        ("Telstra", 95),
        ("Netflix", 18.99),
        ("Lakeside Health (couples gold)", 412.85),
        ("Council rates (Ballarat)", 216.05),
        ("Car fuel", 210),
        ("Car rego (Nov)", 73.33),
        ("RACV home insurance", 182.05),
        ("Bowls subs", 23.75),
        ("Gifts & Christmas", 90),
        ("Roof - Kieran's room", 0),
    ]
    for i, (name, mo) in enumerate(items, 4):
        note = {
            "Car rego (Nov)": "est. 880 for the year",
            "Lakeside Health (couples gold)": "from 1 Apr. off the card on 28th",
            "Roof - Kieran's room": "Craig's quote?",
        }.get(name, "")
        budget.append([name, mo, (f"B{i}*12", round(mo * 12, 2)), note])
    n = len(items) + 3
    budget.append(
        [
            "TOTAL",
            (f"SUM(B4:B{n})", round(sum(m for _, m in items), 2)),
            (f"SUM(C4:C{n})", round(sum(round(m * 12, 2) for _, m in items), 2)),
            "",
        ]
    )
    income = [
        ["Income 2026"],
        [],
        ["Source", "Monthly"],
        ["AusPrime pension - Bernie", 3196.40],
        ["AusPrime pension - Gerry", 3511.56],
        ["Weller St (net, Corio Bay)", 1683.50],
        ["Kieran board", 433.33],
    ]
    put(
        "Documents/Household budget 2026.xlsx",
        xlsx(
            "Household budget 2026",
            [("Budget", budget), ("Income", income)],
            "2026-01-04T11:00:00Z",
            "2026-04-02T19:15:00Z",
        ),
    )

    put("Documents/Scans/Referral - Dr Tolley 11-02-2026.pdf", referral_pdf())
    put("Documents/Scans/CorioBay_EOFY_Statement_2026.pdf", eofy_pdf())

    put(
        "Documents/Gerry meds.txt",
        "GERRY - MEDS (updated May 2026)\r\n\r\nmetformin XR 1000mg - 1 morning 1 night\r\n"
        "empagliflozin (Jardiance) 10mg - morning\r\natorvastatin 40mg - night\r\n"
        "ramipril 5mg - morning\r\n\r\nAllergies: penicillin (rash)\r\nDr Nair "
        "(03) 5320 4471\r\n",
    )
    put(
        "Documents/Recipes/Mags lemon slice.txt",
        "MAGS'S LEMON SLICE (copied off the card she gave me, 2019)\n\nBase: 1 pkt "
        "Marie biscuits crushed, 125g butter melted, 1/2 tin condensed milk, 1 cup "
        "coconut, zest of 1 lemon.\nIcing: 2 cups icing sugar, 30g butter, juice of 1 "
        "lemon.\n\nPress base into slice tin, fridge 1 hr. Ice. Fridge again. Cut "
        "small, it's rich.\n\n'Don't give this to Noreen' - M.\n",
    )
    put(
        "Documents/Recipes/Anzac biscuits.md",
        "# Anzac biscuits\n\n1 cup oats, 1 cup plain flour, 1 cup sugar, 3/4 cup "
        "coconut, 125g butter, 2 tbsp golden syrup, 1/2 tsp bicarb, 2 tbsp boiling "
        "water. 160C 12 min. Chewy = take out early.\n",
    )


def build_misc(rng):
    put(
        "Desktop/todo.txt",
        "TO DO\n\n- gutters before winter (Gerry)\n- Kieran's ceiling - ring Craig back "
        "re quote\n- seed bank roster to Heather\n- bowls AGM minutes\n- Christmas "
        "cards Ireland (post by 20 Nov!)\n- library books back\n- ask Leanne re smoke "
        "alarm invoice\n- update will?? (since 2021...)\n- photo albums to Siobhan\n"
        "- Brendan - ch 3 by Christmas\n",
    )
    put(
        "Desktop/passwords.txt",
        "PASSWORDS - do not lose!!\n\nbigpond email: Gerry&Bernie1983\nnetbank: client "
        "61847720  pw Wendouree#14  (changed after card thing aug 26 -> Wendouree#15)\n"
        "myGov: bernie.halloran59@bigpond.com / Kilmurry1959!\nlakeside app: ??? forgot "
        "- reset\nNetflix: kieran knows\nwifi: TelstraB7F2 / 9x4kfm2pq7\nVicRoads: same "
        "as myGov\nancestry: Considine1849\n",
    )
    draft = ["Month,Weeks,Rent"]
    for m in [
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
    ]:
        draft.append(f"{m},4,1680")
    draft.append("TOTAL,48,20160")
    draft.append(',,"rough - 4 wks x 420 each month"')
    put("Downloads/rental_fy26_draft.csv", "\r\n".join(draft) + "\r\n")

    census = [
        "Surname,Forename,Townland,DED,County,Age,Sex,Relation to head,Religion,"
        "Literacy,Occupation,Marital status",
        "Considine,Honora,Caherfeenick,Kilmurry,Clare,52,Female,Head of Family,"
        "Roman Catholic,Cannot read,Farmer,Widow",
        "Considine,Patrick,Caherfeenick,Kilmurry,Clare,17,Male,Son,Roman Catholic,"
        "Read and write,Farm Labourer,Not Married",
        "Considine,Mary,Caherfeenick,Kilmurry,Clare,14,Female,Daughter,Roman "
        "Catholic,Read and write,Scholar,Not Married",
        "Hehir,John,Caherfeenick,Kilmurry,Clare,71,Male,Brother-in-law,Roman "
        "Catholic,Read,Farm Servant,Widower",
    ]
    put("Family History/census_1911_Considine_Kilmurry.csv", "\n".join(census) + "\n")
    ged = [
        "0 HEAD",
        "1 SOUR FTM",
        "2 VERS 2024",
        "1 GEDC",
        "2 VERS 5.5.1",
        "2 FORM LINEAGE-LINKED",
        "1 CHAR UTF-8",
        "1 DATE 3 OCT 2026",
    ]
    people = [
        (
            "I1",
            "Bernadette Mary /Considine/",
            "F",
            "17 APR 1959",
            "Ennis, Clare, Ireland",
            None,
            "F1",
            "F3",
        ),
        (
            "I2",
            "Colleen /Considine/",
            "F",
            "8 SEP 1956",
            "Ennis, Clare, Ireland",
            None,
            "F1",
            None,
        ),
        (
            "I3",
            "Michael /Considine/",
            "M",
            "1928",
            "Kilmurry, Clare, Ireland",
            "2009",
            "F2",
            "F1",
        ),
        (
            "I4",
            "Margaret (Peg) /Keane/",
            "F",
            "1931",
            "Ennistymon, Clare, Ireland",
            "2019",
            None,
            "F1",
        ),
        (
            "I5",
            "Patrick /Considine/",
            "M",
            "1894",
            "Kilmurry, Clare, Ireland",
            "1961",
            None,
            "F2",
        ),
        (
            "I6",
            "Bridget /Hehir/",
            "F",
            "1899",
            "Miltown Malbay, Clare, Ireland",
            "1970",
            None,
            "F2",
        ),
        (
            "I7",
            "Gerald Patrick /Halloran/",
            "M",
            "2 AUG 1955",
            "Ballarat, Victoria",
            None,
            None,
            "F3",
        ),
        (
            "I8",
            "Siobhán /Halloran/",
            "F",
            "19 JUL 1985",
            "Ballarat, Victoria",
            None,
            "F3",
            None,
        ),
        (
            "I9",
            "Declan /Halloran/",
            "M",
            "26 JAN 1988",
            "Ballarat, Victoria",
            None,
            "F3",
            None,
        ),
    ]
    for pid, name, sex, born, plac, died, famc, fams in people:
        ged += [
            f"0 @{pid}@ INDI",
            f"1 NAME {name}",
            f"1 SEX {sex}",
            "1 BIRT",
            f"2 DATE {born}",
            f"2 PLAC {plac}",
        ]
        if died:
            ged += ["1 DEAT", f"2 DATE {died}"]
        if famc:
            ged.append(f"1 FAMC @{famc}@")
        if fams:
            ged.append(f"1 FAMS @{fams}@")
    ged += [
        "0 @F1@ FAM",
        "1 HUSB @I3@",
        "1 WIFE @I4@",
        "1 CHIL @I2@",
        "1 CHIL @I1@",
        "0 @F2@ FAM",
        "1 HUSB @I5@",
        "1 WIFE @I6@",
        "1 CHIL @I3@",
        "0 @F3@ FAM",
        "1 HUSB @I7@",
        "1 WIFE @I1@",
        "1 MARR",
        "2 DATE 14 SEP 1984",
        "2 PLAC St Patrick's Cathedral, Ballarat",
        "1 CHIL @I8@",
        "1 CHIL @I9@",
        "0 TRLR",
    ]
    put("Family History/Halloran-Considine.ged", "\r\n".join(ged) + "\r\n")

    species = [
        "Acacia melanoxylon",
        "Banksia marginata",
        "Correa reflexa",
        "Eucalyptus viminalis",
        "Grevillea rosmarinifolia",
        "Hakea decurrens",
        "Leptospermum continentale",
        "Bursaria spinosa",
        "Themeda triandra",
        "Xerochrysum bracteatum",
    ]
    log = ["Date,Species,Accession,Seed weight (g),Viability %,Notes"]
    d = date(2026, 1, 8)
    acc = 2026001
    while d < TODAY:
        sp = species[rng.randrange(len(species))]
        log.append(
            f"{d:%d/%m/%Y},{sp},BBG-{acc},{rng.uniform(2, 60):.1f},"
            f"{rng.randrange(55, 98)},"
        )
        acc += 1
        d += timedelta(days=14)
    put("Garden/seedbank_log_2026.csv", "\n".join(log) + "\n")

    clips = [
        (
            "Middlemarch (George Eliot)",
            812,
            "for the growing good of the world is partly "
            "dependent on unhistoric acts; and that things are not so ill with you and me "
            "as they might have been, is half owing to the number who lived faithfully a "
            "hidden life, and rest in unvisited tombs.",
            date(2023, 7, 2),
        ),
        (
            "Persuasion (Jane Austen)",
            401,
            "She had been forced into prudence in her "
            "youth, she learned romance as she grew older: the natural sequel of an "
            "unnatural beginning.",
            date(2024, 1, 19),
        ),
        (
            "The Secret Garden (Frances Hodgson Burnett)",
            233,
            "If you look the right way, you can see that the whole world is a garden.",
            date(2024, 9, 8),
        ),
        (
            "Dubliners (James Joyce)",
            1620,
            "His soul swooned slowly as he heard the snow "
            "falling faintly through the universe and faintly falling, like the descent "
            "of their last end, upon all the living and the dead.",
            date(2023, 5, 14),
        ),
        (
            "Walden (Henry David Thoreau)",
            590,
            "I went to the woods because I wished to "
            "live deliberately, to front only the essential facts of life.",
            date(2025, 2, 23),
        ),
        (
            "Meditations (Marcus Aurelius)",
            288,
            "Loss is nothing else but change, and change is Nature's delight.",
            date(2026, 6, 19),
        ),
        (
            "Meditations (Marcus Aurelius)",
            301,
            "Very little is needed to make a happy life.",
            date(2026, 6, 19),
        ),
        (
            "Middlemarch (George Eliot)",
            1544,
            "What do we live for, if it is not to make "
            "life less difficult to each other?",
            date(2026, 8, 3),
        ),
        (
            "Anne of Green Gables (L. M. Montgomery)",
            377,
            "Isn't it nice to think that "
            "tomorrow is a new day with no mistakes in it yet?",
            date(2025, 11, 2),
        ),
    ]
    out = []
    for i, (book, loc, text, d) in enumerate(clips):
        t = f"{rng.randrange(19, 23):02d}:{rng.randrange(60):02d}:{rng.randrange(60):02d}"
        out.append(
            f"{book}\r\n- Your Highlight on Location {loc}-{loc + 2} | Added on "
            f"{long_date(d)} {t}\r\n\r\n{text}\r\n==========\r\n"
        )
        if i == 5:
            out.append(
                f"{book}\r\n- Your Note on Location {loc + 1} | Added on "
                f"{long_date(d)} {t}\r\n\r\nfor Mags\r\n==========\r\n"
            )
    put("Kindle/My Clippings.txt", "﻿" + "".join(out))

    put(
        "Books/Propagating Natives from Seed - FOBBG.epub",
        epub(
            "Propagating Natives from Seed",
            "Heather Lyle",
            "urn:uuid:5f1d2c0e-8a3b-4c11-9d2e-6b7a01c4e9f3",
            [
                (
                    "Collecting seed",
                    [
                        "Collect from at least ten plants spread across a population, never "
                        "more than a fifth of the seed on any one plant.",
                        "Label everything at the point of collection: species, locality, date, "
                        "collector. A bag without a label is compost.",
                    ],
                ),
                (
                    "Breaking dormancy",
                    [
                        "Acacias and other hard-coated legumes need heat: pour just-boiled "
                        "water over the seed and leave overnight. Swollen seed is ready to sow.",
                        "Many grasses, including kangaroo grass, germinate better after smoke "
                        "water treatment.",
                    ],
                ),
            ],
        ),
    )


# ---------------------------------------------------------------- build


def build():
    FILES.clear()
    MBOX.clear()
    rng = random.Random(SEED)
    origin = origin_table(rng)
    build_contacts()
    build_calendar()
    build_bank(rng, origin)
    build_key_emails(origin)
    build_filler_emails(rng, origin)
    build_mbox(rng)
    build_chats(rng)
    build_notes(rng)
    build_documents()
    build_misc(rng)
    return dict(sorted(FILES.items()))


# ================================================================ planted / check

PLANTED = [
    (
        "N1",
        "Need",
        "The car registration lapses on 3 Nov 2026 and hasn't been paid",
        "urgent-practical, deadline",
        [
            (
                "Mail/Inbox/2026-10-06 Registration renewal notice SUBARU FORESTER 1XY4KD.eml",
                "this year's notice: $912.40, expires 03/11/2026",
                ["1XY4KD", "03/11/2026", "$912.40"],
            ),
            (
                "Chats/WhatsApp Chat with Gerry.txt",
                "Gerry asks twice (19 and 23 Oct); Bernie keeps deferring",
                ["Did you do the rego love?", "Tomorrow, promise"],
            ),
            (
                "Calendar/Home.ics",
                "yearly all-day 'Car rego due' on 3 Nov",
                ["Car rego due", "renew online before 3 Nov"],
            ),
            (
                "Bank/CommBank_SmartAccess_FY2025-26.csv",
                "last year's payment is there; the "
                "FY2026-27 file has no VICROADS line at all",
                ["VICROADS REGO 1XY4KD", "-874.10"],
            ),
            (
                "Chats/Telegram/ChatExport_2026-10-24/result.json",
                "Kieran wants the Forester on Sat 7 Nov, after expiry",
                ["borrow the forester sat 7th"],
            ),
            (
                "Notes/Bernie's Vault/Daily/2026-10-21.md",
                "'On the list.'",
                ["asked about the rego again"],
            ),
        ],
    ),
    (
        "N2",
        "Need",
        "The changing mole on her left calf has never been seen by the "
        "dermatologist; both bookings fell through",
        "health, slow-burning",
        [
            (
                "Documents/Scans/Referral - Dr Tolley 11-02-2026.pdf",
                "GP referral: 7mm irregular lesion, left calf, 'review in 6 months'",
                ["left calf", "7mm", "review in 6 months"],
            ),
            (
                "Calendar/Home.ics",
                "19 Aug skin check STATUS:CANCELLED by her (pennant final)",
                ["Dr Rao - skin check", "cancelled - pennant final"],
            ),
            (
                "Notes/Bernie's Vault/Daily/2026-08-18.md",
                "she cancelled it herself",
                ["Cancelled Dr Rao tomorrow"],
            ),
            (
                "Mail/Inbox/2026-10-02 Your appointment has been cancelled.eml",
                "the clinic cancelled the 5 Nov rebooking",
                ["has been cancelled", "Dr Feeney"],
            ),
            (
                "Chats/WhatsApp Chat with Siobhán.txt",
                "tells Siobhán she's booked in for November",
                ["booked in for November"],
            ),
            (
                "Notes/Bernie's Vault/Daily/2026-10-12.md",
                "the spot bled",
                ["bled a bit"],
            ),
        ],
    ),
    (
        "N3",
        "Need",
        "Health-insurance premiums have bounced since the card was replaced;"
        " cover is suspended 14 Nov unless $1,238.55 is paid",
        "money, urgent",
        [
            (
                "Mail/Inbox/2026-08-08 Weve replaced your card.eml",
                "old card 7731 cancelled, new 0458; update recurring payments",
                ["7731", "0458", "update any recurring payments"],
            ),
            (
                "Notes/Bernie's Vault/Daily/2026-08-15.md",
                "autopay checklist, Lakeside left unticked",
                ["- [ ] Lakeside", "- [x] Netflix"],
            ),
            (
                "Bank/CommBank_SmartAccess_FY2026-27.csv",
                "last LAKESIDE debit 28/07/2026, none after",
                ["28/07/2026", "LAKESIDE HEALTH PREMIUM", "-412.85"],
            ),
            (
                "Mail/Inbox/2026-09-01 We couldnt process your premium payment.eml",
                "first decline",
                ["card declined", "$412.85"],
            ),
            (
                "Mail/Inbox/2026-10-22 FINAL NOTICE policy suspension LH-5520913.eml",
                "final notice (quoted-printable)",
                ["$1,238.55", "14 November 2026"],
            ),
            (
                "Chats/WhatsApp Chat with Gerry.txt",
                "podiatry claim knocked back",
                ["knocked back the claim"],
            ),
        ],
    ),
    (
        "N4",
        "Need",
        "Her best friend Mags, widowed in June, is withdrawing and Bernie "
        "keeps not ringing; Mags's birthday is 30 Oct",
        "relationship, emotional",
        [
            (
                "Chats/WhatsApp Chat with Mags Doyle.txt",
                "warm, then short; last reply 'Don't worry about me love'",
                ["Terry's gone Bernie", "Don't worry about me love"],
            ),
            (
                "Mail/Local Folders/WPBC.mbox",
                "club email: Mags stepped back from pennant",
                ["stepped back from Pennant", "Terry Doyle"],
            ),
            (
                "Notes/Bernie's Vault/Daily/2026-09-06.md",
                "saw her, didn't go over",
                ["Didn't go over", "ring Mags"],
            ),
            (
                "Notes/Bernie's Vault/Daily/2026-10-04.md",
                "still unticked",
                ["- [ ] ring Mags"],
            ),
            ("Contacts/contacts.vcf", "Mags's birthday", ["BDAY:1957-10-30"]),
            (
                "Calendar/Home.ics",
                "birthday lunch was a yearly habit; 'Coffee w Mags' stops in June",
                ["Lunch with Mags (her birthday)", "UNTIL=20260601"],
            ),
        ],
    ),
    (
        "N5",
        "Need",
        "She promised Aoife Nana Peg's sapphire ring at 21 (12 Dec 2026); it "
        "needs 4–6 weeks of repair and is still in the wardrobe",
        "forgotten promise",
        [
            (
                "Mail/Sent/2022-12-12 Happy 17th to our Aoife.eml",
                "the written promise",
                ["when she turns 21", "Nana Peg's sapphire", "I promise"],
            ),
            ("Contacts/contacts.vcf", "Aoife Pettit's birthday", ["BDAY:2005-12-12"]),
            (
                "Notes/Bernie's Vault/Daily/2024-06-09.md",
                "ring found, claw lifting",
                ["blue box", "claws is lifting"],
            ),
            (
                "Mail/Inbox/2026-03-09 Re enquiry - sapphire ring claws.eml",
                "jeweller: $285, 4–6 weeks, longer from November",
                ["$285", "4–6 weeks"],
            ),
            (
                "Chats/WhatsApp Chat with Siobhán.txt",
                "the 21st is booked for 12 Dec",
                ["Sat 12 Dec", "I have something for her too"],
            ),
            ("Calendar/Home.ics", "the party", ["Aoife's 21st – Lake View Hotel"]),
        ],
    ),
    (
        "N6",
        "Need",
        "The self-lodged 2025-26 tax return (with the rental) is due 31 Oct "
        "2026 and stuck on the depreciation schedule",
        "deadline, admin",
        [
            (
                "Calendar/Home.ics",
                "TAX DUE all-day 31 Oct 2026",
                ["TAX DUE (self lodge)", "rental schedule"],
            ),
            (
                "Notes/Bernie's Vault/Tax 2025-26.md",
                "checklist half done",
                ["31 Oct", "depreciation schedule"],
            ),
            (
                "Documents/Rental unit 2025-26.xlsx",
                "rental workbook, blanks for rates, water, depreciation",
                ["21840", "BMT report 2019"],
            ),
            (
                "Documents/Scans/CorioBay_EOFY_Statement_2026.pdf",
                "agent statement",
                ["21,840.00", "2/41 Weller Street"],
            ),
            (
                "Chats/WhatsApp Chat with Siobhán.txt",
                "Tim offers help; 'due the 31st'",
                ["Tim says he can look over the rental bit", "due the 31st"],
            ),
            (
                "Notes/Bernie's Vault/Daily/2026-10-17.md",
                "started, stuck",
                ["Where is the depreciation schedule"],
            ),
        ],
    ),
    (
        "N7",
        "Need",
        "The roof leak over Kieran's room is getting worse; the quote "
        "expired and insurance won't cover gradual damage",
        "slow-burning practical",
        [
            (
                "Notes/Bernie's Vault/Daily/2025-06-03.md",
                "first drip",
                ["Drip in Kieran's room"],
            ),
            (
                "Mail/Inbox/2026-05-20 Quote Q-2291 27 Kellett St.eml",
                "quote, valid 30 days (quoted-printable)",
                ["$2,350.00", "valid 30 days", "valley flashing"],
            ),
            (
                "Notes/Bernie's Vault/Daily/2026-06-22.md",
                "insurer: not covered",
                ["gradual leaks not covered"],
            ),
            (
                "Chats/Telegram/ChatExport_2026-10-24/result.json",
                "Kieran: dripping again",
                ["brown patch above my bed", "ceilings dripping again"],
            ),
            (
                "Notes/Bernie's Vault/Daily/2026-10-09.md",
                "bucket half full",
                ["Bucket in Kieran's room"],
            ),
            (
                "Calendar/Home.ics",
                "a 2025 roof inspection, cancelled",
                ["Roof inspection – Ballarat Roof Restorations"],
            ),
        ],
    ),
    (
        "T1",
        "Trap",
        "A phishing 'ATO refund' email looks like an answer about tax",
        "",
        [
            (
                "Mail/Inbox/2026-10-15 ATO You have a pending tax refund of 128460.eml",
                "spoofed sender domain, 48-hour threat",
                ["$1,284.60", "ato-gov-au-refund.com"],
            ),
            (
                "Mail/Inbox/2026-07-03 You have a new message in your myGov Inbox.eml",
                "the genuine myGov notice, for contrast",
                ["never send you a link"],
            ),
        ],
    ),
    (
        "T2",
        "Trap",
        "Last year's rego notice and payment ($874.10, 03/11/2025)",
        "",
        [
            (
                "Mail/Inbox/2025-10-07 Registration renewal notice SUBARU FORESTER 1XY4KD.eml",
                "superseded notice",
                ["$874.10", "03/11/2025"],
            ),
            (
                "Notes/Bernie's Vault/Daily/2025-10-29.md",
                "'Paid the rego online' - last year",
                ["Paid the rego online, $874.10"],
            ),
            (
                "Documents/Household budget 2026.xlsx",
                "an estimate, not the bill",
                ["est. 880 for the year"],
            ),
        ],
    ),
    (
        "T3",
        "Trap",
        "Calendar still shows a confirmed 5 Nov dermatology appointment "
        "that the clinic cancelled",
        "",
        [
            (
                "Calendar/Home.ics",
                "CONFIRMED, alarm set",
                ["Dermatology – Dr Rao", "booked 20/8 by phone"],
            ),
            (
                "Mail/Inbox/2026-08-20 Appointment confirmation Lydiard Dermatology.eml",
                "the original confirmation",
                ["Thursday 5 November 2026 at 9:15am"],
            ),
            (
                "Mail/Inbox/2026-10-02 Your appointment has been cancelled.eml",
                "the cancellation that overrides it",
                ["unexpected leave"],
            ),
        ],
    ),
    (
        "T4",
        "Trap",
        "A draft rental CSV totals $20,160 (48 weeks), not the real $21,840",
        "",
        [
            (
                "Downloads/rental_fy26_draft.csv",
                "4 weeks x 12 months",
                ["TOTAL,48,20160"],
            ),
            (
                "Documents/Rental unit 2025-26.xlsx",
                "the right 52-week total",
                ["matches Leanne's statement"],
            ),
            (
                "Mail/Inbox/2025-07-11 EOFY owner statement 241 Weller St.eml",
                "last year's gross rent $21,060",
                ["$21,060.00"],
            ),
        ],
    ),
    (
        "T5",
        "Trap",
        "Aoife Brennan (bowls friend, b. 3 Dec 1958) vs granddaughter Aoife Pettit",
        "",
        [
            (
                "Contacts/contacts.vcf",
                "two Aoifes, two birthdays",
                ["FN:Aoife Brennan", "BDAY:1958-12-03"],
            ),
            (
                "Calendar/Home.ics",
                "'Aoife B bday (bowls)' yearly 3 Dec",
                ["Aoife B bday (bowls)"],
            ),
            (
                "Calendar/WPBC Pennant 2026-27.ics",
                "A Brennan on Bernie's rink",
                ["A Brennan"],
            ),
        ],
    ),
]


def norm(s):
    return " ".join(html.unescape(s).split())


def strip_tags(s):
    return re.sub(r"<[^>]+>", " ", s)


def pdf_text(data):
    out = []
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", data, re.S):
        for s in re.finditer(rb"\(((?:\\.|[^\\()])*)\)", m.group(1)):
            out.append(re.sub(rb"\\(.)", rb"\1", s.group(1)).decode("latin-1"))
    return "\n".join(out)


def mail_text(raw):
    msg = message_from_bytes(raw, policy=policy.default)
    out = [str(msg.get("Subject", "")), str(msg.get("From", ""))]
    for part in msg.walk():
        if part.is_multipart():
            continue
        ct = part.get_content_type()
        if ct.startswith("text/"):
            t = part.get_content()
            out.append(strip_tags(t) if ct == "text/html" else t)
        elif ct == "application/pdf":
            out.append(pdf_text(part.get_payload(decode=True)))
    return "\n".join(out)


def json_strings(obj):
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in json_strings(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in json_strings(v)]
    return [str(obj)]


def file_text(path, data):
    ext = path.rsplit(".", 1)[-1].lower()
    if ext in ("docx", "xlsx", "odt", "epub"):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            return "\n".join(
                strip_tags(z.read(n).decode("utf-8"))
                for n in z.namelist()
                if n.endswith((".xml", ".xhtml", ".opf"))
            )
    if ext == "pdf":
        return pdf_text(data)
    if ext == "eml":
        return mail_text(data)
    if ext == "mbox":
        chunks = re.split(rb"\n(?=From \S+ \w{3} \w{3} )", data)
        return "\n".join(mail_text(c.split(b"\n", 1)[1]) for c in chunks)
    if ext == "json":
        return "\n".join(json_strings(json.loads(data.decode("utf-8"))))
    text = data.decode("utf-8-sig")
    if ext in ("ics", "vcf"):
        text = text.replace("\r\n ", "")
        text = (
            text.replace("\\n", "\n")
            .replace("\\,", ",")
            .replace("\\;", ";")
            .replace("\\\\", "\\")
        )
    return text


def check():
    problems = []
    derived = build()
    if not LIFE.is_dir():
        print("check: life/ is missing - run make_life.py first")
        return 1
    on_disk = sorted(
        p.relative_to(LIFE).as_posix() for p in LIFE.rglob("*") if p.is_file()
    )
    if on_disk != list(derived):
        extra = sorted(set(on_disk) - set(derived))
        missing = sorted(set(derived) - set(on_disk))
        problems.append(f"file list differs: extra={extra[:5]} missing={missing[:5]}")
    for path, data in derived.items():
        p = LIFE / path
        if p.is_file() and p.read_bytes() != data:
            problems.append(f"{path}: bytes differ from a fresh derivation")
    planted_md = HERE / "PLANTED.md"
    named = []
    if planted_md.is_file():
        named = re.findall(
            r"`([^`]+\.[A-Za-z0-9]{2,5})`", planted_md.read_text(encoding="utf-8")
        )
        table_paths = {pth for item in PLANTED for pth, _, _ in item[4]}
        for pth in sorted(table_paths - set(named)):
            problems.append(f"PLANTED.md does not name {pth}")
    else:
        problems.append("PLANTED.md is missing")
    for pth in named:
        if not (LIFE / pth).is_file():
            problems.append(f"PLANTED.md names {pth}, not in life/")
    for pid, _, _, _, pieces in PLANTED:
        for pth, _, facts in pieces:
            p = LIFE / pth
            if not p.is_file():
                problems.append(f"{pid}: {pth} missing")
                continue
            text = norm(file_text(pth, p.read_bytes()))
            for fact in facts:
                if norm(fact) not in text:
                    problems.append(f"{pid}: {pth} lacks {fact!r}")
    if problems:
        for pr in problems:
            print("check: " + pr)
        return 1
    needs = [x[0] for x in PLANTED if x[0].startswith("N")]
    traps = [x[0] for x in PLANTED if x[0].startswith("T")]
    print(f"check: {needs[0]}..{needs[-1]} and {traps[0]}..{traps[-1]} hold")
    return 0


def planted_md():
    out = [
        f"# PLANTED — Bernadette Halloran\n\nTODAY = {TODAY.isoformat()}\n\n"
        "Paths are relative to `life/`. Each need is evidenced only by pieces spread "
        "across files; no single file states it.\n"
    ]
    for pid, kind, title, flavour, pieces in PLANTED:
        out.append(
            f"\n## {pid} ({kind}{', ' + flavour if flavour else ''}) — {title}\n"
        )
        for pth, what, facts in pieces:
            out.append(
                f"- `{pth}` — {what}. Key text: " + "; ".join(f'"{f}"' for f in facts)
            )
    return "\n".join(out) + "\n"


def write():
    files = build()
    if LIFE.exists():
        shutil.rmtree(LIFE)
    for path, data in files.items():
        p = LIFE / path
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(data)
    print(f"wrote {len(files)} files to life/")


def main(argv):
    if "--check" in argv:
        return check()
    if "--planted" in argv:
        build()
        sys.stdout.write(planted_md())
        return 0
    write()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
