#!/usr/bin/env python3
"""
Part 1 — Wayback "About Us" collection (Wharton People Analytics RA task).

Pipeline
--------
1. For each of the 50 task companies, identify the corporate "About Us"
   (or mission/values) entry point on the corporate domain.
2. Download ONE snapshot per year, 2016-2024 (~450 total), preferring the
   capture closest to July 1 each year.
3. Extract visible body text (nav/footer/boilerplate stripped).
4. Write a per-company-year dataset with the schema the task requires:
     ticker, company_name, sector, year, wayback_timestamp, page_url,
     page_text_clean, changed_from_prior, theme_categories, analyst_notes
   plus provenance (about_pattern entry point, domain_verified).

Page-identification criterion (document this in your Part 1 README):
  - Candidate entry points per corporate domain (exact URLs):
    /about, /about-us, /company, /our-company, /who-we-are, and the
    homepage ("" = domain root).
  - Score each entry point by how many distinct years 2016-2024 have ANY
    archived capture of that exact URL; pick the best (tie-break: more
    specific path beats homepage; then earliest first capture).
  - Corporate about URLs very often 301-redirect (to a trailing-slash or
    locale variant, e.g. /en-us/about). We therefore do NOT filter CDX to
    statuscode:200, and downloads use the standard Wayback URL (no id_
    suffix) so the archive resolves the redirect chain to the target
    page's own capture. The resolved final URL is recorded in page_url.
  - A year whose entry point has no capture, whose download fails, or
    whose extracted body text is <200 chars becomes a gap row with an
    analyst_note. The task explicitly says "We are not expecting 100%
    coverage" — document gaps, don't fabricate.

Domain overrides (verified via CDX 2026-10-15, see
part1_domain_verification_notes.md):
  - META: meta.com/about* has only 1 snapshot 2016-2024 (pre-rebrand the
    domain wasn't Facebook's). facebook.com is the historical about host;
    about.facebook.com also qualifies. 2021 rebrand documented in README.
  - GOOGL: abc.xyz has no /about* path; the single-page site IS the about.
    Homepage-as-equivalent per the task's "(or equivalent)" clause.
  - BRK.B: berkshirehathaway.com has no about page; homepage = about.

Run:
    pip install requests beautifulsoup4 trafilatura   # trafilatura optional
    python part1_wayback_scaffold.py --out ./data
    # smoke test first:
    python part1_wayback_scaffold.py --out ./data --limit-companies 2

LLM analysis stubs are at the bottom (detect_change / classify_themes /
style_shift). Plug in your API of choice; prompts are shaped for the three
required analyses: (a) changed vs prior year, (b) value-theme categories
(you define + justify), (c) linguistic drift over time.
"""

import argparse
import csv
import json
import os
import re
import time

import requests

CDX_URL = "https://web.archive.org/cdx/search/cdx"
# No id_ suffix: the archive must resolve redirect captures (301) to the
# target page's capture; id_ would return the bare redirect stub instead.
WAYBACK_FMT = "https://web.archive.org/web/{ts}/{url}"
YEARS = list(range(2016, 2025))
# Entry-point paths tried per domain; "" is the homepage fallback.
ENTRY_POINTS = ["about", "about-us", "company", "our-company", "who-we-are", ""]

