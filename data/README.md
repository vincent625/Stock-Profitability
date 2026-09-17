# Data contracts

The model separates **calculation code** from **source data** so that missing fields are never silently invented.

## `quarterly_financials.csv`
One row per company fiscal quarter, ideally 20 quarters. Ratios and margins use decimals (`0.12` = 12%). Required for full EQ/valuation recomputation:
- `revenue_growth`
- `operating_margin`
- `fcf_margin`
- `pe`, `p_fcf`, `p_s`

`keymetrics fetch-quarterly` can create a best-effort public version via yfinance. Vendor-standardized data can simply replace it.

## `guidance_observations.csv`
One row per comparable management-guidance observation. Guidance is intentionally curated because historical management guidance is not consistently machine-readable from free public APIs.

- `metric_kind=absolute`: EPS/revenue values; error is relative to guide midpoint.
- `metric_kind=growth_pp`: growth-rate guidance; error is measured in percentage points.
- `include=0` excludes a year/observation when acquisition/IPR&D or another basis change makes it non-comparable.

## `forward_pe_history.csv`
Historical **forward** P/E is needed for the exact QQQ market-multiple scenario. yfinance does not provide a reliable 20-quarter forward-P/E history; use a licensed vendor or a maintained source table. The code falls back only when explicitly requested.

## `company_scenarios.csv`
Used for company-specific healthcare fundamental scenarios (normalized earnings/FCF, SOTP, revenue/EV, etc.). This is the place to keep model-specific overrides transparent rather than hiding them inside code.

## Snapshot folder
`data/snapshots/2026-09-01/` contains the exact inputs/outputs for the current 45-company centered-sentiment model. `keymetrics validate-snapshot` regression-tests the formulas against that snapshot.
