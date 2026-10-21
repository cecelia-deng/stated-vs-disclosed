# Stated vs. Disclosed: Organizational Authenticity in 50 Large US Firms, 2016–2024

**Qing Deng** — Research Assistant recruitment task, Wharton People
Analytics / Wharton–TAU Lab.

## What this project does

For the same 50 large US companies over 2016–2024, I measure what
each company *says* about its values (its About page, recovered from
the Wayback Machine) and what it formally *discloses* (its annual
proxy statement, from SEC EDGAR), score both with one nine-theme
instrument, and ask how the two relate — including when an external
shock (2020) hits.

- **Part 1** — 450 company-year About/homepage captures, two
  independent codings (LLM labels and a keyword dictionary,
  53–90% agreement by theme). About pages are sticky: about half of
  year-to-year comparisons show a substantive rewrite.
- **Part 2** — all 450 proxy statements (median ~46,000 words),
  scored with the same dictionary. Diversity language in proxies
  nearly doubled to a 2021 peak and receded; sustainability
  crested later (a 2022–23 plateau) and had barely receded by 2024.
- **Part 3** — an Organizational Authenticity Index: cosine
  similarity between a firm's standardised About-page theme profile
  and the following spring's proxy profile (mean 0.16 over 121
  company-years; Wells Fargo, the sample's known scandal case,
  scores well below average, as it should).
- **Part 4** — which channel responds to a shock? The disclosure
  channel: proxy diversity language nearly doubled, while
  continuously observed About pages barely moved; the apparent
  2022 website surge is mostly a sample-composition artefact.

## Repository structure

- `part1/` … `part4/` — for each part: `README.md` (what I did,
  why, assumptions, limitations, what I would do with more time),
  `summary.md` (a 1–2 page non-technical summary; Part 4's design
  notes are in its README and its essay is its summary), the code,
  and the output data (`partN_output.csv` plus supporting files).
- `key_numbers.py` / `key_numbers.json` — every number quoted in
  the four READMEs and summaries is computed by this script from
  the data files and stored in the JSON, so the write-ups can be
  audited figure by figure.

## Reproduction

Python 3 with a virtual environment (`pip install requests
beautifulsoup4 trafilatura pandas`). Run from each part's folder:
Part 1 collection (`part1_wayback_scaffold.py`) then labelling
(`part1_llm_pipeline.py`, needs a Gemini API key; the free tier's
daily quota is a real constraint, documented in the README) and
dictionary scoring; Part 2 collection (`part2_edgar_scaffold.py`)
then `part2_dictionary_scoring.py`; Part 3 `part3_index.py`; from
the repository root, `key_numbers.py` regenerates every reported
figure.

## Data notes

- Part 1 extracted texts are included (`part1/data/texts/`). Part 2
  full texts total ~137 MB and are not committed; every document is
  identified by accession number and URL in `part2/data/index.csv`
  and can be re-downloaded exactly with `part2_edgar_scaffold.py`.
- Coverage is complete on the disclosure side (450 of 450 proxy
  statements, including three contested-year DEFC14A filings and
  three statements filed under Broadcom's predecessor entity) and
  documented year by year, with gaps, on the About side
  (`part1/coverage_summary.csv`).
