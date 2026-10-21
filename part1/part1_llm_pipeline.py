#!/usr/bin/env python3
"""
part1_llm_pipeline.py - LLM analysis stage for Part 1 (values language).

Runs AFTER part1_wayback_scaffold.py has collected the About-page texts.
Uses Google Gemini via the custom.google-gemini connector (the API key
lives in Muse's Secure Vault; this script only ever holds a surrogate -
see ~/workspace/custom-connectors/custom.google-gemini/bin/gemini_call.py).

Three stages, each checkpointed (safe to stop / re-run; finished units
are skipped):
  A. themes   - per company-year: classify the 9-theme taxonomy.
                Output: data/llm_themes.csv
  B. changes  - per consecutive available year pair: substantive change?
                Output: data/llm_changes.csv
  C. drift    - per company: linguistic drift across the whole series.
                Output: data/llm_drift/<TICKER>.md

Analysis-eligible = cleaned text with >= MIN_WORDS words (default 100):
below that a snapshot is mostly navigation residue, and theme labels on
it would be noise. The threshold is reported in the Part 1 README.

Usage:
    python3 part1_llm_pipeline.py --stage themes  [--limit N] [--model M]
    python3 part1_llm_pipeline.py --stage changes [--limit N] [--model M]
    python3 part1_llm_pipeline.py --stage drift   [--limit N] [--model M]
"""
import argparse
import csv
import http.client
import json
import os
import sys
import time
import urllib.error

sys.path.insert(0, os.path.expanduser(
    "~/workspace/custom-connectors/custom.google-gemini/bin"))
from gemini_call import call as gemini_call  # noqa: E402

MIN_WORDS = 100


class FatalQuota(Exception):
    """Daily free-tier quota exhausted - abort the whole run cleanly.
    Checkpointing means a re-run tomorrow resumes where this stopped."""
THEMES = ["innovation", "customer-focus", "integrity", "sustainability",
          "diversity-inclusion", "employee-wellbeing", "shareholder-value",
          "community", "excellence"]

PROMPT_THEMES = """Classify the values/themes expressed in this corporate About page.
Use ONLY these categories: {themes}
Text:
{text}

Return JSON: {{"themes": ["...", ...], "notes": "one sentence on what the page most emphasizes"}}"""

PROMPT_CHANGE = """Compare two yearly snapshots of the same company's About page.
A (prior year):
{text_a}

B (current year):
{text_b}

1. Did the page substantively change (beyond dates/numbers)? yes/no
2. In one sentence, what changed?
Return JSON: {{"changed": true/false, "summary": "..."}}"""

PROMPT_DRIFT = """These are yearly About-page texts from one company ({company}), oldest to newest.
Describe notable linguistic/stylistic shifts over time (tone, buzzwords, framing).
Keep to 3 bullets.
{texts}"""


def llm(prompt, model, json_mode=True, tries=5):
    """One generateContent call with backoff on 429/5xx and on the
    sandbox proxy's dropped connections (URLError / timeouts)."""
    gen_cfg = {"temperature": 0.2}
    if json_mode:
        gen_cfg["responseMimeType"] = "application/json"
    for i in range(tries):
        try:
            out = gemini_call(f"/models/{model}:generateContent", {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": gen_cfg,
            })
            cands = out.get("candidates", [])
            if not cands:
                raise RuntimeError(f"no candidates: {json.dumps(out)[:200]}")
            parts = cands[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts)
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                # Per-minute limits recover in ~a minute. A DAILY quota
                # 429 also lands here, but after 2 long waits we give up
                # via FatalQuota instead of burning the whole run.
                time.sleep(60)
                continue
            if e.code == 429:
                raise FatalQuota("429 after retries - daily quota likely "
                                 "exhausted; re-run after the reset")
            if e.code in (500, 503) and i < tries - 1:
                time.sleep(2 ** (i + 1) * 5)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, RuntimeError,
                ConnectionError, http.client.HTTPException) as e:
            # ConnectionError covers http.client.RemoteDisconnected -
            # the proxy drops connections without a response and urllib
            # does NOT wrap that one in URLError.
            if i < tries - 1:
                time.sleep(2 ** (i + 1) * 3)
                continue
            raise RuntimeError(f"LLM call failed after {tries} tries: {e}")


