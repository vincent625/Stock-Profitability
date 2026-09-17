# Contributing

1. Keep all scoring assumptions in `config/model.yaml`, not scattered as magic numbers.
2. Add or update tests whenever a score formula changes.
3. Run `pytest -q` and `keymetrics validate-snapshot` before committing.
4. Never replace missing company guidance or valuation fields with zero unless zero is economically meaningful.
5. Keep source URLs for manually curated guidance, forward-P/E and company-specific scenario assumptions.
6. If changing model methodology, save a new dated snapshot rather than overwriting the existing regression fixture.
