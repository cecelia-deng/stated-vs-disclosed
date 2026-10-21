#!/usr/bin/env python3
"""
part2_dictionary_scoring.py - dictionary-based theme scoring for Part 2.

Method (chosen 2026-10-20, see part2_theme_dictionary.md):
Classical dictionary scoring over the full proxy text - no LLM quota,
fully reproducible, scales 50 -> 500 firms unchanged. For each document:
count hits per theme, report density (hits per 10k words) and the theme
SHARE vector (hits_theme / total hits across the 9 themes, sums to 1).

FALSE-FRIEND RULE (important in proxy statements, which are financial
documents): any word whose dominant proxy meaning is NOT the values
meaning is entered ONLY as part of a disambiguating phrase, never bare:
  equity      -> stock compensation by default; only "pay equity",
                 "racial equity", "gender equity", "diversity, equity"
  inclusion   -> often "inclusion of shareholder proposals in the proxy
                 statement"; only "diversity and inclusion",
                 "inclusive culture", "inclusion and belonging"
  benefits    -> usually retirement / executive benefits; only
                 "employee benefits", "employee wellbeing"
  performance -> saturates the compensation discussion; never counted
  engagement  -> usually shareholder engagement; only "employee
                 engagement"
  diverse     -> matched with a word boundary so "diversified"
                 (portfolio diversification) never counts

LLM validation (a ~30-document Gemini sample scored on the same 9
themes, agreement reported) is a separate script; this one is the
primary method.

Usage: python3 part2_dictionary_scoring.py [--data ./data]
Output: data/theme_dictionary_scores.csv
"""
import argparse
import csv
import os
import re

DICTIONARY = {
    "innovation": [
        "innovation", "innovative", "research and development", "patent",
        "patents", "artificial intelligence", "machine learning",
        "digital transformation", "invention", "breakthrough",
        "product development", "technology", "technologies",
    ],
    "customer-focus": [
        "customer", "customers", "consumer", "consumers", "client",
        "clients", "customer experience", "customer satisfaction",
        "user experience",
    ],
    "integrity": [
        "integrity", "ethics", "ethical", "code of conduct",
        "code of ethics", "transparency", "transparent", "accountability",
        "accountable", "compliance culture", "speak up", "whistleblower",
    ],
    "sustainability": [
        "climate", "emissions", "net zero", "net-zero", "renewable",
        "environmental", "sustainability", "sustainable", "carbon",
        "greenhouse gas", "decarbonization", "energy transition",
        "environment", "esg",
    ],
    "diversity-inclusion": [
        "diversity", "diverse", "board diversity", "gender diversity",
        "diversity and inclusion", "diversity, equity", "inclusive",
        "inclusion and belonging", "belonging", "pay equity",
        "racial equity", "gender equity", "underrepresented",
        "people of color", "women in leadership", "lgbtq", "veterans",
        "ethnic", "racial", "gender",
    ],
    "employee-wellbeing": [
        "human capital", "talent", "retention", "employee engagement",
        "wellbeing", "well-being", "mental health", "employee benefits",
        "workforce", "workplace safety", "health and safety",
        "training and development", "our people", "employees",
    ],
    "shareholder-value": [
        "shareholder value", "total shareholder return", "dividend",
        "dividends", "share repurchase", "stock repurchase", "buyback",
        "return on invested capital", "return on equity",
        "earnings per share", "long-term value", "value creation",
        "capital allocation",
    ],
    "community": [
        "community", "communities", "philanthropy", "philanthropic",
        "charitable", "volunteering", "volunteers", "social impact",
        "giving back", "donations", "donation",
    ],
    "excellence": [
        "excellence", "excellent", "operational excellence", "quality",
        "world-class", "world class", "best-in-class", "best in class",
        "continuous improvement",
    ],
}

PATTERNS = {theme: [re.compile(r"\b" + re.escape(kw) + r"\b")
                    for kw in kws]
            for theme, kws in DICTIONARY.items()}


def score_text(text):
    low = text.lower()
    total_words = len(low.split())
    hits = {}
    for theme, pats in PATTERNS.items():
        hits[theme] = sum(len(p.findall(low)) for p in pats)
    total_hits = sum(hits.values())
    shares = {t: (round(hits[t] / total_hits, 4) if total_hits else 0.0)
              for t in hits}
    density = {t: (round(hits[t] / total_words * 10000, 2)
                   if total_words else 0.0) for t in hits}
    return total_words, hits, shares, density


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="./data")
    args = ap.parse_args()

    index_path = os.path.join(args.data, "index.csv")
    out_path = os.path.join(args.data, "theme_dictionary_scores.csv")
    themes = list(DICTIONARY)
    with open(index_path) as f:
        rows = list(csv.DictReader(f))
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "year", "total_words"] +
                   [f"hits_{t}" for t in themes] +
                   [f"share_{t}" for t in themes] +
                   [f"per10k_{t}" for t in themes])
        n = 0
        for r in rows:
            path = r["text_path"]
            if not os.path.exists(path):
                continue
            text = open(path, encoding="utf-8", errors="replace").read()
            if len(text.split()) <= 500:
                continue  # the documented Part 2 gaps
            tw, hits, shares, density = score_text(text)
            w.writerow([r["ticker"], r["year"], tw] +
                       [hits[t] for t in themes] +
                       [shares[t] for t in themes] +
                       [density[t] for t in themes])
            n += 1
    print(f"scored {n} proxy documents -> {out_path}")


if __name__ == "__main__":
    main()