# (ticker, company_name, sector, corporate_domain) — company list is given
# verbatim in the task PDF; domains are best-effort and MUST be verified.
COMPANIES = [
    # Technology
    ("MSFT", "Microsoft", "Technology", "microsoft.com"),
    ("AAPL", "Apple", "Technology", "apple.com"),
    ("NVDA", "NVIDIA", "Technology", "nvidia.com"),
    ("GOOGL", "Alphabet", "Technology", "abc.xyz"),
    ("META", "Meta Platforms", "Technology", "meta.com"),
    ("AVGO", "Broadcom", "Technology", "broadcom.com"),
    ("CRM", "Salesforce", "Technology", "salesforce.com"),
    ("ORCL", "Oracle", "Technology", "oracle.com"),
    ("IBM", "IBM", "Technology", "ibm.com"),
    ("INTC", "Intel", "Technology", "intel.com"),
    # Financials
    ("BRK.B", "Berkshire Hathaway", "Financials", "berkshirehathaway.com"),
    ("JPM", "JPMorgan Chase", "Financials", "jpmorganchase.com"),
    ("BAC", "Bank of America", "Financials", "bankofamerica.com"),
    ("WFC", "Wells Fargo", "Financials", "wellsfargo.com"),
    ("GS", "Goldman Sachs", "Financials", "goldmansachs.com"),
    ("MS", "Morgan Stanley", "Financials", "morganstanley.com"),
    ("BLK", "BlackRock", "Financials", "blackrock.com"),
    ("SCHW", "Charles Schwab", "Financials", "schwab.com"),
    ("AXP", "American Express", "Financials", "americanexpress.com"),
    ("C", "Citigroup", "Financials", "citigroup.com"),
    # Healthcare
    ("LLY", "Eli Lilly", "Healthcare", "lilly.com"),
    ("UNH", "UnitedHealth Group", "Healthcare", "unitedhealthgroup.com"),
    ("JNJ", "Johnson & Johnson", "Healthcare", "jnj.com"),
    ("ABBV", "AbbVie", "Healthcare", "abbvie.com"),
    ("MRK", "Merck", "Healthcare", "merck.com"),
    ("TMO", "Thermo Fisher Scientific", "Healthcare", "thermofisher.com"),
    ("ABT", "Abbott Laboratories", "Healthcare", "abbott.com"),
    ("PFE", "Pfizer", "Healthcare", "pfizer.com"),
    ("MDT", "Medtronic", "Healthcare", "medtronic.com"),
    ("BMY", "Bristol-Myers Squibb", "Healthcare", "bms.com"),
    # Consumer Discretionary
    ("AMZN", "Amazon", "Consumer Discretionary", "amazon.com"),
    ("TSLA", "Tesla", "Consumer Discretionary", "tesla.com"),
    ("HD", "Home Depot", "Consumer Discretionary", "homedepot.com"),
    ("MCD", "McDonald's", "Consumer Discretionary", "mcdonalds.com"),
    ("NKE", "Nike", "Consumer Discretionary", "nike.com"),
    ("SBUX", "Starbucks", "Consumer Discretionary", "starbucks.com"),
    ("TGT", "Target", "Consumer Discretionary", "target.com"),
    ("LOW", "Lowe's", "Consumer Discretionary", "lowes.com"),
    ("TJX", "TJX Companies", "Consumer Discretionary", "tjx.com"),
    ("F", "Ford Motor", "Consumer Discretionary", "ford.com"),
    # Energy
    ("XOM", "ExxonMobil", "Energy", "exxonmobil.com"),
    ("CVX", "Chevron", "Energy", "chevron.com"),
    ("COP", "ConocoPhillips", "Energy", "conocophillips.com"),
    ("EOG", "EOG Resources", "Energy", "eogresources.com"),
    ("SLB", "SLB (Schlumberger)", "Energy", "slb.com"),
    ("MPC", "Marathon Petroleum", "Energy", "marathonpetroleum.com"),
    ("PSX", "Phillips 66", "Energy", "phillips66.com"),
    ("VLO", "Valero Energy", "Energy", "valero.com"),
    ("OXY", "Occidental Petroleum", "Energy", "oxy.com"),
    ("HAL", "Halliburton", "Energy", "halliburton.com"),
]

