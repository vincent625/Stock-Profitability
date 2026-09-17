# Key Metrics for Profitability

A reproducible 45-company equity-research model combining:

- **Earnings Quality** — 20-quarter revenue growth, operating margin and FCF margin
- **Valuation** — P/E, P/FCF and P/S, with missing/non-meaningful multiples reweighted rather than zeroed
- **Management Guidance Credibility** — historical guidance vs actuals with accuracy, range-hit and evidence-depth scoring
- **Bear / Base / Bull valuation** — historical-market-multiple scenarios plus fundamental valuation
- **News Sentiment / Catalyst overlay** — 7D / 30D / 90D sentiment, confidence shrinkage, event materiality, momentum and catalyst risk
- **Combined Opportunity ranking** — fundamentals remain the core; sentiment is a capped tactical overlay

The repository ships with the exact **September 1, 2026** 45-company model snapshot used to regression-test the formulas.

### Snapshot reconstruction caveat

The saved September 1 snapshot reflects the model state from this project: the QQQ leg retains the full 20-quarter reconstruction, while the healthcare snapshot preserves the established EQ/valuation screening inputs, annual guidance backtests and company-specific fundamental scenarios. Its standardized healthcare market-multiple leg was conservatively reconstructed when the original historical-ratio artifact was unavailable. New runs should replace that reconstruction with your own historical forward/trailing-multiple source where available.

> Research tooling only. This is not investment advice and the scenario values are not price targets.

## 1. Model architecture

### Fundamental Integrated Score

```text
30% Earnings Quality
30% Valuation
15% Confidence-adjusted Guidance Credibility
25% Hybrid Bear/Base/Bull Scenario Score
```

When a company has no comparable management guidance, the missing 15% is **not treated as zero**; the remaining weights are proportionally reweighted.

### Earnings Quality

For each fiscal quarter:

```text
Revenue score        = clamp(50 + revenue_growth × 200, 0, 100)
Operating margin     = clamp(30 + operating_margin × 200, 0, 100)
FCF margin score     = clamp(30 + fcf_margin × 233.3333, 0, 100)

Quarter EQ = 35% revenue + 35% operating margin + 30% FCF margin
```

Missing inputs are dynamically reweighted, but at least two components are required.

Company EQ composite:

```text
70% latest quarter + 30% average historical quarterly EQ
```

### Valuation

Higher score = cheaper.

```text
P/E   : 100 at 10x, 0 at 50x
P/FCF : 100 at 10x, 0 at 60x
P/S   : 100 at 1x,  0 at 12x

Valuation = 40% P/E + 35% P/FCF + 25% P/S
```

P/E <= 0 or > 100x is excluded rather than penalized as zero. Missing valuation components are reweighted.

Company valuation composite:

```text
70% latest valuation + 30% historical average valuation
```

### Guidance Credibility

The code supports both guidance methods used in the project:

1. **Healthcare annual/full-year guidance** — banded accuracy scoring, range hit, evidence factor.
2. **QQQ comparable recurring guidance** — accuracy declines linearly to zero at 10% absolute forecast error, plus range-hit scoring when a formal range exists.

Confidence adjustment used by the integrated model:

```text
High        1.00x
High/Medium 0.95x
Medium      0.90x
Medium/Low  0.80x
Low         0.65x
```

Historical guidance is intentionally a **curated input**. Free public APIs do not provide a reliable, standardized history of company-issued guidance across all 45 issuers.

### Bear / Base / Bull scenario score

Returns are mapped to 0–100 subscores:

```text
Bear: 0 at -60%, 100 at +20%
Base: 0 at -20%, 100 at +50%
Bull: 0 at   0%, 100 at +100%

Scenario Score = 35% Bear + 40% Base + 25% Bull
```

#### QQQ market-multiple leg

```text
Implied forward EPS = current price / current forward P/E

Bear EPS factor = 0.90
Base EPS factor = 1.10
Bull EPS factor = 1.25

Bear target P/E = own historical 25th percentile
Base target P/E = own historical median
Bull target P/E = own historical 75th percentile
```

