#!/usr/bin/env python3
"""
part3_index.py - Organizational Authenticity Index (Part 3).

Design as revised 2026-10-20 (see part3_index_methodology.md):
- SAME ruler both sides: theme-DICTIONARY share vectors for About
  ("said") and proxy ("did"); the Part 1 LLM labels are the validation
  cross-check, not an input.
- Each theme is z-scored WITHIN its document type, over the main
  sample, before comparing: raw shares mostly encode document type
  (proxies are structurally heavy on shareholder-value/integrity,
  About pages on customer-focus/innovation), which would compress
  every firm's score into the same narrow band. The z-cosine therefore
  lives in [-1, 1] and measures RELATIVE emphasis alignment: does this
  firm stress theme X in its proxy more than other firms do, matching
  how much more it stresses X on its About page than other firms do?
- MAIN metric is the LAGGED alignment, cosine(said_t, did_{t+1}):
  most sample firms have December fiscal year-ends, so the proxy filed
  in spring t+1 is the disclosure document for fiscal year t, the year
  the About snapshot describes. Same-year alignment is reported as a
  robustness variant (exact for autumn filers like Microsoft).
- Raw-share cosine is kept as authenticity_cosine_raw (robustness):
  the rank gap between the two versions is itself the demonstration
  that standardisation was necessary.
- Main sample is ROW-level page_type == 'about'.

Outputs data/authenticity_index.csv.
Requires: ../part1/data/{index.csv, theme_dictionary_scores.csv},
          ../part2/data/theme_dictionary_scores.csv
"""
import csv
import json
import math
import os
from collections import defaultdict

THEMES = ["innovation", "customer-focus", "integrity", "sustainability",
          "diversity-inclusion", "employee-wellbeing", "shareholder-value",
          "community", "excellence"]


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return round(dot / (na * nb), 4) if na and nb else None


def fit_stats(vecs, keys):
    cols = list(zip(*[vecs[k] for k in keys]))
    stats = []
    for c in cols:
        m = sum(c) / len(c)
        sd = math.sqrt(sum((x - m) ** 2 for x in c) / len(c)) or 1.0
        stats.append((m, sd))
    return stats


def apply_z(vec, stats):
    return [(x - m) / sd for x, (m, sd) in zip(vec, stats)]


def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for rank, i in enumerate(order):
            r[i] = rank
        return r
    rx, ry = ranks(xs), ranks(ys)
    return cosine([x - sum(rx) / len(rx) for x in rx],
                  [y - sum(ry) / len(ry) for y in ry])


def load_scores(path):
    shares, hits = {}, {}
    with open(path) as f:
        for r in csv.DictReader(f):
            k = (r["ticker"], int(r["year"]))
            shares[k] = [float(r[f"share_{t}"]) for t in THEMES]
            hits[k] = [int(r[f"hits_{t}"]) for t in THEMES]
    return shares, hits


