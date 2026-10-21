#!/usr/bin/env python3
"""
Part 2 — Proxy-statement (DEF 14A) collection scaffold (Wharton People Analytics RA task).

Why proxy statements: see part2_source_decision.md. In short, DEF 14A is a
mandatory annual SEC filing, so one API (SEC EDGAR) yields near-complete
2016-2024 coverage for all 50 task companies, with a consistent document type
year-over-year. Coverage spot-verified 2026-10-15/16 (US Eastern):
JPM 9/9, MSFT 9/9, GOOGL 9/9 years 2016-2024.

Pipeline
--------
1. For each of the 50 task companies (ticker -> CIK map below), query the SEC
   submissions API (recent bucket + archived "files" buckets) for DEF 14A
   filings whose proxy-year (filing year, December filings rolled to the
   next year — see proxy_year()) falls in 2016-2024.
2. Download the primary filing document from https://www.sec.gov/Archives/...
3. Extract visible body text (trafilatura preferred, BeautifulSoup fallback).
4. Write index.csv with schema:
     ticker, company_name, year, filing_date, form, accession,
     doc_url, text_path, word_count, analyst_notes
   plus one .txt per company-year under texts/.

Amendment rule: prefer the non-amended DEF 14A for a year; if only DEF 14A/A
exists, take the latest amendment and note it in analyst_notes.

XOM edge case: ExxonMobil's recent filings sit under CIK 2115436 but its
2016-2020 proxies are under legacy CIK 34088. Both are queried and merged;
2021 is missing under both (documented gap, not fabricated).

SEC fair-access rules: set CONTACT_EMAIL to your own address, keep >=0.3s
between requests, back off on 429/503. Do NOT hammer the API.

Run:
    pip install requests            # only hard dependency; trafilatura /
                                    # beautifulsoup4 are optional upgrades
    python part2_edgar_scaffold.py --out ./data
    # smoke test first:
    python part2_edgar_scaffold.py --out ./data --limit-companies 2
"""

import argparse
import csv
import json
import os
import re
import time
import urllib.request
import urllib.error

YEARS = list(range(2016, 2025))
CONTACT_EMAIL = "qingdeng@engineering.upenn.edu"  # <-- set your own per SEC rules
UA = {"User-Agent": f"WhartonRA-Part2-Research {CONTACT_EMAIL}",
      "Accept-Encoding": "identity",
      "Host": "www.sec.gov"}
UA_DATA = {"User-Agent": f"WhartonRA-Part2-Research {CONTACT_EMAIL}"}
SLEEP = 0.35

# (ticker, company_name) in PDF order; CIK from SEC company_tickers.json.
CIKS = {
    "MSFT": "789019", "AAPL": "320193", "NVDA": "1045810", "GOOGL": "1652044",
    "META": "1326801", "AVGO": "1730168", "CRM": "1108524", "ORCL": "1341439",
    "IBM": "51143", "INTC": "50863",
    "BRK.B": "1067983", "JPM": "19617", "BAC": "70858", "WFC": "72971",
    "GS": "886982", "MS": "895421", "BLK": "2012383", "SCHW": "316709",
    "AXP": "4962", "C": "831001",
    "LLY": "59478", "UNH": "731766", "JNJ": "200406", "ABBV": "1551152",
    "MRK": "310158", "TMO": "97745", "ABT": "1800", "PFE": "78003",
    "MDT": "1613103", "BMY": "14272",
    "AMZN": "1018724", "TSLA": "1318605", "HD": "354950", "MCD": "63908",
    "NKE": "320187", "SBUX": "829224", "TGT": "27419", "LOW": "60667",
    "TJX": "109198", "F": "37996",
    "XOM": "2115436", "CVX": "93410", "COP": "1163165", "EOG": "821189",
    "SLB": "87347", "MPC": "1510295", "PSX": "1534701", "VLO": "1035002",
    "OXY": "797468", "HAL": "45012",
}
# Companies whose filings span more than one CIK (merged, deduped by year).
# XOM: recent CIK 2115436 + legacy 34088 (2021 missing under both).
# BLK: BlackRock reorganized; recent CIK 2012383 covers only 2025+;
# historical DEF 14As sit under legacy CIK 1364742 (BlackRock Finance, Inc.).
EXTRA_CIKS = {"XOM": ["34088"], "BLK": ["1364742"]}
NAMES = {
    "MSFT": "Microsoft", "AAPL": "Apple", "NVDA": "NVIDIA", "GOOGL": "Alphabet",
    "META": "Meta Platforms", "AVGO": "Broadcom", "CRM": "Salesforce",
    "ORCL": "Oracle", "IBM": "IBM", "INTC": "Intel",
    "BRK.B": "Berkshire Hathaway", "JPM": "JPMorgan Chase",
    "BAC": "Bank of America", "WFC": "Wells Fargo", "GS": "Goldman Sachs",
    "MS": "Morgan Stanley", "BLK": "BlackRock", "SCHW": "Charles Schwab",
    "AXP": "American Express", "C": "Citigroup",
    "LLY": "Eli Lilly", "UNH": "UnitedHealth Group", "JNJ": "Johnson & Johnson",
    "ABBV": "AbbVie", "MRK": "Merck", "TMO": "Thermo Fisher Scientific",
    "ABT": "Abbott Laboratories", "PFE": "Pfizer", "MDT": "Medtronic",
    "BMY": "Bristol-Myers Squibb",
    "AMZN": "Amazon", "TSLA": "Tesla", "HD": "Home Depot",
    "MCD": "McDonald's", "NKE": "Nike", "SBUX": "Starbucks", "TGT": "Target",
    "LOW": "Lowe's", "TJX": "TJX Companies", "F": "Ford Motor",
    "XOM": "ExxonMobil", "CVX": "Chevron", "COP": "ConocoPhillips",
    "EOG": "EOG Resources", "SLB": "SLB (Schlumberger)",
    "MPC": "Marathon Petroleum", "PSX": "Phillips 66", "VLO": "Valero Energy",
    "OXY": "Occidental Petroleum", "HAL": "Halliburton",
}