# ticker -> EXTRA candidate (domain, entry_points) added to the default
# (domain + www.domain) x ENTRY_POINTS grid. All verified via CDX
# 2026-10-15/20; see part1_domain_verification_notes.md.
DOMAIN_OVERRIDES = {
    # meta.com was not Facebook's domain pre-2021; the historical about
    # host is facebook.com (9/9). 2021 rebrand documented in README.
    "META": [("facebook.com", ENTRY_POINTS),
             ("about.facebook.com", ENTRY_POINTS),
             ("meta.com", ENTRY_POINTS)],
    # abc.xyz (Alphabet's investor page) is a near-static founders' letter,
    # not a values About page; google.com/about is the operating company's
    # About with 9/9 coverage. Both stay candidates; the picker decides by
    # coverage, and about-type beats homepage.
    "GOOGL": [("google.com", ENTRY_POINTS),
              ("www.google.com", ENTRY_POINTS),
              ("about.google", ENTRY_POINTS),
              ("abc.xyz", [""])],
    # Berkshire's famously minimal site has no about page; homepage = about.
    "BRK.B": [("berkshirehathaway.com", [""])],
    # Intel's overview lives at a deep /content/ path (9/9 verified);
    # intel.com homepage captures are JS shells with no extractable text.
    "INTC": [("www.intel.com",
              ["content/www/us/en/company-overview/company-overview.html"])],
    # Microsoft's about is locale-pathed; /en-us/about is 9/9 verified.
    "MSFT": [("www.microsoft.com", ["en-us/about"])],
    # ExxonMobil's about presence is the corporate site's homepage (9/9);
    # www.exxonmobil.com/about-us has no usable captures 2016-2024.
    "XOM": [("corporate.exxonmobil.com", [""])],
}

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "wharton-ra-task-research/0.1 (academic research)"})


def cdx_get(params, tries=4):
    """GET the CDX API with backoff on 429/503 AND on connection errors
    (the sandbox proxy occasionally drops a connection mid-run; one
    dropped query must not kill a 50-company overnight run)."""
    for i in range(tries):
        try:
            r = SESSION.get(CDX_URL, params=params, timeout=60)
        except requests.RequestException:
            time.sleep(2 ** (i + 1) * 3)
            continue
        if r.status_code == 200:
            return r.json() if r.text.strip() else []
        if r.status_code in (429, 503):
            time.sleep(2 ** (i + 1) * 5)
            continue
        r.raise_for_status()
    raise RuntimeError(f"CDX failed after {tries} tries: {params}")


def captures_for_entry(domain, entry):
    """All 2016-2024 captures of the exact entry URL (any status — about
    pages frequently redirect, and the redirect is resolved at download
    time). Returns [{timestamp, original, statuscode}]."""
    url = domain if entry == "" else f"{domain}/{entry}"
    rows = cdx_get([
        ("url", url), ("matchType", "exact"),
        ("from", "20160101"), ("to", "20241231"),
        ("output", "json"),
        ("filter", "mimetype:text/html"),
        ("fl", "timestamp,original,statuscode"),
    ])
    if not rows:
        return []
    header, data = rows[0], rows[1:]
    return [dict(zip(header, r)) for r in data]


def pick_about_entry(domains_entries):
    """Score every (domain, entry) by distinct years 2016-2024 with any
    capture. Selection rule (documented criterion): a real about path is
    preferred — take the best-coverage non-homepage entry when it covers
    >=5 of 9 years; otherwise fall back to the homepage (the task's
    "or equivalent" clause). Tie-break: earliest first capture.
    Per year, prefer a 200 capture closest to July 1.
    Returns (domain, entry, {year: capture})."""
    scored = []  # (domain, entry, coverage, first_ts)
    for domain, entries in domains_entries:
        for entry in entries:
            time.sleep(1)  # be nice to the CDX API
            caps = captures_for_entry(domain, entry)
            by_year = {}
            for c in caps:
                y = int(c["timestamp"][:4])
                if y not in YEARS:
                    continue
                # Error captures (403 bot-walls, 404s) are not data: a year
                # with ONLY error captures is a gap year, honestly reported.
                if c["statuscode"][:1] in ("4", "5"):
                    continue
                # prefer 200 captures; among same status, closest to Jul 1
                key = (0 if c["statuscode"] == "200" else 1,
                       abs(int(c["timestamp"][4:8]) - 701))
                if y not in by_year or key < by_year[y][0]:
                    by_year[y] = (key, c)
            cov = {y: v[1] for y, v in by_year.items()}
            if cov:
                scored.append((domain, entry, cov,
                               min(c["timestamp"] for c in cov.values())))
    if not scored:
        return None, None, {}
    about = [s for s in scored if s[1]]
    home = [s for s in scored if not s[1]]
    best_about = max(about, key=lambda s: (len(s[2]), -int(s[3])),
                     default=None)
    if best_about and len(best_about[2]) >= 5:
        chosen = best_about
    else:
        chosen = max(scored, key=lambda s: (len(s[2]), bool(s[1]), -int(s[3])))
    return chosen[0], chosen[1], chosen[2]


