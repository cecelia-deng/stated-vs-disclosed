# Part 1 — What Companies Say: Corporate "About" Pages, 2016–2024

## What this part does

For 50 large US companies, I collected one archived copy of each
company's official "About" (mission/values) page per year, 2016–2024,
from the Wayback Machine, extracted the text, and measured three
things: which of nine value themes each page expresses, whether the
page changed substantively from the previous available year, and how
each company's stated emphasis drifted over the nine years.

## Data and coverage

- 450 company-years targeted; **313 documents** had at least 100 words
  of usable text and enter the theme analysis; 78 company-years are
  documented gaps (no usable capture) and 59 are short fragments
  under 100 words (450 - 313 - 78 = 59).
- Each gap is recorded in `index.csv` with an `analyst_note`; following
  the task brief, gaps are documented, never filled by substitution
  (see the no-substitution rule below).

## How the page for each company was chosen

One entry URL per company for all nine years, selected by exact-match
Wayback CDX queries over a fixed candidate grid (`/about`, `/about-us`,
`/company`, `/our-company`, `/who-we-are`, homepage). An about-type
entry had to cover at least 5 of 9 years, otherwise the homepage is the
company's series. Per year I take the successful (HTTP 200) capture
closest to July 1; captures behind bot walls (HTTP 403) are excluded
even when the archive lists them. `page_type` is recorded **per
company-year**: 241 about rows, 209 homepage rows; 23 of 50 companies
are homepage-based. Homepage documents are as long as about documents
(~336 words/year on average) but carry fewer value themes
(3.35 vs 5.38 per document), so downstream analyses treat the two types
separately and Part 3's main sample uses about rows only.

**No cross-year substitution.** If a year has no usable capture, it
stays a gap. Substituting a neighbouring year's snapshot would
fabricate "no change" in exactly the measurement this part exists to
make.

**Exception: Meta.** Meta's series follows the company's own official
company-info page across its domain migrations
(newsroom.fb.com → about.fb.com → about.meta.com), because
facebook.com/about served login walls or logged-out homepage copy to
the crawler in most years; 2016–17 are flagged `page_type=homepage`.
This is one page migrating, not page-shopping — but the three
migration-adjacent pairs are flagged `artifact_flag=True` in the
change data and excluded from change-rate statistics, since their
measured "change" partly reflects the move itself (text similarity
0.15, 0.40 and 0.52, against a 0.998 median for unchanged pairs).

## Themes: two methods, one taxonomy

Nine themes, chosen because each has a counterpart disclosure area in
proxy statements (Part 2): innovation, customer-focus, integrity,
sustainability, diversity-inclusion, employee-wellbeing,
shareholder-value, community, excellence. `diversity-inclusion` is
defined to include successor vocabulary (belonging, inclusion,
opportunity for all) so post-2022 rewording is not misread as
disappearance.

1. **LLM labels** (`llm_themes.csv`): a Gemini model tagged each
   document's themes. Prevalence on the 168 about-type documents with
   usable text (the analytic sample; pooled figures including
   homepage documents are lower for most themes because homepage copy
   is product-led): customer-focus 87%, innovation 80%, excellence
   80%, community 64%, sustainability 57%, integrity 45%,
   diversity-inclusion 40%, shareholder-value 38%, employee-wellbeing
   20%.
2. **Dictionary labels** (`theme_dictionary_scores.csv`): the same
   keyword dictionary used in Part 2, so Parts 1 and 3 compare like
   with like. Agreement between the two methods ranges from 53%
   (customer-focus — the dictionary misses pages that talk about users
   without saying "customer") to 90% (diversity-inclusion). I report
   both and treat the gap as a measurement limitation, not a nuisance
   to hide.

## Year-over-year change: one ruler

`changed_from_prior` in `llm_changes.csv` applies one rule, fixed
in advance, to **all 266 consecutive-available-year pairs**: bag-of-words
cosine similarity ≤ 0.95 = substantive change (boilerplate churn moves
similarity far less than a rewrite). Change rates are reported by page
type, because homepage pairs change for product and news reasons that
have nothing to do with values: **about-type pairs changed in 51% of
cases (72/141); homepage pairs in 75% (92/122)**. The about-type year
pattern peaks in 2020 (65% of pairs) and otherwise sits in a 42–56%
band, lowest in 2024 (42%). All headline statements in the summary use
the about-type figures.