def sec_get(url, tries=4):
    """GET with SEC politeness: backoff on 429/503."""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA_DATA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(2 ** (i + 1) * 5)
                continue
            raise
        time.sleep(SLEEP)
    raise RuntimeError(f"SEC API failed after {tries} tries: {url}")


def sec_download(url, tries=4):
    """Download a filing document and return its HTML as text.

    BUG HISTORY (2026-10-20): the first full run asked for
    Accept-Encoding: gzip but read the body with urllib, which does NOT
    decompress - the saved 'texts' were raw gzip bytes decoded with
    errors='replace', and the plausible-looking word counts were garbage
    tokens. Fixed by requesting identity encoding AND decompressing on
    magic bytes if a server gzips anyway. Guard: real extracted text must
    be mostly printable ASCII - see extract_text callers' sanity check.
    """
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read()
                enc = (r.headers.get("Content-Encoding") or "").lower()
            if raw[:2] == b"\x1f\x8b" or "gzip" in enc:
                import gzip
                raw = gzip.decompress(raw)
            elif "deflate" in enc:
                import zlib
                raw = zlib.decompress(raw)
            return raw.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(2 ** (i + 1) * 5)
                continue
            return None
        except Exception:
            time.sleep(2 ** (i + 1))
    return None


def filings_for_cik(cik):
    """All (form, filingDate, accession, primaryDoc) rows, recent + archives."""
    c = str(cik).zfill(10)
    d = sec_get(f"https://data.sec.gov/submissions/CIK{c}.json")
    rows = []
    rec = d["filings"]["recent"]
    n = len(rec["form"])
    for i in range(n):
        rows.append((rec["form"][i], rec["filingDate"][i],
                     rec["accessionNumber"][i], rec["primaryDocument"][i]))
    for f in d["filings"].get("files", []):
        sub = sec_get(f"https://data.sec.gov/submissions/{f['name']}")
        n = len(sub["form"])
        for i in range(n):
            rows.append((sub["form"][i], sub["filingDate"][i],
                         sub["accessionNumber"][i], sub["primaryDocument"][i]))
        time.sleep(SLEEP)
    return rows


def proxy_year(dt):
    """Calendar year this proxy belongs to. DEF 14A is filed 1-3 months
    BEFORE the annual meeting, so a December filing belongs to next year's
    meeting cycle (e.g. Apple's 2017-12-27 filing is its 2018 proxy).
    Documented convention; edge cases land in analyst_notes."""
    y = int(dt[:4])
    return y + 1 if dt[5:7] == "12" else y


def pick_proxy_filings(ticker):
    """One DEF 14A per proxy-year 2016-2024. Returns {year: dict}."""
    ciks = [CIKS[ticker]] + EXTRA_CIKS.get(ticker, [])
    cands = {}
    for cik in ciks:
        for form, dt, acc, prim in filings_for_cik(cik):
            y = proxy_year(dt)
            if y not in YEARS or form not in ("DEF 14A", "DEF 14A/A"):
                continue
            key = (y, form != "DEF 14A", dt)  # prefer non-amended, then latest
            if y not in cands or key < cands[y][0]:
                cands[y] = (key, {"form": form, "filing_date": dt,
                                  "accession": acc, "primary": prim, "cik": cik})
    return {y: v[1] for y, v in cands.items()}