def load_texts(index_csv):
    """Yield (ticker, year, text) for analysis-eligible rows."""
    with open(index_csv) as f:
        for row in csv.DictReader(f):
            path = row["page_text_clean"]
            if not os.path.exists(path):
                continue
            text = open(path).read().strip()
            if len(text.split()) >= MIN_WORDS:
                yield row["ticker"], int(row["year"]), text


def done_keys(path, key_cols):
    if not os.path.exists(path):
        return set()
    with open(path) as f:
        return {tuple(r[c] for c in key_cols) for r in csv.DictReader(f)}


def stage_themes(texts, out_csv, model, limit):
    done = done_keys(out_csv, ["ticker", "year"])
    todo = [(t, y, x) for t, y, x in texts if (t, str(y)) not in done]
    if limit:
        todo = todo[:limit]
    print(f"themes: {len(todo)} to do ({len(done)} already done)")
    new = not os.path.exists(out_csv)
    with open(out_csv, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["ticker", "year", "themes", "notes", "model"])
        for ticker, year, text in todo:
            try:
                raw = llm(PROMPT_THEMES.format(themes=", ".join(THEMES),
                                               text=text[:6000]), model)
                out = json.loads(raw)
                if isinstance(out, list):
                    out = {"themes": out, "notes": ""}
                if not isinstance(out, dict) or "themes" not in out:
                    raise ValueError(f"unexpected JSON shape: {raw[:80]}")
                bad = [t for t in out["themes"] if t not in THEMES]
                if bad:
                    print(f"  ! {ticker} {year}: off-taxonomy {bad} dropped")
                    out["themes"] = [t for t in out["themes"] if t in THEMES]
                w.writerow([ticker, year, ";".join(out["themes"]),
                            out.get("notes", ""), model])
            except FatalQuota:
                raise
            except Exception as e:
                # Leave the row unwritten: the checkpoint logic retries
                # it on the next run instead of killing this one.
                print(f"  ! {ticker} {year}: FAILED ({str(e)[:80]}), "
                      "will retry next run")
                continue
            f.flush()
            print(f"  {ticker} {year}: {out['themes']}")
            time.sleep(2)


def bow_cosine(text_a, text_b):
    """Bag-of-words cosine similarity (tokens len>=3, tiny stoplist).
    Quantitative companion to the LLM change judgment: copyright-year /
    cookie-banner churn moves this barely, a real rewrite moves it a lot.
    README rule of thumb: > 0.95 ~ no substantive change."""
    import math
    import re as _re
    stop = {"the", "and", "for", "our", "you", "your", "are", "with",
            "this", "that", "from", "all", "can", "will", "have", "has"}
    def vec(t):
        v = {}
        for w in _re.findall(r"[a-z]{3,}", t.lower()):
            if w not in stop:
                v[w] = v.get(w, 0) + 1
        return v
    va, vb = vec(text_a), vec(text_b)
    dot = sum(c * vb.get(w, 0) for w, c in va.items())
    na = math.sqrt(sum(c * c for c in va.values()))
    nb = math.sqrt(sum(c * c for c in vb.values()))
    return round(dot / (na * nb), 4) if na and nb else 0.0


