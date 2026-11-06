"""Fetch a broad equities and macro pile from public sources, once, and check it offline.

    python demo/markets-2026-11-05/fetch.py --to PILE [--contact EMAIL]   # online, once
    python demo/markets-2026-11-05/fetch.py --to PILE --check    # offline
    python demo/markets-2026-11-05/fetch.py --list               # the sources, no fetching

Every source is saved by the snapshot add-on, as it came, into a folder of
its own under PILE, with its address, the time and its SHA-256 in that
folder's .snapshots.jsonl. Two kinds of source are found from pages fetched
first, not listed by hand: the Federal Reserve's FOMC statements, minutes,
projections and press conference transcripts (read off its calendar page),
and the PDF transcript each press-conference page links; and SEC EDGAR's
filing index for every S&P 500 constituent, with full XBRL company facts and
the latest 10-K for the five largest in each sector (read off the
constituents file fetched first). SEC refuses a client that names no
contact, so EDGAR is fetched only with --contact, and the email goes in the
User-Agent to sec.gov alone, never into a line or this repo. Zipped CSVs (the Fama-French library) are fetched as they
came and unpacked beside them into PILE/french-csv, each unpacked file with
the SHA-256 of the zip it came from in .unpacked.jsonl.

`--check` goes nowhere. It hashes every file in PILE against
[sources.json](sources.json), the frozen record of what was fetched, and
says `holds`, `DIFFERS` or `missing` for each. After the fetch, nothing in
the study goes online: every answer comes from these files.

The data are the publishers', not this repo's, so the repo keeps their
hashes, never their bytes. Not here, and why: BLS's release pages refuse scripted
reads (its API is used instead); old .xls workbooks (Damodaran, NY Fed)
have no reader in willow yet.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SNAPSHOT = ROOT / "adapters" / "stdlib" / "snapshot" / "snapshot.py"
FED = "https://www.federalreserve.gov"
YEARS = range(2023, 2027)  # FOMC documents, and the Treasury curves below
CURVE_YEARS = range(2015, 2027)
PAUSE = 0.4  # seconds between fetches, to be polite to small servers

# --- FRED: one CSV per series, its whole history --------------------------------
FRED_SERIES = {
    "output": "GDP GDPC1 A191RL1Q225SBEA INDPRO TCU DGORDER RSAFS RRSFS PCE PCEC96",
    "prices": "CPIAUCSL CPILFESL PCEPI PCEPILFE PPIACO T5YIE T10YIE MICH CUSR0000SAH1",
    "labor": "UNRATE U6RATE PAYEMS ICSA CCSA CIVPART LNS12300060 JTSJOL JTSQUR CES0500000003 AHETPI",
    "rates": "FEDFUNDS DFF SOFR DGS1MO DGS3MO DGS6MO DGS1 DGS2 DGS5 DGS10 DGS30 T10Y2Y T10Y3M DFII10 MORTGAGE30US",
    "credit": "BAMLH0A0HYM2 BAMLC0A0CM BAMLC0A4CBBB AAA BAA BUSLOANS TOTALSL DRCCLACBS NFCI STLFSI4",
    "money": "M2SL WALCL RRPONTSYD WTREGEN TOTRESNS",
    "markets": "SP500 NASDAQCOM DJIA VIXCLS",
    "commodities": "DCOILWTICO DCOILBRENTEU DHHNGSP PCOPPUSDM PALLFNFINDEXM",
    "fx": "DTWEXBGS DEXUSEU DEXJPUS DEXCHUS DEXUSUK DEXCAUS DEXMXUS",
    "housing": "HOUST PERMIT CSUSHPINSA MSPUS EXHOSLUSM495S",
    "sentiment": "UMCSENT USREC USSLIND",
    "fiscal": "GFDEBTN FYFSD GFDEGDQ188S A091RC1Q027SBEA",
}  # fmt: skip

# --- BLS's own API, for the same numbers FRED republishes ------------------------
BLS_SERIES = (
    "CUUR0000SA0 CUUR0000SA0L1E LNS14000000 CES0000000001 CES0500000003 WPUFD4".split()
)

# --- The world, by country --------------------------------------------------------
G20 = "ARG;AUS;BRA;CAN;CHN;FRA;DEU;IND;IDN;ITA;JPN;KOR;MEX;RUS;SAU;ZAF;TUR;GBR;USA"
WB_INDICATORS = {
    "gdp-growth": "NY.GDP.MKTP.KD.ZG",
    "gdp-usd": "NY.GDP.MKTP.CD",
    "inflation": "FP.CPI.TOTL.ZG",
    "unemployment": "SL.UEM.TOTL.ZS",
    "current-account": "BN.CAB.XOKA.GD.ZS",
    "market-cap": "CM.MKT.LCAP.GD.ZS",
    "real-interest": "FR.INR.RINR",
    "trade": "NE.TRD.GNFS.ZS",
}
IMF_INDICATORS = "NGDP_RPCH PCPIPCH LUR GGXWDG_NGDP BCA_NGDPD NGDPD GGXCNL_NGDP".split()
ECB_SERIES = {
    "eurusd": "EXR/D.USD.EUR.SP00.A",
    "eurjpy": "EXR/D.JPY.EUR.SP00.A",
    "deposit-rate": "FM/D.U2.EUR.4F.KR.DFR.LEV",
    "hicp": "ICP/M.U2.N.000000.4.ANR",
    "hicp-core": "ICP/M.U2.N.XEF000.4.ANR",
}
CBOE = "VIX VIX9D VIX3M VIX6M VVIX SKEW OVX GVZ".split()
FRENCH = [
    "F-F_Research_Data_Factors", "F-F_Research_Data_Factors_daily",
    "F-F_Research_Data_5_Factors_2x3", "F-F_Momentum_Factor",
    "12_Industry_Portfolios", "49_Industry_Portfolios", "25_Portfolios_5x5",
    "Developed_3_Factors", "Emerging_5_Factors",
]  # fmt: skip
DATAHUB = [
    ("s-and-p-500", "data.csv", "sp500-shiller-monthly.csv"),
    ("s-and-p-500-companies", "constituents.csv", "sp500-constituents.csv"),
    ("s-and-p-500-companies-financials", "constituents-financials.csv",
     "sp500-constituents-financials.csv"),
    ("finance-vix", "vix-daily.csv", "vix-daily-datahub.csv"),
    ("gold-prices", "monthly.csv", "gold-monthly.csv"),
    ("oil-prices", "wti-daily.csv", "wti-daily-datahub.csv"),
    ("oil-prices", "brent-daily.csv", "brent-daily-datahub.csv"),
    ("cpi-us", "cpiai.csv", "cpi-us-datahub.csv"),
    ("bond-yields-us-10y", "monthly.csv", "us-10y-monthly-datahub.csv"),
    ("nasdaq-listings", "nasdaq-listed.csv", "nasdaq-listed-datahub.csv"),
    ("nyse-other-listings", "other-listed.csv", "nyse-other-listed-datahub.csv"),
]  # fmt: skip


def static_sources() -> list[tuple[str, str, str]]:
    """(folder, file name, address) for every source listed by hand."""
    out: list[tuple[str, str, str]] = []
    for group, ids in FRED_SERIES.items():
        for sid in ids.split():
            out.append((f"fred/{group}", f"{sid}.csv",
                        f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"))  # fmt: skip
    for sid in BLS_SERIES:
        out.append(
            (
                "bls",
                f"{sid}.json",
                f"https://api.bls.gov/publicAPI/v2/timeseries/data/{sid}",
            )
        )
    tre = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates"
    for y in CURVE_YEARS:
        for kind in ("daily_treasury_yield_curve", "daily_treasury_real_yield_curve",
                     "daily_treasury_bill_rates"):  # fmt: skip
            out.append(("treasury", f"{kind}_{y}.csv",
                        f"{tre}/daily-treasury-rates.csv/{y}/all?type={kind}"
                        f"&field_tdr_date_value={y}&page&_format=csv"))  # fmt: skip
    fd = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
    for name, path in [("debt-to-penny", "v2/accounting/od/debt_to_penny"),
                       ("avg-interest-rates", "v2/accounting/od/avg_interest_rates"),
                       ("mts-receipts-outlays", "v1/accounting/mts/mts_table_1")]:  # fmt: skip
        out.append(("treasury-fiscal", f"{name}.csv",
                    f"{fd}/{path}?format=csv&page[size]=10000&sort=-record_date"))  # fmt: skip
    out.append(
        (
            "fed-h15",
            "h15-all.csv",
            f"{FED}/datadownload/Output.aspx?rel=H15&series=bf17364827e38702b42a58cf8eaa3f78"
            "&lastobs=&from=&to=&filetype=csv&label=include&layout=seriescolumn&type=package",
        )
    )
    nyf = "https://markets.newyorkfed.org/api/rates"
    for rate in ("secured/sofr", "unsecured/effr", "secured/tgcr", "unsecured/obfr"):
        out.append(("nyfed", f"{rate.split('/')[1]}.json",
                    f"{nyf}/{rate}/search.json?startDate=2018-04-02&endDate=2026-11-05"))  # fmt: skip
    for x in CBOE:
        out.append(
            (
                "cboe",
                f"{x}_History.csv",
                f"https://cdn.cboe.com/api/global/us_indices/daily_prices/{x}_History.csv",
            )
        )
    ff = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp"
    for x in FRENCH:
        out.append(("french", f"{x}_CSV.zip", f"{ff}/{x}_CSV.zip"))
    for repo, path, name in DATAHUB:
        out.append(
            (
                "datahub",
                name,
                f"https://raw.githubusercontent.com/datasets/{repo}/main/data/{path}",
            )
        )
    for name, ind in WB_INDICATORS.items():
        out.append(("worldbank", f"{name}.json",
                    f"https://api.worldbank.org/v2/country/{G20}/indicator/{ind}"
                    "?format=json&per_page=2000&date=1990:2026"))  # fmt: skip
    for ind in IMF_INDICATORS:
        out.append(
            (
                "imf-weo",
                f"{ind}.json",
                f"https://www.imf.org/external/datamapper/api/v1/{ind}",
            )
        )
    for name, key in ECB_SERIES.items():
        out.append(("ecb", f"{name}.csv",
                    f"https://data-api.ecb.europa.eu/service/data/{key}"
                    "?format=csvdata&startPeriod=1999-01-01"))  # fmt: skip
    oecd = "https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_CLI,4.1"
    out.append(("oecd", "cli-g7.csv",
                f"{oecd}/USA+GBR+JPN+DEU+FRA+ITA+CAN.M.LI...AA...H"
                "?startPeriod=2000-01&format=csvfilewithlabels"))  # fmt: skip
    nq = "https://www.nasdaqtrader.com/dynamic/SymDir"
    out += [("listings", "nasdaqlisted.txt", f"{nq}/nasdaqlisted.txt"),
            ("listings", "otherlisted.txt", f"{nq}/otherlisted.txt")]  # fmt: skip
    out += [
        ("nowcasts", "gdpnow.html", "https://www.atlantafed.org/cqer/research/gdpnow"),
        (
            "nowcasts",
            "spf-q4-2026.html",
            "https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/spf-q4-2026",
        ),
        ("bea", "current-releases.html", "https://www.bea.gov/news/current-releases"),
        ("fed-fomc", "calendar.html", f"{FED}/monetarypolicy/fomccalendars.htm"),
    ]
    return out


FOMC_LINK = re.compile(
    r'href="(/(?:newsevents/pressreleases/monetary(20\d{6})a|monetarypolicy/fomcminutes(20\d{6})'
    r'|monetarypolicy/fomcprojtabl(20\d{6})|monetarypolicy/fomcpresconf(20\d{6}))\.htm)"'
)
PRESCONF_PDF = re.compile(
    r'href="(/mediacenter/files/FOMCpresconf(20\d{6})\.pdf)"', re.I
)


def fomc_sources(calendar: Path) -> list[tuple[str, str, str]]:
    """Statements, minutes, projections and press conferences, read off the calendar page."""
    html = calendar.read_text(encoding="utf-8", errors="replace")
    out = []
    for m in FOMC_LINK.finditer(html):
        path = m.group(1)
        day = next(g for g in m.groups()[1:] if g)
        if int(day[:4]) not in YEARS:
            continue
        kind = ("statements" if "monetary" in path and "pressreleases" in path
                else "minutes" if "minutes" in path
                else "projections" if "projtabl" in path else "presconf")  # fmt: skip
        out.append((f"fed-fomc/{kind}", f"{day}.html", FED + path))
    return sorted(set(out))


def presconf_pdfs(folder: Path) -> list[tuple[str, str, str]]:
    out = []
    for page in sorted(folder.glob("*.html")):
        for m in PRESCONF_PDF.finditer(
            page.read_text(encoding="utf-8", errors="replace")
        ):
            out.append(
                ("fed-fomc/presconf-transcripts", f"{m.group(2)}.pdf", FED + m.group(1))
            )
    return sorted(set(out))


SEC = "https://data.sec.gov"
PER_SECTOR = 5  # companies per sector given company facts and their latest 10-K
#: A constituent whose CIK is a new successor that hasn't filed a 10-K yet, and the
#: predecessor that did. ExxonMobil Holdings Corp (2115436) succeeded Exxon Mobil
#: Corp (34088) by holding-company reorganization in 2026 (its 8-K12B).
PREDECESSOR = {"XOM": 34088}


def constituents(pile: Path) -> list[dict]:
    with open(
        pile / "datahub" / "sp500-constituents.csv", encoding="utf-8", newline=""
    ) as f:
        return [r for r in csv.DictReader(f) if r.get("CIK", "").strip().isdigit()]


def largest_by_sector(pile: Path) -> list[dict]:
    """The PER_SECTOR largest companies of each GICS sector, by the market cap
    in datahub's financials file: a ranking for choosing, not a valuation."""
    with open(pile / "datahub" / "sp500-constituents-financials.csv", encoding="utf-8",
              newline="") as f:  # fmt: skip
        cap = {r["Symbol"]: float(r["Market Cap"] or 0) for r in csv.DictReader(f)}
    by: dict[str, list[dict]] = {}
    for r in constituents(pile):
        if r["Symbol"] in cap:
            by.setdefault(r["GICS Sector"], []).append(r)
    out = []
    for sector in sorted(by):
        seen: set[str] = set()  # one company, one CIK: GOOGL and GOOG count once
        for r in sorted(by[sector], key=lambda r: (-cap[r["Symbol"]], r["Symbol"])):
            if r["CIK"] not in seen and len(seen) < PER_SECTOR:
                seen.add(r["CIK"])
                out.append(r)
    return out


