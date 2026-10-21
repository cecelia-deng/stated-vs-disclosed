# Part 2 — What Companies Disclose: Proxy Statements (DEF 14A), 2016–2024

## What this part does

Part 1 measured what companies *say* on their About pages. This part
measures the formal counterpart: what the same 50 companies
*disclose* to shareholders in their annual proxy statements
(Form DEF 14A, SEC EDGAR), 2016–2024, scored on the same nine value
themes with the same dictionary, so the two sides can be compared
like with like in Part 3.

## Why proxy statements

The task allowed ESG reports, sustainability/DEI reports, or proxy
statements. I chose proxy statements because they are (i) mandatory
and therefore available for all 50 firms in all years — voluntary ESG
reports are not, which would have built selection into the sample;
(ii) filed on a known calendar with a stable structure, so
year-to-year comparison is meaningful; and (iii) the document in
which boards formally account for governance, executive pay, human
capital and shareholder proposals. It is the closest formal
counterpart to the values an About page advertises. The full reasoning is in
`part2_source_decision.md`.

## Coverage and a data-quality note

450 of 450 company-years have full text (median 45,847 words per
document); there are no gaps. Getting to complete coverage took
three recovery passes, all instructive:

- **Form variants.** A collector that recognises only DEF 14A
  systematically misses *contested* years: when a proxy fight is on,
  the company's own definitive statement is filed as **DEFC14A**.
  Three of the gaps were exactly that — ExxonMobil 2021 (the Engine
  No. 1 fight), McDonald's 2022 (the Icahn campaign) and Starbucks
  2024 — recovered from the same accessions once the form list was
  widened. (Two further misses were mundane: a wrong document
  selected inside NVIDIA's 2022 filing package, and Amazon's
  table-heavy Inline XBRL statements, which the default extractor
  silently under-read until a fallback extractor was used.)
- **Predecessor entities.** Broadcom's 2016–18 statements were
  filed under its pre-redomiciliation Singapore entity, Broadcom
  Limited, which has a different CIK from today's Broadcom Inc. A
  collector keyed to the current CIK silently misses a company's
  pre-merger or pre-redomiciliation years; the series was completed
  by searching the predecessor entity.
- **Fragment audit.** Word counts alone did not catch a subtler
  failure: eleven 2023–24 documents of 600–900 words that were
  single exhibits from inside the filing package, not the proxy.
  They were found by inspecting the low tail of the length
  distribution (the thinnest genuine proxy in the corpus, Berkshire
  Hathaway's, is ~9,700 words) and every one was recovered from its
  accession. Final rule: no document under 9,000 words is accepted
  without manual inspection.

An earlier collection pass silently saved corrupted files (the
downloader requested gzip encoding but did not decompress it, so the
" texts" were binary noise whose word counts — a plausible-looking
2,000–6,000 per document — should have been impossible for real
proxies, which run to tens of thousands of words). The bug was caught
on exactly that plausibility check, the downloader was fixed, a
letter-ratio sanity guard was added so corrupt text can never pass
as data again, and the corpus was re-downloaded and verified
end-to-end (documents begin with the meeting notice and end with the
proxy card).

## Method: dictionary scoring, LLM as validation only

Each document is scored with a nine-theme keyword dictionary
(`part2_theme_dictionary.md`): hits per theme, theme share (hits /
total theme hits, summing to 1) and density per 10,000 words. The
method was chosen over LLM scoring because it runs in minutes over
450 long documents with no API quota, is fully reproducible, needs
no section extraction (proxy section headings vary too much across
firms for extraction to be safe), and scales from 50 to 500 firms
unchanged — the task's scalability requirement. An LLM validation
sample is listed under "more time" below; the same dictionary
validated against LLM labels on the About side in Part 1 (agreement
53–90% by theme).

**False friends.** Proxy statements are financial documents, and
several dictionary candidates mean something else there. Ambiguous
words were entered only as disambiguating phrases, never bare: in
this corpus "equity" almost always denotes equity *compensation*, so
the dictionary matches "pay equity", "racial equity" and
"diversity, equity" only; "inclusion" is matched only in phrases
such as "diversity and inclusion" (bare "inclusion" usually refers
to including shareholder proposals in the statement); "benefits"
only as "employee benefits"; "performance" is excluded entirely
(it saturates the compensation discussion); "diverse" is
word-boundary matched so "diversified" (portfolio diversification)
never counts.

## What the disclosures look like

Mean theme shares across 450 proxies: employee-wellbeing 0.236
(largely human-capital and compensation vocabulary; see the audit
note below), sustainability 0.181, shareholder-value 0.124,
diversity-inclusion 0.124, innovation 0.100, integrity 0.086,
customer-focus 0.070, community 0.052, excellence 0.026. Two
trajectories carry into Part 4 (theme shares, all firms):

- **Diversity-inclusion:** 0.084 (2016) → peak 0.160 (2021) → 0.119
  (2024). The 2021 proxy — filed in spring 2021, reporting fiscal
  2020 — is where the post-2020 disclosure response lands.
- **Sustainability:** 0.126 (2016) → a 2022–23 plateau at ~0.26 →
  0.256 (2024): a larger, later crest that, unlike diversity, had
  barely receded by 2024. The plateau coincides with the wave of
  environmental shareholder proposals in the 2022 season and with
  the SEC's climate-disclosure proposal of March 2022.

**Cross-sector and cross-company comparison.** Theme emphasis
differs sharply by sector (mean shares): Energy's sustainability
share (0.314) is nearly double the next sector's, as its business
would predict; diversity-inclusion is similar in Financials,
Consumer Discretionary and Technology (0.146–0.149) and lowest
in Energy (0.081); shareholder-value is, counterintuitively,
*lowest* in Financials (0.079) and highest in Healthcare (0.170).
Bank proxies spend their words on governance and pay mechanics
rather than capital-return vocabulary. At company level the
extremes are an energy story: Occidental's 2022 statement (0.666
sustainability share) and ExxonMobil's 2023 statement (0.638) are
the corpus's most sustainability-saturated documents, while
Berkshire Hathaway's famously thin 2020 statement is the most
diversity-saturated (0.439) — a reminder that shares on short
documents swing widely.

