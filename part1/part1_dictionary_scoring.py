#!/usr/bin/env python3
"""
part1_dictionary_scoring.py - run the Part 2 theme dictionary over the
Part 1 About-page texts, so Part 3 compares both sides with the SAME
ruler (Qing's ruling 2026-10-20). The Part 1 LLM labels stay in
llm_themes.csv and serve as the cross-method consistency check.

Eligibility mirrors the LLM stage: usable texts with >= 100 words
(all rows incl. homepage - Part 3 filters the main sample itself).

Output: data/theme_dictionary_scores.csv (same columns as Part 2)
Usage: python3 part1_dictionary_scoring.py
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from part2_dictionary_scoring import DICTIONARY, score_text  # noqa: E402

MIN_WORDS = 100


def main():
    with open("data/index.csv") as f:
        rows = list(csv.DictReader(f))
    themes = list(DICTIONARY)
    out_path = "data/theme_dictionary_scores.csv"
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "year", "total_words"] +
                   [f"hits_{t}" for t in themes] +
                   [f"share_{t}" for t in themes] +
                   [f"per10k_{t}" for t in themes])
        n = low = 0
        for r in rows:
            path = r["page_text_clean"]
            if not os.path.exists(path):
                continue
            text = open(path, encoding="utf-8", errors="replace").read()
            if len(text.split()) < MIN_WORDS:
                continue
            tw, hits, shares, density = score_text(text)
            w.writerow([r["ticker"], r["year"], tw] +
                       [hits[t] for t in themes] +
                       [shares[t] for t in themes] +
                       [density[t] for t in themes])
            n += 1
            if sum(hits.values()) < 5:
                low += 1
    print(f"scored {n} About documents -> {out_path} "
          f"({low} with <5 total theme hits: sparse, Part 3 flags them)")


if __name__ == "__main__":
    main()
