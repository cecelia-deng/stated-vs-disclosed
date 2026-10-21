# Part 2 — Theme Dictionary and "False Friend" Rules

Method: dictionary-based scoring (`part2_dictionary_scoring.py`).
Each proxy statement's full text is matched against nine theme
keyword lists; the output per document is a hit count, a density
(hits per 10,000 words), and a share vector (the nine themes'
shares of all theme hits, summing to 1). The same dictionary,
unchanged, scores the Part 1 About pages, so Parts 2 and 3 compare
like with like.

## The dictionary

- **innovation**: innovation, innovative, research and development,
  patent(s), artificial intelligence, machine learning, digital
  transformation, invention, breakthrough, product development,
  technology, technologies
- **customer-focus**: customer(s), consumer(s), client(s), customer
  experience, customer satisfaction, user experience
- **integrity**: integrity, ethics, ethical, code of conduct, code
  of ethics, transparency, transparent, accountability, accountable,
  compliance culture, speak up, whistleblower
- **sustainability**: climate, emissions, net zero, net-zero,
  renewable, environmental, sustainability, sustainable, carbon,
  greenhouse gas, decarbonization, energy transition, environment,
  ESG
- **diversity-inclusion**: diversity, diverse (word-boundary, see
  below), board diversity, gender diversity, diversity and
  inclusion, diversity/equity phrases, inclusive, inclusion and
  belonging, belonging, pay equity, racial equity, gender equity,
  underrepresented, people of color, women in leadership, LGBTQ,
  veterans, ethnic, racial, gender
- **employee-wellbeing**: human capital, talent, retention, employee
  engagement, wellbeing, well-being, mental health, employee
  benefits, workforce, workplace safety, health and safety,
  training and development, our people, employees
- **shareholder-value**: shareholder value, total shareholder
  return, dividend(s), share/stock repurchase, buyback, return on
  invested capital, return on equity, earnings per share,
  long-term value, value creation, capital allocation
- **community**: community, communities, philanthropy,
  philanthropic, charitable, volunteering, volunteers, social
  impact, giving back, donation(s)
- **excellence**: excellence, excellent, operational excellence,
  quality, world-class, best-in-class, continuous improvement

## False-friend rules (the dictionary's one subtlety)

Financial documents reuse everyday words with different meanings,
so ambiguous words count only inside phrases that pin down the
intended sense:

- **equity** counts only in "pay equity", "racial equity",
  "diversity, equity" and similar phrases — never as bare "equity"
  (in a proxy, that is almost always stock compensation or
  shareholders' equity).
- **inclusion** counts only in phrases such as "diversity and
  inclusion" and "inclusion and belonging" — bare "inclusion"
  usually means inclusion of a shareholder proposal in the proxy
  materials.
- **benefits** counts only as "employee benefits" — bare
  "benefits" is usually executive-benefit plan language.
- **performance** is excluded entirely: it appears on nearly every
  page of pay discussion and carries no values signal.
- **engagement** counts only as "employee engagement" —
  "shareholder engagement" is investor-relations vocabulary.
- **diverse** is matched on word boundaries so it cannot fire on
  "diversified" (portfolio diversification).

## Known level effects

Proxy statements are governance documents, so integrity and
shareholder-value vocabulary has a high fixed baseline (codes of
conduct, dividend policy) in nearly every filing. This inflates
those themes' *levels* in a way that is roughly constant across
firms and years; it cancels in Part 3's within-document-type
standardisation and in the year-over-year comparisons, but theme
levels should not be compared naively across the two document
types. Employee-wellbeing has a documented caveat of its own: its
largest contributor is the generic word "employees", and a KWIC
spot-check found roughly half of those contexts are substantive
human-capital discussion and half compensation-plan mechanics
(see the Part 2 README).