def sec_sources(pile: Path) -> list[tuple[str, str, str]]:
    out = [
        (
            "sec",
            "company_tickers.json",
            "https://www.sec.gov/files/company_tickers.json",
        )
    ]
    for r in constituents(pile):
        out.append(("sec/submissions", f"{r['Symbol']}.json",
                    f"{SEC}/submissions/CIK{int(r['CIK']):010d}.json"))  # fmt: skip
    for sym, cik in sorted(PREDECESSOR.items()):
        out.append(("sec/submissions", f"{sym}.predecessor.json",
                    f"{SEC}/submissions/CIK{cik:010d}.json"))  # fmt: skip
        out.append(("sec/companyfacts", f"{sym}.predecessor.json",
                    f"{SEC}/api/xbrl/companyfacts/CIK{cik:010d}.json"))  # fmt: skip
    for r in largest_by_sector(pile):
        out.append(("sec/companyfacts", f"{r['Symbol']}.json",
                    f"{SEC}/api/xbrl/companyfacts/CIK{int(r['CIK']):010d}.json"))  # fmt: skip
    return out


def latest_10k(pile: Path) -> list[tuple[str, str, str]]:
    """Each chosen company's latest 10-K, read off its filing index."""
    out = []
    for r in largest_by_sector(pile):
        sub = pile / "sec" / "submissions" / f"{r['Symbol']}.json"
        if not sub.is_file():
            continue
        index = json.loads(sub.read_text(encoding="utf-8"))["filings"]
        pages = [(int(r["CIK"]), index["recent"])]
        pred = pile / "sec" / "submissions" / f"{r['Symbol']}.predecessor.json"
        if pred.is_file():
            pages.append(
                (
                    PREDECESSOR[r["Symbol"]],
                    json.loads(pred.read_text(encoding="utf-8"))["filings"]["recent"],
                )
            )
        for older in index.get(
            "files", []
        ):  # a busy filer's 10-K can fall off "recent"
            page = (
                pile
                / "sec"
                / "submissions"
                / f"{r['Symbol']}.{Path(older['name']).stem}.json"
            )
            if page.is_file():
                pages.append(
                    (int(r["CIK"]), json.loads(page.read_text(encoding="utf-8")))
                )
        found = next(((cik, day, acc, doc) for cik, pg in pages
                      for form, acc, day, doc in zip(pg["form"], pg["accessionNumber"],
                                                     pg["filingDate"], pg["primaryDocument"])
                      if form == "10-K"), None)  # fmt: skip
        if found:
            cik, day, acc, doc = found
            out.append(("sec/10-k", f"{r['Symbol']}-{day}{Path(doc).suffix or '.htm'}",
                        f"https://www.sec.gov/Archives/edgar/data/{cik}/"
                        f"{acc.replace('-', '')}/{doc}"))  # fmt: skip
        else:
            for older in index.get("files", [])[:1]:
                out.append(("sec/submissions",
                            f"{r['Symbol']}.{Path(older['name']).stem}.json",
                            f"{SEC}/submissions/{older['name']}"))  # fmt: skip
    return out