JUNK_PATH_MARKERS = ("sitemap", "404", "not-found", "notfound", "/error")


def usable(final_url, text):
    """A resolved page counts as usable only if it has real body text and
    did not land on a utility page (sitemap/404/error). Redirect-to-junk
    is recorded as a gap, never as data."""
    if len(text) < 200:
        return False
    path = (final_url or "").lower()
    return not any(m in path for m in JUNK_PATH_MARKERS)


def download_page(timestamp, original, tries=3):
    """Download via the standard Wayback URL so archived redirects resolve.
    Returns (html, final_url) or (None, None)."""
    for i in range(tries):
        try:
            r = SESSION.get(WAYBACK_FMT.format(ts=timestamp, url=original),
                            timeout=60)
            if r.status_code == 200 and len(r.text) > 500:
                return r.text, r.url
            return None, None  # block page / dead end -> treat as missing
        except requests.RequestException:
            time.sleep(2 ** (i + 1))
    return None, None


def extract_text(html):
    """Visible body text, boilerplate stripped. trafilatura preferred."""
    try:
        import trafilatura
        t = trafilatura.extract(html, include_comments=False, include_tables=False)
        if t and len(t) > 200:
            return re.sub(r"\s+", " ", t).strip()
    except ImportError:
        pass
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return re.sub(r"\s+", " ", text).strip()