Historical forward-P/E observations above 150x are excluded. If there are fewer than five valid historical observations, the fallback is 70% / 100% / 130% of current forward P/E.

#### QQQ fundamental leg

Screening-grade 5-year normalized-FCF DCF:

```text
Normalized FCF/share = current_price / latest_P/S × median positive FCF margin
Growth anchor         = 60% latest revenue growth + 40% median recent revenue growth
```

| Case | Discount | Terminal growth | Year-5 FCF growth |
|---|---:|---:|---:|
| Bear | 12% | 2% | 2.5% |
| Base | 10% | 3% | 5% |
| Bull | 9% | 4% | 8% |

QQQ default scenario blend is 50% market multiple / 50% fundamental DCF.

#### Healthcare fundamental leg

Healthcare keeps company-specific valuation methods when economically appropriate: normalized earnings/FCF, revenue/EV, SOTP, or other explicit fundamental scenarios. The generic pipeline accepts these as transparent `company_scenarios.csv` inputs rather than hiding company-specific assumptions inside code.

### Centered news-sentiment overlay

The old 95% fundamental + 5% sentiment blend was replaced because neutral sentiment should not reduce a strong fundamental score.

```text
Raw sentiment = 20% 7D + 50% 30D + 30% 90D

Adjusted sentiment = 50 + (Raw - 50) × Confidence

Confidence:
High   1.00
Medium 0.85
Low    0.65

Materiality:
Major    1.00
Moderate 0.70
Minor    0.30

Overlay = clamp(
    0.05 × (Adjusted Sentiment - 50) × Materiality,
    -2.5,
    +2.5
)

Opportunity Score = Fundamental Integrated + Overlay
```

So sentiment = 50 has **exactly zero impact**.

`Catalyst Risk` is tracked separately on a 0–100 scale and is deliberately **not** included in the Opportunity Score because high event risk can produce either positive or negative outcomes.

## 2. Repository layout

```text
config/
  model.yaml                 # every weight, threshold and calibration
  universe.csv               # QQQ 20 + healthcare 25

data/
  snapshots/2026-09-01/      # exact saved model regression fixture
  templates/                 # normalized input schemas
scripts/
  build_full_model.py        # complete normalized-input pipeline
  build_qqq_scenarios.py     # forward-P/E + DCF scenario builder
  score_guidance.py          # guidance backtest scoring
  score_news_live.py         # optional GDELT + FinBERT automation
  score_quarterly_inputs.py  # EQ + valuation quarter scoring
src/keymetrics/
  scoring.py
  guidance.py
  valuation.py
  sentiment.py
  quarterly.py
  full_model.py
  pipeline.py
  reporting.py
  data_sources/
tests/
  test_scoring.py
  test_snapshot.py
```

## 3. Quick start — exact saved snapshot

Python 3.11+ is recommended.

```bash
git clone <your-repo-url>
cd key-metrics-profitability
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e '.[dev]'
```

Validate the formulas against the shipped 45-company result:

```bash
keymetrics validate-snapshot
```

Build the saved model again:

```bash
keymetrics snapshot --output output/snapshot --charts
```

Optional Excel export:

```bash
pip install -e '.[excel]'
keymetrics snapshot --output output/snapshot --charts --xlsx
```

Expected core outputs:

```text
output/snapshot/fundamental_model.csv
output/snapshot/opportunity_ranking.csv
output/snapshot/top15_opportunity.png
output/snapshot/fundamental_vs_sentiment.png
output/snapshot/analysis.xlsx          # when --xlsx is used
```

## 4. Refresh the 20-quarter financial panel

Install the optional public-data adapter:

```bash
pip install -e '.[live]'
keymetrics fetch-quarterly \
  --universe config/universe.csv \
  --quarters 20 \
  --output data/live/quarterly_financials.csv
```