def stage_changes(texts, out_csv, model, limit):
    # Pairs whose "change" is partly a measurement artefact: Meta's
    # company-info page migrated hosts (see Part 1 README). Flagged in
    # the data itself so change-rate computations can exclude them with
    # one filter instead of relying on prose warnings.
    ARTIFACT_PAIRS = {("META", 2017, 2018),   # homepage -> company-info
                      ("META", 2019, 2020),   # newsroom.fb.com -> about.fb.com
                      ("META", 2021, 2022)}   # about.fb.com -> about.meta.com
    by_company = {}
    for t, y, x in texts:
        by_company.setdefault(t, []).append((y, x))
    done = done_keys(out_csv, ["ticker", "from_year", "to_year"])
    pairs = []
    for ticker, series in sorted(by_company.items()):
        series.sort()
        for (y1, x1), (y2, x2) in zip(series, series[1:]):
            if (ticker, str(y1), str(y2)) not in done:
                pairs.append((ticker, y1, x1, y2, x2))
    if limit:
        pairs = pairs[:limit]
    print(f"changes: {len(pairs)} pairs to do ({len(done)} already done)")
    new = not os.path.exists(out_csv)
    with open(out_csv, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["ticker", "from_year", "to_year", "gap_years",
                        "changed", "text_similarity", "artifact_flag",
                        "summary", "model"])
        for ticker, y1, x1, y2, x2 in pairs:
            try:
                raw = llm(PROMPT_CHANGE.format(text_a=x1[:4000],
                                               text_b=x2[:4000]), model)
                out = json.loads(raw)
                if not isinstance(out, dict) or "changed" not in out:
                    raise ValueError(f"unexpected JSON shape: {raw[:80]}")
                w.writerow([ticker, y1, y2, y2 - y1, out["changed"],
                            bow_cosine(x1, x2),
                            (ticker, y1, y2) in ARTIFACT_PAIRS,
                            out.get("summary", ""), model])
            except FatalQuota:
                raise
            except Exception as e:
                print(f"  ! {ticker} {y1}->{y2}: FAILED ({str(e)[:80]}), "
                      "will retry next run")
                continue
            f.flush()
            print(f"  {ticker} {y1}->{y2}: changed={out['changed']}")
            time.sleep(2)


def stage_drift(texts, out_dir, model, limit):
    os.makedirs(out_dir, exist_ok=True)
    by_company = {}
    for t, y, x in texts:
        by_company.setdefault(t, []).append((y, x))
    tickers = [t for t in sorted(by_company)
               if not os.path.exists(os.path.join(out_dir, f"{t}.md"))]
    if limit:
        tickers = tickers[:limit]
    print(f"drift: {len(tickers)} companies to do")
    for ticker in tickers:
        series = sorted(by_company[ticker])
        blob = "\n\n---\n\n".join(f"[{y}]\n{x[:2000]}" for y, x in series)
        try:
            md = llm(PROMPT_DRIFT.format(company=ticker, texts=blob),
                     model, json_mode=False)
        except FatalQuota:
            raise
        except Exception as e:
            print(f"  ! {ticker}: FAILED ({str(e)[:80]}), "
                  "will retry next run")
            continue
        with open(os.path.join(out_dir, f"{ticker}.md"), "w") as f:
            f.write(f"# {ticker} - linguistic drift (model: {model})\n\n{md}\n")
        print(f"  {ticker}: done ({len(series)} years)")
        time.sleep(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["themes", "changes", "drift"],
                    required=True)
    ap.add_argument("--data", default="./data")
    ap.add_argument("--model", default="gemini-3.5-flash-lite")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    texts = list(load_texts(os.path.join(args.data, "index.csv")))
    print(f"analysis-eligible texts (>={MIN_WORDS} words): {len(texts)}")

    try:
        run_stage(args, texts)
    except FatalQuota as e:
        print(f"STOPPED: {e}")
        sys.exit(2)


def run_stage(args, texts):
    if args.stage == "themes":
        stage_themes(texts, os.path.join(args.data, "llm_themes.csv"),
                     args.model, args.limit)
    elif args.stage == "changes":
        stage_changes(texts, os.path.join(args.data, "llm_changes.csv"),
                      args.model, args.limit)
    else:
        stage_drift(texts, os.path.join(args.data, "llm_drift"),
                    args.model, args.limit)


if __name__ == "__main__":
    main()