def snap(
    pile: Path, folder: str, name: str, url: str, contact: str | None = None
) -> int:
    if (pile / folder / name).exists():
        return 0  # fetched once: a rerun fills gaps, never refetches
    log = pile / folder / ".snapshots.jsonl"
    tried = ({json.loads(x).get("file") for x in log.read_text(encoding="utf-8").splitlines()}
             if log.is_file() else set())  # fmt: skip
    stem, suffix, n = Path(name).stem, Path(name).suffix, 1
    while name in tried:  # a refused copy keeps its name; a retry takes the next one
        n += 1
        name = f"{stem}.try{n}{suffix}"
        if (pile / folder / name).exists():
            return 0
    got = subprocess.run(
        [
            sys.executable,
            str(SNAPSHOT),
            "fetch",
            "--url",
            url,
            "--to",
            str(pile / folder),
            "--name",
            name,
        ]  # fmt: skip
        + (["--contact", contact] if contact and ".sec.gov/" in url else []),
        capture_output=True,
        text=True,
    )
    print(
        f"{'ok  ' if got.returncode == 0 else 'FAIL'} {folder}/{name}"
        + ("" if got.returncode == 0 else f"  {got.stderr.strip()[:120]}"),
        flush=True,
    )
    time.sleep(PAUSE)
    return got.returncode