def load_done(index_path):
    done = set()
    if os.path.exists(index_path):
        with open(index_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done.add((row["ticker"], row["year"]))
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="./data")
    ap.add_argument("--limit-companies", type=int, default=0,
                    help="smoke-test on first N companies")
    ap.add_argument("--tickers", default="",
                    help="comma-separated tickers to run (targeted re-runs)")
    args = ap.parse_args()

    if args.tickers:
        wanted = {t.strip() for t in args.tickers.split(",") if t.strip()}
        companies = [c for c in COMPANIES if c[0] in wanted]
    elif args.limit_companies:
        companies = COMPANIES[:args.limit_companies]
    else:
        companies = COMPANIES
    os.makedirs(os.path.join(args.out, "texts"), exist_ok=True)
    index_path = os.path.join(args.out, "index.csv")
    done = load_done(index_path)
    new_index = not os.path.exists(index_path)

    cols = ["ticker", "company_name", "sector", "year", "wayback_timestamp",
            "page_url", "about_pattern", "domain_verified", "page_text_clean",
            "changed_from_prior", "theme_categories", "analyst_notes"]
    f = open(index_path, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=cols)
    if new_index:
        w.writeheader()

    prev_text = {}
    for ticker, name, sector, domain in companies:
        override = DOMAIN_OVERRIDES.get(ticker)
        # Default grid: bare domain + www host (captures often live only
        # under www), times the standard entry points; plus any verified
        # per-company extras from DOMAIN_OVERRIDES.
        domains_entries = [(domain, ENTRY_POINTS),
                           (f"www.{domain}", ENTRY_POINTS)]
        if override:
            domains_entries += override
        print(f"[{ticker}] discovering about entry point ...")
        try:
            used_domain, entry, coverage = pick_about_entry(domains_entries)
        except Exception as e:
            # One company's discovery failure must not kill the whole run:
            # record 9 honest gap rows and move on.
            print(f"[{ticker}] discovery FAILED ({e}); writing gap rows")
            used_domain, entry, coverage = domain, "", {}
        verified = "True" if override else "False"
        entry_label = entry if entry else "(homepage)"
        note_base = (f"domain={used_domain}; entry={entry_label}; "
                     f"coverage={len(coverage)}/9yrs")
        for year in YEARS:
            if (ticker, str(year)) in done:
                continue
            cap = coverage.get(year)
            text, ts, url, note = "", "", "", f"{note_base}; no capture of entry URL"
            if cap:
                ts = cap["timestamp"]
                time.sleep(0.5)
                html, final_url = download_page(ts, cap["original"])
                if html:
                    text = extract_text(html)
                    url = final_url or cap["original"]
                if not usable(url, text):
                    why = ("resolved to utility page" if text and url and
                           any(m in url.lower() for m in JUNK_PATH_MARKERS)
                           else "capture unusable (<200 chars body)")
                    text, url = "", cap["original"]
                    note = f"{note_base}; {why}"
                else:
                    note = note_base
            text_path = os.path.join(args.out, "texts", f"{ticker}_{year}.txt")
            with open(text_path, "w", encoding="utf-8") as tf:
                tf.write(text)
            changed = ""
            if text and prev_text.get(ticker):
                changed = "tbd-llm"  # filled by detect_change() below
            prev_text[ticker] = text or prev_text.get(ticker, "")
            w.writerow({
                "ticker": ticker, "company_name": name, "sector": sector,
                "year": year, "wayback_timestamp": ts, "page_url": url,
                "about_pattern": f"{used_domain}/{entry_label}",
                "domain_verified": verified,
                "page_text_clean": text_path, "changed_from_prior": changed,
                "theme_categories": "", "analyst_notes": note,
            })
            f.flush()
        print(f"[{ticker}] done ({len(coverage)}/9 years, entry={entry_label})")
    f.close()
    print("index ->", index_path)


# ---------------------------------------------------------------------------
# LLM pipeline stubs — plug in your API of choice (OpenAI/Anthropic/etc.).
# Run these over index.csv AFTER collection; write results back into
# changed_from_prior / theme_categories / analyst_notes.
# ---------------------------------------------------------------------------

PROMPT_CHANGE = """Compare two yearly snapshots of the same company's About page.
A (prior year):\n{text_a}\n\nB (current year):\n{text_b}\n\n
1. Did the page substantively change (beyond dates/numbers)? yes/no
2. In one sentence, what changed?
Return JSON: {{"changed": true/false, "summary": "..."}}"""

PROMPT_THEMES = """Classify the values/themes expressed in this corporate About page.
Use ONLY these categories (define + justify them in your README):
[innovation, customer-focus, integrity, sustainability, diversity-inclusion,
 employee-wellbeing, shareholder-value, community, excellence]
Text:\n{text}\n\nReturn JSON: {{"themes": ["...", ...], "notes": "..."}}"""

PROMPT_DRIFT = """These are yearly About-page texts from one company, oldest to newest.
Describe notable linguistic/stylistic shifts over time (tone, buzzwords,
framing). Keep to 3 bullets.
{texts}"""


def detect_change(text_a, text_b, llm_call):
    """llm_call(prompt) -> str. Returns (changed: bool, summary: str)."""
    out = json.loads(llm_call(PROMPT_CHANGE.format(text_a=text_a[:4000],
                                                  text_b=text_b[:4000])))
    return out["changed"], out["summary"]


def classify_themes(text, llm_call):
    out = json.loads(llm_call(PROMPT_THEMES.format(text=text[:6000])))
    return out["themes"], out["notes"]


def style_shift(year_texts, llm_call):
    blob = "\n\n---\n\n".join(f"[{y}]\n{t[:2000]}" for y, t in year_texts)
    return llm_call(PROMPT_DRIFT.format(texts=blob))


if __name__ == "__main__":
    main()
