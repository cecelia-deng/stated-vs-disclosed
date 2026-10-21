#!/usr/bin/env python3
"""key_numbers.py - recompute EVERY number quoted in the four parts'
READMEs/summaries from the final data, and write key_numbers.json.
Drafts copy numbers from that file only (Qing's rule, 2026-10-20)."""
import csv
import json
import statistics
from collections import defaultdict

THEMES = ["innovation", "customer-focus", "integrity", "sustainability",
          "diversity-inclusion", "employee-wellbeing", "shareholder-value",
          "community", "excellence"]
K = {}

# ---------- Part 2 ----------
p2 = list(csv.DictReader(open("part2/data/index.csv")))
ok = [r for r in p2 if int(r["word_count"]) > 500]
K["p2_coverage"] = f"{len(ok)}/450"
K["p2_median_words"] = int(statistics.median(int(r["word_count"]) for r in ok))
K["p2_gaps"] = [[r["ticker"], int(r["year"])] for r in p2
                if int(r["word_count"]) <= 500]
sec = {}
with open("part1/data/index.csv") as f:
    for r in csv.DictReader(f):
        sec[r["ticker"]] = r["sector"]
scores = list(csv.DictReader(open("part2/data/theme_dictionary_scores.csv")))
K["p2_theme_means"] = {t: round(sum(float(r[f"share_{t}"]) for r in scores)
                                / len(scores), 3) for t in THEMES}
by_year = defaultdict(list)
for r in scores:
    by_year[int(r["year"])].append(r)
for th in ("diversity-inclusion", "sustainability"):
    K[f"p2_{th}_by_year"] = {
        y: round(sum(float(r[f"share_{th}"]) for r in v) / len(v), 3)
        for y, v in sorted(by_year.items())}
by_sec = defaultdict(list)
for r in scores:
    by_sec[sec[r["ticker"]]].append(r)
K["p2_sector_table"] = {s: {t: round(sum(float(r[f"share_{t}"]) for r in v)
                                      / len(v), 3)
                             for t in ("sustainability", "shareholder-value",
                                       "diversity-inclusion",
                                       "employee-wellbeing")}
                        for s, v in sorted(by_sec.items())}

# ---------- Part 3 ----------
idx = list(csv.DictReader(open("part3/data/authenticity_index.csv")))
head = [r for r in idx if r["main_sample"] == "True"
        and r["authenticity_cosine"] != ""
        and "sparse" not in r["about_coverage_flag"]]
