# Part 3 — The Organizational Authenticity Index

## What this part does

Parts 1 and 2 produce, for every company-year, two nine-theme
profiles: what the company *says* (About page) and what it formally
*discloses* (proxy statement), measured with the same dictionary.
This part combines them into an Organizational Authenticity Index:
the alignment between a firm's stated emphasis and its disclosed
emphasis, by theme, relative to other firms.

## Definition

For company *i* in year *t*: let **s** be the About page's theme
share vector and **d** the proxy's, both over the nine themes. Each
theme is z-scored **within its document type** over the main sample
(a theme's z for a document = how much more that document stresses
the theme than the average document of its type). The index is

```
authenticity(i, t) = cosine( z(s_t), z(d_{t+1}) )  in [-1, 1]
```

Three design choices, each deliberate:

1. **Same ruler both sides.** Both vectors come from the identical
   dictionary. An earlier design (LLM labels for About, dictionary
   for proxies) would have baked method differences into the
   "authenticity gap" itself.
2. **Z-scores, not raw shares.** Raw shares mostly encode document
   type: proxies are structurally heavy on shareholder-value and
   governance language, About pages on customer and innovation
   language, whatever the firm. Without standardisation, the index
   ranks firms on a narrow, document-driven band. With it, the
   index asks the relative question: does this firm stress theme X
   in its disclosures more than other firms do, in the same way its
   About page stresses X more than other firms' pages do? The
   standardisation demonstrably matters: firm rankings under the raw
   and standardised versions correlate at only Spearman 0.46.
3. **Lagged alignment as the main convention.** Most sample firms
   have December fiscal year-ends, so the proxy filed in spring
   *t+1* is the disclosure document for fiscal year *t*, the year
   the About snapshot describes. Same-year alignment is reported as
   a robustness variant. Caveat: lag alignment assumes spring
   filing; off-cycle filers such as MSFT (June fiscal year-end) and
   AVGO (October) may be misaligned by a year, and their scores —
   AVGO's top ranking included — should be read with that caution.

**Sample.** The main sample is row-level: company-years whose About
text is a genuine about-type page (`page_type == 'about'`) — 168
company-years with both sides present. Dictionary-sparse About
documents (fewer than 5 total theme hits, whose shares are unstable)
are excluded from the headline index, leaving 137 company-years for
the z-score estimation and 121 lagged scores (2016–2023); the
with-sparse variant is reported as robustness.

## Results

- **Distribution.** Mean 0.16, SD 0.31, median 0.13, range
  -0.65 to 0.84 (n = 121). The index varies substantially across
  firms and years, as the task requires.
- **Time pattern.** Mean alignment rises from 0.02 (2017), peaks around
  2021 (0.25), with a modest dip in 2022 (0.19) and 0.21 in 2023. Each year's mean rests on only n = 11-18 company-years,
  so single-year values should be read as indicative, not precise. A robustness check standardising *within* each year,
  which removes the common shock that pushed all firms' language in
  the same direction, leaves the shape intact and the 2021 peak
  slightly *stronger* (0.30), so the pattern is not an artefact of
  everyone talking about the same themes at once.
- **Firms.** Highest mean alignment: AVGO (0.55, with the off-cycle
  caveat above), Amazon (0.47), JPMorgan (0.40), Phillips 66
  (0.40), Intel (0.34). Lowest: Microsoft (-0.25
  under the headline lag — and the off-cycle asterisk does not
  rescue it: under the timing that fits Microsoft's fiscal
  calendar (same-year), its score is -0.40, and it ranks lowest
  under either convention), Tesla (-0.08), Marathon
  Petroleum (-0.08). **This measures disclosure alignment, not
  corporate ethics**: the bottom of the table mostly reflects
  structural mismatch between what a firm's About page talks about
  and what its proxy is required to cover, not a verdict on any
  firm's sincerity.
- **Sectors (descriptive only).** Using the task's five sector
  labels throughout: Financials 0.18 (n=19), Energy 0.17 (n=32),
  Healthcare 0.17 (n=25), Technology 0.15 (n=25), Consumer
  Discretionary 0.14 (n=20). Sector cells rest on as few as 4 firms
  and should be read as descriptive.

## Validity check: Wells Fargo

Wells Fargo is the sample's known hard case — its fake-accounts
scandal broke in September 2016. Its four-year mean for 2016–19
(0.06) is well below the sample mean (0.16), ranking 7th lowest of
24 firms, and turns negative by 2019; the year-to-year path is
noisy (2016: 0.13, 2017: 0.36, 2018: 0.06, 2019: -0.30). One timing
detail strengthens the reading: the 2016 snapshot (taken around
July 1) *predates* the scandal's September 2016 exposure and sits
near the sample mean. The deterioration comes after. The index
does not flatter the firm behind the sample's best-known values
scandal, which is modest face validity. (WFC's 2020–24 About pages are
dictionary-sparse; those years appear only in the robustness
variant.)

## Limitations

1. **Both sides are the company's own words.** The proxy is what a
   firm tells shareholders, not observed behaviour. The index
   measures *disclosure alignment*; I name it honestly rather than
   claim it captures authenticity itself.
2. **Same-dictionary measurement error is correlated across
   sides.** A theme the dictionary systematically misses (or
   over-counts) is missed on both ends, which can inflate alignment.
   Mitigations: the dictionary was validated against independent
   LLM labels on the About side (Part 1), and the index is
   interpreted relatively (z-scores), never as an absolute.
3. **About pages are sticky**, so much of the index's year-to-year
   movement comes from the proxy side; small wiggles should not be
   over-read.
4. **Sparse-row exclusion is non-random** (it removes terse-website
   firms in multi-year runs) and the main sample's sector cells are
   small; both are acknowledged in the sample definition above.

## What I would do with more time

- Score a second disclosure type (10-K human-capital sections) and
  check whether the index is stable across choices of the "did"
  document.
- Replace first-peak-year timing tests with cross-correlation of
  each firm's two theme series, which uses all years rather than a
  single maximum.
- Validate against an external criterion (e.g., published ESG
  controversy events) for a handful of firms beyond Wells Fargo.

## Files

- `data/authenticity_index.csv` — per company-year: both
  vectors, the headline index, and the robustness variants
  (contemporaneous, raw-share, L1, Jaccard, with-sparse,
  within-year-z), coverage and sparsity flags.
- Code: `part3_index.py`. Design rationale: this document and
  `part3_index_methodology.md`.