**What drives each theme (audit).** Top contributing terms per
theme across the corpus — diversity: diversity, diverse, gender,
racial, inclusive; sustainability: sustainability, environmental,
climate, ESG, environment; integrity: ethics, transparency,
accountability, integrity, code of conduct; shareholder-value:
dividend(s), shareholder value, earnings per share, total
shareholder return; innovation: technology, innovation,
technologies. One flag: employee-wellbeing is dominated by the bare
word "employees" (24,089 hits, ~5x the next term). A KWIC spot-check
of random contexts found roughly half substantive human-capital
discussion (surveys, training, reporting channels) and half
compensation-plan mechanics (pay eligibility, risk-taker
definitions). On the proxy side this theme is therefore best read
as overall people-and-pay emphasis; its level, unlike its movement
over time, should be interpreted with that caution.

## Limitations

- Fixed proxy boilerplate (voting procedures, board elections)
  inflates the baseline of governance-adjacent themes for every
  firm. This is a level effect: Part 3 compares firms' *relative*
  emphasis (z-scores) and within-firm change, where the constant
  boilerplate component cancels.
- A dictionary is literal: it misses disclosures phrased outside its
  vocabulary and cannot judge depth or sincerity — it measures
  emphasis, not quality.
- One document type cannot represent everything a firm "does";
  see Part 3's framing of the index as *disclosure* alignment.

## What I would do with more time

- Run the LLM validation sample (~30 proxies scored independently)
  and report dictionary-vs-LLM agreement on the disclosure side, as
  was done for About pages in Part 1.
- Separate shareholder-proposal sections from board sections and
  score them independently — proposals show what shareholders push
  for; the board's response shows what the firm accepts.
- Add pay-ratio and human-capital sub-scores as the SEC's disclosure
  rules phase in over the sample period.
- Measure tone as well as topic: the task asks about "language,
  tone, and topic emphasis", and this part covers topic emphasis.
  A Loughran-McDonald financial-sentiment pass over the same corpus
  (uncertainty and litigious word shares by year) is the natural
  extension and needs no new data.

## Files

- `data/index.csv` — per company-year: filing date, form,
  accession number, document URL, word count, notes.
- `data/texts/` — extracted full texts.
- `data/theme_dictionary_scores.csv` — per document: hits,
  shares and densities for the nine themes.
- Code: `part2_edgar_scaffold.py` (collection),
  `part2_dictionary_scoring.py` (scoring); dictionary and rationale:
  `part2_theme_dictionary.md`.
