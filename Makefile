.PHONY: install test snapshot charts excel validate
install:
	python -m pip install -e '.[dev]'

test:
	pytest -q

validate:
	keymetrics validate-snapshot

snapshot:
	keymetrics snapshot --output output/snapshot

charts:
	keymetrics snapshot --output output/snapshot --charts

excel:
	python -m pip install -e '.[excel]'
	keymetrics snapshot --output output/snapshot --charts --xlsx
