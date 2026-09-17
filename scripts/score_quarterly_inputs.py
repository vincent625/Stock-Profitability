#!/usr/bin/env python3
"""Score a normalized quarterly input file into EQ and valuation composites."""
from pathlib import Path
import argparse
from keymetrics.config import model_config
from keymetrics.io import read_csv, write_csv
from keymetrics.quarterly import score_quarterly_rows, company_quarterly_composites

p=argparse.ArgumentParser()
p.add_argument('--input',default='data/live/quarterly_financials.csv')
p.add_argument('--config',default='config/model.yaml')
p.add_argument('--output',default='output/quarterly_scored.csv')
p.add_argument('--summary',default='output/quarterly_composites.csv')
a=p.parse_args()
cfg=model_config(a.config)
rows=read_csv(a.input)
scored=score_quarterly_rows(rows,cfg['eq'],cfg['valuation'])
write_csv(a.output,scored)
summary=company_quarterly_composites(rows,cfg['eq'],cfg['valuation'])
write_csv(a.summary,[{'ticker':k,**v} for k,v in sorted(summary.items())])
print(f'Wrote {a.output} and {a.summary}')
