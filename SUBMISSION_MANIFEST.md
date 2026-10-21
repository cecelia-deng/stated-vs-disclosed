# Wharton People Analytics RA — Submission Package Manifest

Assembled 2026-10-20 (EDT) from the final, reviewed drafts.
Location: ~/workspace/wharton-ra/submission/ ; archive: submission.zip

## Contents

- `README.md` — project overview, headline findings, reproduction steps.
- `key_numbers.py` / `key_numbers.json` — every number quoted in the
  write-ups, computed from the data files (single source of truth).
- `part1/` — README.md, summary.md, code (wayback scaffold, LLM
  pipeline, dictionary scoring), data/ (index, llm_themes,
  theme_dictionary_scores, llm_changes, drift_dictionary,
  extracted texts), part1_output.csv, coverage_summary.csv.
- `part2/` — README.md, summary.md, code (EDGAR scaffold, dictionary
  scoring), data/ (index, theme_dictionary_scores), part2_output.csv,
  part2_theme_dictionary.md, part2_source_decision.md.
  (Full proxy texts, ~137 MB, are not in the package; every document
  is identified by accession + URL in data/index.csv and regenerable.)
- `part3/` — README.md, summary.md, part3_index.py,
  data/authenticity_index.csv, part3_output.csv.
- `part4/` — README.md (question, design, results in brief),
  summary.md (the essay).

## Verified at assembly

- Disclosure coverage 450/450 (incl. 3 DEFC14A contested-year filings,
  3 Broadcom predecessor-CIK filings, 11 recovered filing fragments).
- All figures in all eight documents match key_numbers.json;
  stale-figure sweep (0.086, 447, -34%, "similar magnitude") clean.
- Packaged part3_index.py and key_numbers.py re-run in place and
  reproduce the committed outputs byte-identically.
- First person ("I") throughout; Part 4 split into README + summary
  per the task's per-part deliverables.

## Still open (Cecelia's decisions)

- Submission channel: GitHub repository (task-preferred) vs email
  attachment — the Step 3 CV email (step3_cv_email_FINAL.md) is
  assembled and unsent, awaiting her go-ahead.
