# Part 4 — README: Which Channel Moves First?

## Question

When an external shock hits, which channel moves first: the formal
disclosure document, or the self-description a firm can edit any
day? And does the aggregate answer hold firm by firm?

## Data and design

The test case is diversity-inclusion language around a dated shock
(2020) and its partial reversal (2023 onward), measured on both
channels with the identical instrument: dictionary theme shares
from Part 1 (`../part1/data/theme_dictionary_scores.csv`, About side
restricted to about-type pages with at least 5 total theme hits)
and Part 2 (`../part2/data/theme_dictionary_scores.csv`). Three
checks, in increasing strictness:

- **A. Aggregate curves.** Mean theme share by year on each
  channel. Fast, but exposed to sample-composition effects, because
  the set of measurable About pages changes over time.
- **B. Paired check.** The same curves recomputed on firms present
  in the sample in *both* years of a comparison (e.g. 2021 and
  2022). This is the composition-proof version of A.
- **C. Firm-level peak timing.** For each firm with at least six
  usable years on both channels, the year its diversity share
  peaks on each channel; tallied as proxy-first / same-year /
  About-first. Aggregate curves can be driven by a few large
  movers, so C asks whether the aggregate pattern is also the
  typical firm's pattern.

My initial hypothesis, from the aggregate curves alone, was a
lead-lag: disclosure peaks in 2021, websites follow in 2022. The
hypothesis did not survive check B, and the summary reports the
finding that replaced it. All figures are in `key_numbers.json`.

## Results in brief

1. Proxy diversity share: 0.084 (2016) → 0.160 peak (2021) →
   0.119 (2024), on complete coverage (450 of 450 documents).
2. About-page diversity share (aggregate) peaks a year later,
   0.092 in 2022, against 0.056 in 2024 — but see (3): in the
   paired sample that peak largely disappears.
3. Paired check (12 firms, 2021→2022): About moves only
   0.071 → 0.079 (+0.008; 2 up, 8 flat, 2 down) against +0.026
   unpaired. The aggregate website "surge" is mostly sample
   composition.
4. Firm-level peak years split evenly (4 proxy-first, 0 same,
   4 About-first at the ≥6-year cut; 7–7 in the wider cut).