def doc_url(cik, accession, primary):
    return (f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
            f"{accession.replace('-', '')}/{primary}")


def extract_text(html):
    """Visible body text, boilerplate stripped.
    Prefers trafilatura, then bs4, then a stdlib-only fallback so the
    script runs with nothing installed beyond `requests`."""
    try:
        import trafilatura
        t = trafilatura.extract(html, include_comments=False, include_tables=False)
        if t and len(t) > 500:
            return re.sub(r"\s+", " ", t).strip()
    except ImportError:
        pass
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        return re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()
    except ImportError:
        pass
    return _stdlib_extract(html)


class _TextParser(__import__("html.parser", fromlist=["HTMLParser"]).HTMLParser):
    SKIP = {"script", "style", "noscript", "nav", "footer", "header", "aside",
            "form", "select", "option"}
    BLOCK = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6",
             "table", "section", "article"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._chunks = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip_depth += 1
        elif tag in self.BLOCK and self._skip_depth == 0:
            self._chunks.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag in self.BLOCK and self._skip_depth == 0:
            self._chunks.append("\n")

    def handle_data(self, data):
        if self._skip_depth == 0:
            self._chunks.append(data)

    def text(self):
        return re.sub(r"[ \t\xa0]+", " ",
                      re.sub(r"\n\s*\n+", "\n", "".join(self._chunks))).strip()


def _stdlib_extract(html):
    p = _TextParser()
    p.feed(html)
    return p.text()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="./data")
    ap.add_argument("--limit-companies", type=int, default=0)
    ap.add_argument("--tickers", default="",
                    help="comma-separated tickers to run (targeted re-runs)")
    args = ap.parse_args()

    if args.tickers:
        tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
    elif args.limit_companies:
        tickers = list(CIKS)[:args.limit_companies]
    else:
        tickers = list(CIKS)
    os.makedirs(os.path.join(args.out, "texts"), exist_ok=True)
    index_path = os.path.join(args.out, "index.csv")
    done = set()
    if os.path.exists(index_path):
        with open(index_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done.add((row["ticker"], row["year"]))
    new_index = not os.path.exists(index_path)

    cols = ["ticker", "company_name", "year", "filing_date", "form",
            "accession", "doc_url", "text_path", "word_count", "analyst_notes"]
    f = open(index_path, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=cols)
    if new_index:
        w.writeheader()

    for ticker in tickers:
        print(f"[{ticker}] listing DEF 14A filings ...")
        try:
            by_year = pick_proxy_filings(ticker)
        except Exception as e:
            print(f"[{ticker}] listing failed: {e}")
            by_year = {}
        note_cov = f"def14a-coverage={len(by_year)}/9yrs"
        for year in YEARS:
            if (ticker, str(year)) in done:
                continue
            info = by_year.get(year)
            text, wc, url, note = "", 0, "", f"{note_cov}; no DEF 14A found"
            if info:
                url = doc_url(info["cik"], info["accession"], info["primary"])
                time.sleep(SLEEP)
                html = sec_download(url)
                if html:
                    text = extract_text(html)
                    # Sanity guard (added after the gzip bug): genuine
                    # proxy text is overwhelmingly letters/spaces. If the
                    # printable-letter ratio is low, the download is
                    # corrupt - record a failure, never garbage "text".
                    letters = sum(c.isalpha() or c.isspace() for c in text)
                    if text and letters / len(text) < 0.75:
                        text = ""
                    wc = len(text.split())
                amend = "; amended filing used" if info["form"] == "DEF 14A/A" else ""
                note = (f"{note_cov}; filed {info['filing_date']}{amend}"
                        if wc > 500 else f"{note_cov}; download/extraction failed")
                if wc <= 500:
                    text, wc = "", 0
            text_path = os.path.join(args.out, "texts", f"{ticker}_{year}.txt")
            with open(text_path, "w", encoding="utf-8") as tf:
                tf.write(text)
            w.writerow({"ticker": ticker, "company_name": NAMES[ticker],
                        "year": year,
                        "filing_date": info["filing_date"] if info else "",
                        "form": info["form"] if info else "",
                        "accession": info["accession"] if info else "",
                        "doc_url": url, "text_path": text_path,
                        "word_count": wc, "analyst_notes": note})
            f.flush()
        print(f"[{ticker}] done ({len(by_year)}/9 years)")
    f.close()
    print("index ->", index_path)


if __name__ == "__main__":
    main()
