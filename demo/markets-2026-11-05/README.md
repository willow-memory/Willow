# markets-2026-11-05

A broad equities and macro pile, from public sources, fetched once on
2026-11-05 and checked offline after that: 944 sources, 665 MB as fetched,
1,297 files once mirrored for the kernel (about 25 minutes, most of it
reading the XBRL company facts).

    python demo/markets-2026-11-05/fetch.py --to PILE --contact EMAIL   # online, once
    python demo/markets-2026-11-05/fetch.py --to PILE --check     # offline: holds, DIFFERS, missing
    python demo/markets-2026-11-05/mirror.py --from PILE --to MIRROR
    python kernel.py init --box BOX --pile MIRROR --key KEY

The repo keeps each source's address and SHA-256 in
[sources.json](sources.json), never its bytes: the data are the publishers'.

## What's in it

| Folder | Sources | From |
|---|---|---|
| `fred/<group>` | 88 | FRED: output, prices, labor, rates, credit, money, markets, commodities, FX, housing, sentiment, fiscal; each series' whole history |
| `treasury` | 36 | Treasury par yield curve, real yield curve and bill rates, daily, 2015 to 2026 |
| `treasury-fiscal` | 3 | Debt to the penny, average interest rates, Monthly Treasury Statement table 1 |
| `fed-h15` | 1 | The Fed's H.15 selected interest rates, every series |
| `fed-fomc` | 136 | FOMC statements, minutes, projection tables, press conference pages and their PDF transcripts, 2023 to 2026, read off the Fed's calendar page |
| `nyfed` | 4 | SOFR, EFFR, TGCR, OBFR, daily since 2018 |
| `cboe` | 8 | VIX, VIX9D, VIX3M, VIX6M, VVIX, SKEW, OVX, GVZ, daily history |
| `french`, `french-csv` | 9 | Kenneth French's library: 3 and 5 factors, momentum, 12 and 49 industries, 25 size and value portfolios, developed and emerging factors; zips kept as fetched, CSVs unpacked beside them |
| `datahub` | 11 | datahub.io core finance sets: Shiller's monthly S&P 500, S&P 500 constituents and financials, VIX, gold, WTI, Brent, CPI, 10-year yield, Nasdaq and NYSE listings |
| `listings` | 2 | Nasdaq Trader's symbol directories, Nasdaq and other-listed |
| `bls` | 4 | BLS's own API for CPI, average hourly earnings, unemployment and payrolls, the same numbers FRED republishes |
| `worldbank` | 8 | G20, 1990 to 2026: GDP growth and level, inflation, unemployment, current account, market cap, real rates, trade |
| `imf-weo` | 7 | IMF World Economic Outlook: growth, inflation, unemployment, debt, current account, GDP, fiscal balance, with projections |
| `ecb` | 5 | EUR/USD, EUR/JPY, the deposit rate, HICP and core HICP |
| `oecd` | 1 | Composite leading indicators, G7, monthly since 2000 |
| `sec/submissions` | 504 | SEC EDGAR's filing index for every S&P 500 constituent: each filing's form, date and document |
| `sec/companyfacts` | 56 | EDGAR's XBRL company facts (every reported figure, every period) for the five largest companies in each GICS sector |
| `sec/10-k` | 55 | The same 55 companies' latest 10-K, as filed |

The five per sector are ranked by the market cap in datahub's financials
file, a way of choosing, not a valuation. One constituent needed a hand:
the list now gives XOM's CIK as ExxonMobil Holdings Corp (2115436), a
successor formed by holding-company reorganization in 2026 that hasn't
filed a 10-K yet, so the latest 10-K and its company facts come from the
predecessor, Exxon Mobil Corp (34088), filed beside it as
`XOM.predecessor.json`. That's `PREDECESSOR` in fetch.py.
| `nowcasts`, `bea` | 3 | Atlanta Fed GDPNow, the Philadelphia Fed's fourth-quarter 2026 Survey of Professional Forecasters, BEA's current releases |

The same number from two publishers is here on purpose (CPI from BLS, FRED
and datahub; VIX from CBOE, FRED and datahub; the 10-year from Treasury,
H.15, FRED and datahub), so `contradictions` and `duplicates` have real
work to do, and the FOMC text against the series it talks about gives
`said`, `quotes` and `claim-check` theirs.

## Not here, and why

- **SEC EDGAR without `--contact`**: SEC refuses a client whose
  User-Agent names no contact email, so EDGAR is skipped unless one is
  given. The email goes to sec.gov in the request header only (the snapshot
  add-on's `--contact`), never into a log line, sources.json or this repo.
- **BLS release pages** refuse scripted reads; the API is used instead.
  Without a key it allows few requests a day, so a series that hit the
  limit is set aside in `PILE/.refused`, listed under `failed`, and fetched
  again under a new name (`NAME.try2.json`) on the next run.
- **Census** retail sales now need an API key; FRED's `RSAFS` and `RRSFS`
  carry the same series.
- **Old .xls workbooks** (Damodaran's, the NY Fed's) have no reader in
  willow yet.
- **Market prices for single stocks** come only from sources whose terms
  forbid scripted downloads, so the pile has each company's filings and
  reported figures, and prices only at the index level.

## How the pile is kept honest

- Every file is the snapshot add-on's: as it came, with its address, time
  and SHA-256, and fetched once. A rerun fills gaps and never overwrites.
- A 200 that carried an error (an HTML page where a CSV was asked for, a
  BLS limit message) is moved to `PILE/.refused`, not kept as data.
- `mirror.py` cuts any mirrored file over the kernel's 1 MB into parts with
  the text add-on, so nothing the readers wrote is silently dropped.