An LLM pass judged 142 pairs before the free-tier daily quota ran out;
I kept those verdicts (`llm_changed`) as validation rather than mixing
two rulers across companies — the LLM pass ran in list order, so a
mixed file would have confounded method with sector. Agreement is 89%
(126/142), and all 16 disagreements are one-directional: the rule never
invents a change; it misses subtle edits in near-identical texts
(similarity 0.951–0.998). Findings are reported under this limitation.

## Drift

`drift_dictionary.csv` compares each company's theme shares in
2016–19 vs 2021–24 (29 companies with enough years). The headline
pattern is diversity-inclusion, measured here by the LLM labels on
about-type documents only, all available years (n = 15–21 pages per
year): expressed by 40% of About pages in 2016, essentially flat
through 2021 (35–42%), spiking to 53% in 2022, and falling back to
37% by 2024. A balanced panel of the 6 firms with about pages in all
nine years (WFC, MS, PFE, SBUX, CVX, INTC) shows the same shape
(33% in 2021, 67% in 2022, 33% in 2024), though six firms cannot
carry precise percentages, and Part 4's paired dictionary test
shows that much of the aggregate 2022 jump is sample composition
rather than language change. I do
not report the pooled all-page-type series (21% in 2016 → 37% in
2022 → 29% in 2024): early years are homepage-heavy and homepage
copy rarely expresses this theme, so much of that apparent "rise" is
sample composition, not language change.

## Quality checks performed

- Bot-wall (403) captures and redirect-to-sitemap/404 captures
  identified and excluded.
- Language check on all extracted texts (langdetect): after replacing
  one French-locale capture (Alphabet 2023), the corpus is
  English-only.
- Alphabet's series uses google.com/about rather than the near-static
  abc.xyz founders' letter, which barely changed in nine years and is
  not the operating company's About page (a documented trade-off:
  5 of 9 years have ≥100 words there).
- The two theme methods were cross-validated against each other
  (above), and the change rule against LLM judgments (above).

## Limitations

- 23 of 50 companies are homepage-based (24 counting Meta, whose
  first two years are homepage captures); homepage text is
  marketing-heavy, and its "changes" can reflect site redesigns
  rather than values restatements.
- Dictionary-sparse documents (fewer than 5 total theme hits; 31 of
  the 168 about rows with usable text) have unstable theme shares and
  are excluded from Part 3's headline index; the excluded firms are
  simply terse-website firms, in consecutive multi-year runs — a
  non-random selection, acknowledged here.
- The change rule under-detects subtle edits (see above); "no change"
  should be read as "no substantial change".

## What I would do with more time

- Run the LLM change judgments for all 266 pairs (the free-tier quota
  stopped the pass at 142) and report rule-vs-LLM agreement by sector.
- Expand the dictionary for the diffuse themes — customer-focus above
  all, where pages talk about "users" and "people" without the
  literal words the dictionary keys on — and re-check agreement.
- Add a second human annotator for a 30-document sample of each
  document type, and report inter-annotator agreement alongside the
  two automated methods.
- Scale the identical pipeline to 500 firms; the collection and
  scoring code is firm-count-agnostic, and the balanced panel in
  particular would grow from 6 firms to a size that can carry the
  year-by-year percentages.

## Files

- `data/index.csv` — per company-year: chosen URL, archive
  timestamp, page_type, word count, analyst notes.
- `data/texts/` — extracted texts.
- `data/llm_themes.csv` — LLM theme labels per document.
- `data/theme_dictionary_scores.csv` — dictionary hits, shares,
  densities per document.
- `data/llm_changes.csv` — per pair: similarity,
  changed_from_prior (rule), llm_changed (validation subset),
  artifact_flag.
- `data/drift_dictionary.csv` — per company early-vs-late theme
  shares and biggest movers.
- Code: `part1_wayback_scaffold.py` (collection),
  `part1_llm_pipeline.py` (LLM stages), `part1_dictionary_scoring.py`.
