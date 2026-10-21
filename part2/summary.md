# Part 2 Summary — What Companies Formally Disclose

If the About page is what a company says about itself, the proxy
statement is its formal account to shareholders. Every year, each public company must file
one with the SEC before its annual meeting, accounting for who sits
on the board, how executives are paid, how human capital is managed,
and how the board responds to shareholder proposals. This part of
the project collected those statements for the same 50 companies
over 2016–2024 (450 of 450 company-years) and scored each one on
the same nine value themes used for the About pages; the documents
run to a median of about 46,000 words.

The scoring method is deliberately plain: a keyword dictionary,
built for this corpus. Its one subtlety matters. Financial documents
reuse everyday words with different meanings ("equity" in a proxy
statement is almost always stock compensation, not fairness), so
ambiguous words were only counted inside phrases that pin down the
intended meaning ("pay equity", "diversity and inclusion",
"employee benefits"), and a few hopeless cases ("performance",
which appears on nearly every page of pay discussion) were excluded
altogether. The result for each document is a profile: what fraction
of its values-language goes to each of the nine themes.

Three features of those profiles stand out. First, the largest
single theme is employee wellbeing (about a quarter of all theme
language). Much of it, though, is the vocabulary of pay and human
capital management rather than wellbeing as an About page would mean
it. Second, diversity and inclusion language follows a clear arc:
8.4% of theme language in 2016, rising to a peak of 16.0% in the 2021
statements, the ones reporting on fiscal 2020, the year of the
pandemic and the George Floyd protests, and receding to 11.9% by
2024. Third, sustainability language crested later and higher, and
stayed there: from 12.6% in 2016 to a plateau of about 26% in
2022–23, still 25.6% in 2024.

A note on how these numbers were nearly wrong: the first download
of this corpus silently produced corrupted files whose word counts
looked plausible but were far too small for real proxy statements.
The implausibility was the clue; the corpus was re-collected with
the bug fixed and verified document by document. I describe this
because the check that caught it ("does this number make sense for
this kind of document?") is part of the method, not an aside.

What this part cannot do is judge sincerity: a dictionary measures
emphasis, not depth. Whether the emphasis in these formal
disclosures lines up with the values the same companies advertise,
and how each of the two channels responds when the world changes,
is what Parts 3 and 4 measure.

For a reader comparing companies, the proxy is where the differences are: it is the one values document every firm must produce, on the same calendar, in a comparable form.