def error_body(path: Path) -> str | None:
    """Why a file that came with a 200 is an error, not data, or None."""
    head = path.read_bytes()[:4096].lstrip().lower()
    if path.suffix in (".csv", ".json", ".txt") and head.startswith(
        (b"<!doctype", b"<html")
    ):
        return "an HTML page where data was asked for"
    if path.parent.name == "bls":
        status = json.loads(path.read_text(encoding="utf-8")).get("status")
        if status != "REQUEST_SUCCEEDED":
            return f"BLS answered {status} (its daily limit, without a key)"
    return None


def refuse(pile: Path) -> None:
    """Error bodies moved to PILE/.refused, so the pile holds data only and a rerun retries them."""
    for log in sorted(pile.rglob(".snapshots.jsonl")):
        if ".refused" in log.parts:
            continue
        kept = []
        for line in log.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            p = log.parent / (r.get("file") or ".none")
            why = error_body(p) if r.get("sha256") and p.is_file() else None
            if why:
                dest = pile / ".refused" / log.parent.relative_to(pile)
                dest.mkdir(parents=True, exist_ok=True)
                p.replace(dest / p.name)
                r = {**r, "why": why, "refused": True}
                r.pop("sha256")
                print(
                    f"REFUSED {log.parent.relative_to(pile).as_posix()}/{p.name}: {why}"
                )
            kept.append(json.dumps(r, sort_keys=True))
        log.write_text("".join(k + "\n" for k in kept), encoding="utf-8")