def main():
    with open("../part1/data/index.csv") as f:
        p1 = {(r["ticker"], int(r["year"])): r
              for r in csv.DictReader(f)}
    said, said_hits = load_scores("../part1/data/theme_dictionary_scores.csv")
    did, did_hits = load_scores("../part2/data/theme_dictionary_scores.csv")

    # Sparse About rows (<5 total dictionary hits) make share vectors
    # unstable - one word can swing a theme from 0 to 50%. They are
    # 18% of the main sample, above the 10% line, so the HEADLINE
    # metric excludes them (z-stats fitted without them); the
    # with-sparse lagged cosine is kept as a robustness column.
    sparse = {k for k, h in said_hits.items() if sum(h) < 5}
    main_all = [k for k in said if k in did
                and p1.get(k, {}).get("page_type") == "about"]
    sample = [k for k in main_all if k not in sparse]
    print(f"main sample: {len(main_all)} company-years, "
          f"{len(main_all) - len(sample)} sparse excluded from headline, "
          f"z-fit n={len(sample)}")
    said_stats = fit_stats(said, sample)
    did_stats = fit_stats(did, sample)
    said_z = {k: apply_z(v, said_stats) for k, v in said.items()}
    did_z = {k: apply_z(v, did_stats) for k, v in did.items()}
    said_stats_all = fit_stats(said, main_all)
    did_stats_all = fit_stats(did, main_all)
    said_z_all = {k: apply_z(v, said_stats_all) for k, v in said.items()}
    did_z_all = {k: apply_z(v, did_stats_all) for k, v in did.items()}
    # Within-year z robustness: standardise each theme within each
    # calendar year separately. The pooled z leaves the common shock
    # in (in 2021 every firm talked DEI on both channels, pushing both
    # vectors the same way); within-year z removes that year-level
    # component, so any surviving year pattern is cross-sectional.
    from collections import defaultdict as _dd
    def within_year_z(vecs):
        by_year = _dd(list)
        for k in main_all:
            if k in vecs:
                by_year[k[1]].append(k)
        stats = {y: fit_stats(vecs, ks) for y, ks in by_year.items()}
        return {k: apply_z(v, stats[k[1]]) for k, v in vecs.items()
                if k[1] in stats}
    said_z_wy = within_year_z(said)
    did_z_wy = within_year_z(did)

    rows = []
    for (ticker, year) in sorted(set(p1) | set(said) | set(did)):
        meta = p1.get((ticker, year), {})
        k = (ticker, year)
        s, d = said.get(k), did.get(k)
        d_next = did.get((ticker, year + 1))
        row = {"ticker": ticker,
               "company_name": meta.get("company_name", ""),
               "sector": meta.get("sector", ""), "year": year,
               "page_type": meta.get("page_type", ""),
               "main_sample": meta.get("page_type") == "about",
               "said_vector": json.dumps(s) if s else "",
               "did_vector": json.dumps(d) if d else "",
               "n_themes_said": (sum(1 for h in said_hits[k] if h >= 1)
                                 if s else ""),
               "n_themes_did": (sum(1 for h in did_hits[k] if h >= 5)
                                if d else ""),
               "about_coverage_flag": ("" if s else "no usable About text"),
               "proxy_coverage_flag": ("" if d else "no usable proxy text")}
        if s and sum(said_hits[k]) < 5:
            row["about_coverage_flag"] = "sparse dictionary coverage (<5 hits)"
        if s and d_next:
            row["authenticity_cosine"] = cosine(
                said_z[k], did_z[(ticker, year + 1)])
            row["authenticity_cosine_withsparse"] = cosine(
                said_z_all[k], did_z_all[(ticker, year + 1)])
            kz = (ticker, year + 1)
            if k in said_z_wy and kz in did_z_wy:
                row["authenticity_cosine_withinyear"] = cosine(
                    said_z_wy[k], did_z_wy[kz])
        if s and d:
            row["authenticity_cosine_contemp"] = cosine(said_z[k], did_z[k])
            row["authenticity_cosine_raw"] = cosine(s, d)
            row["authenticity_l1_raw"] = round(
                1 - sum(abs(x - y) for x, y in zip(s, d)) / 2, 4)
            sb = [1 if h >= 1 else 0 for h in said_hits[k]]
            db = [1 if h >= 5 else 0 for h in did_hits[k]]
            inter = sum(1 for x, y in zip(sb, db) if x and y)
            union = sum(1 for x, y in zip(sb, db) if x or y)
            row["authenticity_jaccard"] = (round(inter / union, 4)
                                           if union else "")
        rows.append(row)

    os.makedirs("data", exist_ok=True)
    fields = ["ticker", "company_name", "sector", "year", "page_type",
              "main_sample", "authenticity_cosine",
              "authenticity_cosine_withsparse",
              "authenticity_cosine_withinyear",
              "authenticity_cosine_contemp", "authenticity_cosine_raw",
              "authenticity_l1_raw", "authenticity_jaccard",
              "n_themes_said", "n_themes_did", "said_vector", "did_vector",
              "about_coverage_flag", "proxy_coverage_flag"]
    with open("data/authenticity_index.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    main_rows = [r for r in rows if r["main_sample"]
                 and (r["ticker"], r["year"]) not in sparse
                 and r.get("authenticity_cosine") is not None]
    if not main_rows:
        print("no main-sample rows with a lagged score yet - "
              "is the Part 2 dictionary output present?")
        return
    vals = sorted(r["authenticity_cosine"] for r in main_rows)
    n = len(vals)
    mean = sum(vals) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / n)
    print(f"MAIN (lagged z-cosine), main sample: n={n} mean {mean:.3f} "
          f"sd {sd:.3f} median {vals[n // 2]:.3f} "
          f"min {vals[0]:.3f} max {vals[-1]:.3f}")
    both = [(r["authenticity_cosine"], r["authenticity_cosine_raw"])
            for r in main_rows
            if r.get("authenticity_cosine_raw") is not None]
    if len(both) > 3:
        print(f"Spearman(main, raw-share cosine) = "
              f"{spearman([a for a, _ in both], [b for _, b in both]):.3f} "
              f"(n={len(both)}) - the standardisation check")
    by_year = defaultdict(list)
    for r in main_rows:
        by_year[r["year"]].append(r["authenticity_cosine"])
    print("by year:", {y: round(sum(v) / len(v), 3)
                       for y, v in sorted(by_year.items())})
    wy = defaultdict(list)
    for r in main_rows:
        if r.get("authenticity_cosine_withinyear") is not None:
            wy[r["year"]].append(r["authenticity_cosine_withinyear"])
    if wy:
        print("by year (within-year z robustness):",
              {y: round(sum(v) / len(v), 3) for y, v in sorted(wy.items())})
    by_firm = defaultdict(list)
    for r in main_rows:
        by_firm[r["ticker"]].append(r["authenticity_cosine"])
    fm = sorted(((sum(v) / len(v), t) for t, v in by_firm.items()))
    print("top 5 firms:", [(t, round(m, 3)) for m, t in fm[-5:]])
    print("bottom 5 firms:", [(t, round(m, 3)) for m, t in fm[:5]])


if __name__ == "__main__":
    main()