Then score the panel:

```bash
python scripts/score_quarterly_inputs.py \
  --input data/live/quarterly_financials.csv \
  --output output/quarterly_scored.csv \
  --summary output/quarterly_composites.csv
```

### Important live-data limitation

`yfinance` can provide a useful public quarterly panel, but it does **not** provide a dependable 20-quarter history of forward P/E. For the exact historical-forward-P/E model, maintain `forward_pe_history.csv` from a licensed/vendor source.

SpaceX is private and is marked `data_mode=manual` in `config/universe.csv`.

## 5. Recompute Guidance Credibility

Populate:

```text
data/templates/guidance_observations.csv
```

Then run:

```bash
python scripts/score_guidance.py \
  --input data/templates/guidance_observations.csv \
  --output output/guidance_summary.csv
```

The CSV explicitly stores guide low/high/midpoint, actual, metric type, comparability exclusions and source URL. This is deliberate: historical management guidance should be auditable.

## 6. Rebuild QQQ Bear / Base / Bull scenarios

Populate `data/templates/qqq_scenario_inputs.csv` with:

- current price
- current forward P/E
- semicolon-delimited historical forward-P/E observations
- latest P/S
- semicolon-delimited FCF-margin history
- latest revenue growth
- recent revenue-growth history

Run:

```bash
python scripts/build_qqq_scenarios.py \
  --input data/templates/qqq_scenario_inputs.csv \
  --output data/live/qqq_scenarios.csv
```

Healthcare company-specific scenario values can be maintained in `company_scenarios.csv` and combined with the QQQ output before running the full pipeline.

## 7. Optional live news sentiment

The snapshot sentiment table is analyst-reviewed. For automation, the repo includes a public GDELT + FinBERT workflow:

```bash
pip install -e '.[nlp]'
python scripts/score_news_live.py \
  --universe config/universe.csv \
  --output data/live/news_sentiment.csv
```

The automated news workflow:

1. queries recent English news from GDELT;
2. applies FinBERT to article titles;
3. calculates 7D / 30D / 90D sentiment;
4. shrinks sparse evidence toward neutral;
5. uses keyword heuristics for event materiality and catalyst risk.

**Review materiality and catalyst risk manually before using the scores for decisions.** Clinical trial, FDA, antitrust, litigation and M&A events often need context that headline NLP cannot reliably infer.

## 8. Complete normalized-input build

Once these files exist:

```text
data/live/quarterly_financials.csv
output/guidance_summary.csv
data/live/company_scenarios.csv
data/live/news_sentiment.csv
```

run:

```bash
python scripts/build_full_model.py \
  --quarterly data/live/quarterly_financials.csv \
  --guidance output/guidance_summary.csv \
  --scenarios data/live/company_scenarios.csv \
  --sentiment data/live/news_sentiment.csv \
  --output-dir output/live \
  --charts
```

Add `--xlsx` after installing the Excel optional dependency.

## 9. Reproducibility

The snapshot regression test is important because the model contains several layers where small implementation changes can alter rankings:

```bash
pytest -q
keymetrics validate-snapshot
```

The test recomputes:

- hybrid Bear/Base/Bull values;
- Bear/Base/Bull returns;
- Scenario Score;
- confidence-adjusted Guidance;
- Fundamental Integrated Score;
- raw and adjusted News Sentiment;
- centered sentiment overlay;
- final Opportunity Score.

It compares the results with the saved 45-company snapshot to `1e-8` tolerance.

## 10. Data-source philosophy

The model never treats missing values as zero unless zero is economically meaningful. In particular:

- missing guidance is **N/A**, not a zero score;
- negative/non-meaningful P/E is excluded and valuation weights are rebalanced;
- missing scenario legs fall back only when the method explicitly allows it;
- free APIs are not used to fabricate historical forward P/E or management guidance;
- source URLs belong in the input tables so every manual assumption can be audited.

## License

MIT. See `LICENSE`.