def unpack(pile: Path) -> None:
    """Each Fama-French zip's CSVs beside it, with the zip's SHA-256."""
    src, dst = pile / "french", pile / "french-csv"
    dst.mkdir(parents=True, exist_ok=True)
    log = []
    for z in sorted(src.glob("*.zip")):
        zsha = hashlib.sha256(z.read_bytes()).hexdigest()
        with zipfile.ZipFile(z) as zf:
            for info in zf.infolist():
                name = Path(info.filename).name
                if not name or info.is_dir():
                    continue
                data = zf.read(info)
                (dst / name).write_bytes(data)
                log.append({"file": name, "from": z.name, "from_sha256": zsha,
                            "sha256": hashlib.sha256(data).hexdigest()})  # fmt: skip
    (dst / ".unpacked.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in log), encoding="utf-8"
    )


def fetch(pile: Path, contact: str | None = None) -> int:
    worst = 0
    for s in static_sources():
        worst = max(worst, snap(pile, *s))
    cal = pile / "fed-fomc" / "calendar.html"
    if cal.is_file():
        for s in fomc_sources(cal):
            worst = max(worst, snap(pile, *s))
        for s in presconf_pdfs(pile / "fed-fomc" / "presconf"):
            worst = max(worst, snap(pile, *s))
    if contact and (pile / "datahub" / "sp500-constituents.csv").is_file():
        for s in sec_sources(pile):
            worst = max(worst, snap(pile, *s, contact=contact))
        for _ in range(
            2
        ):  # a second pass reads the older index pages the first fetched
            for s in latest_10k(pile):
                worst = max(worst, snap(pile, *s, contact=contact))
    elif not contact:
        print("SEC EDGAR skipped: it needs --contact EMAIL")
    refuse(pile)
    unpack(pile)
    freeze(pile)
    return worst