vals = sorted(float(r["authenticity_cosine"]) for r in head)
n = len(vals)
mean = sum(vals) / n
K["p3_headline"] = {"n": n, "mean": round(mean, 3),
                    "sd": round(statistics.pstdev(vals), 3),
                    "median": round(vals[n // 2], 3),
                    "min": round(vals[0], 3), "max": round(vals[-1], 3)}
by = defaultdict(list)
for r in head:
    by[int(r["year"])].append(float(r["authenticity_cosine"]))
K["p3_by_year"] = {y: round(sum(v) / len(v), 3) for y, v in sorted(by.items())}
K["p3_by_year_n"] = {y: len(v) for y, v in sorted(by.items())}
byw = defaultdict(list)
for r in head:
    if r["authenticity_cosine_withinyear"] != "":
        byw[int(r["year"])].append(float(r["authenticity_cosine_withinyear"]))
K["p3_by_year_withinyear"] = {y: round(sum(v) / len(v), 3)
                              for y, v in sorted(byw.items())}
def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for rank, i in enumerate(order):
            r[i] = rank
        return r
    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return round(num / den, 3) if den else None
both = [(float(r["authenticity_cosine"]), float(r["authenticity_cosine_raw"]))
        for r in head if r["authenticity_cosine_raw"] != ""]
K["p3_spearman_main_vs_raw"] = spearman([a for a, _ in both],
                                        [b for _, b in both])
firm = defaultdict(list)
for r in head:
    firm[r["ticker"]].append(float(r["authenticity_cosine"]))
fm = sorted(((round(sum(v) / len(v), 3), t) for t, v in firm.items()))
K["p3_firms_top5"] = [[t, m] for m, t in fm[-5:][::-1]]
K["p3_firms_bottom5"] = [[t, m] for m, t in fm[:5]]
K["p3_n_firms"] = len(fm)
wfc = {int(r["year"]): float(r["authenticity_cosine"]) for r in idx
       if r["ticker"] == "WFC" and r["authenticity_cosine"] != ""}
K["p3_wfc"] = {"values_2016_19": {y: round(wfc[y], 3) for y in (2016, 2017, 2018, 2019) if y in wfc},
               "mean_2016_19": round(sum(wfc[y] for y in (2016, 2017, 2018, 2019) if y in wfc) / 4, 3),
               "rank_low_to_high": [t for _, t in fm].index("WFC") + 1,
               "of_firms": len(fm)}
by_sec3 = defaultdict(list)
for r in head:
    by_sec3[r["sector"]].append(float(r["authenticity_cosine"]))
K["p3_sector_means"] = {s: [len(v), round(sum(v) / len(v), 3)]
                        for s, v in sorted(by_sec3.items())}

# ---------- Part 4 ----------
p1 = {}
with open("part1/data/index.csv") as f:
    for r in csv.DictReader(f):
        p1[(r["ticker"], int(r["year"]))] = r["page_type"]
about = defaultdict(dict)
with open("part1/data/theme_dictionary_scores.csv") as f:
    for r in csv.DictReader(f):
        k = (r["ticker"], int(r["year"]))
        if p1.get(k) != "about":
            continue
        hits = sum(int(r[c]) for c in r if c.startswith("hits_"))
        if hits >= 5:
            about[r["ticker"]][int(r["year"])] = float(r["share_diversity-inclusion"])
ay = defaultdict(list)
for t, ys in about.items():
    for y, v in ys.items():
        ay[y].append(v)
K["p4_about_dei_by_year_nonsparse"] = {y: round(sum(v) / len(v), 3)
                                       for y, v in sorted(ay.items())}
paired = {t: ys for t, ys in about.items() if 2021 in ys and 2022 in ys}
K["p4_paired_2021_2022"] = {
    "n": len(paired),
    "mean_2021": round(sum(ys[2021] for ys in paired.values()) / len(paired), 3),
    "mean_2022": round(sum(ys[2022] for ys in paired.values()) / len(paired), 3),
    "up": sum(1 for ys in paired.values() if ys[2022] > ys[2021]),
    "flat": sum(1 for ys in paired.values() if ys[2022] == ys[2021]),
    "down": sum(1 for ys in paired.values() if ys[2022] < ys[2021])}
for a, b in ((2020, 2022), (2022, 2024)):
    pp = {t: ys for t, ys in about.items() if a in ys and b in ys}
    K[f"p4_paired_{a}_{b}"] = {
        "n": len(pp),
        "from": round(sum(ys[a] for ys in pp.values()) / len(pp), 3),
        "to": round(sum(ys[b] for ys in pp.values()) / len(pp), 3)}
proxy = defaultdict(dict)
for r in scores:
    proxy[r["ticker"]][int(r["year"])] = float(r["share_diversity-inclusion"])
def peak(s):
    m = max(s.values())
    return min(y for y, v in s.items() if v == m)
res = {"proxy_first": 0, "same": 0, "about_first": 0}
for t in set(about) & set(proxy):
    if len(about[t]) < 6 or len(proxy[t]) < 6:
        continue
    if max(about[t].values()) == 0 or max(proxy[t].values()) == 0:
        continue
    pa, pp_ = peak(about[t]), peak(proxy[t])
    res["proxy_first" if pp_ < pa else "about_first" if pa < pp_ else "same"] += 1
K["p4_firm_peak_split_ge6"] = res

with open("key_numbers.json", "w") as f:
    json.dump(K, f, indent=1)
print(json.dumps(K, indent=1))