def freeze(pile: Path) -> None:
    """sources.json: every file fetched, its address and SHA-256, and what failed."""
    rows, failed = [], []
    for log in sorted(pile.rglob(".snapshots.jsonl")):
        folder = log.parent.relative_to(pile).as_posix()
        for line in log.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r.get("sha256") and (log.parent / r["file"]).is_file():
                rows.append({"folder": folder, "file": r["file"], "url": r["url"],
                             "bytes": r["bytes"], "sha256": r["sha256"]})  # fmt: skip
            else:
                failed.append({"folder": folder, "url": r["url"],
                               "status": r.get("status"), "why": r.get("why")})  # fmt: skip
    latest = {
        f["url"]: f for f in failed
    }  # a source retried keeps only its last failure
    failed = [f for u, f in sorted(latest.items()) if u not in {r["url"] for r in rows}]
    body = {"fetched_for": "markets-2026-11-05", "sources": rows, "failed": failed}
    (HERE / "sources.json").write_text(json.dumps(body, indent=1, sort_keys=True) + "\n",
                                       encoding="utf-8")  # fmt: skip
    print(
        f"froze {len(rows)} sources, {len(failed)} failed, "
        f"{sum(r['bytes'] for r in rows) / 1e6:.1f} MB"
    )


def check(pile: Path) -> int:
    pins = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))["sources"]
    missing = differs = False
    for s in pins:
        p = pile / s["folder"] / s["file"]
        if not p.is_file():
            state, missing = "missing", True
        elif hashlib.sha256(p.read_bytes()).hexdigest() == s["sha256"]:
            state = "holds"
        else:
            state, differs = "DIFFERS", True
        if state != "holds":
            print(f"{state:<8} {s['folder']}/{s['file']}")
    print(f"{len(pins)} sources checked")
    return 2 if differs else 42 if missing else 0


def main(argv: list[str]) -> int:
    if argv == ["--list"]:
        for s in static_sources():
            print("\t".join(s))
        return 0
    if len(argv) == 2 and argv[0] == "--to":
        return fetch(Path(argv[1]))
    if (
        len(argv) == 4
        and argv[0] == "--to"
        and argv[2] == "--contact"
        and "@" in argv[3]
    ):
        return fetch(Path(argv[1]), argv[3])
    if len(argv) == 3 and argv[0] == "--to" and argv[2] == "--check":
        return check(Path(argv[1]))
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
