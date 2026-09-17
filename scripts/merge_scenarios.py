#!/usr/bin/env python3
"""Merge QQQ generated scenarios and healthcare/company-specific scenarios."""
import argparse
from keymetrics.io import read_csv, write_csv

p=argparse.ArgumentParser()
p.add_argument('--qqq',default='data/live/qqq_scenarios.csv')
p.add_argument('--other',default='data/live/healthcare_scenarios.csv')
p.add_argument('--output',default='data/live/company_scenarios.csv')
a=p.parse_args()
rows=read_csv(a.qqq)+read_csv(a.other)
seen=set()
for r in rows:
    t=r['ticker']
    if t in seen: raise SystemExit(f'Duplicate ticker in scenario inputs: {t}')
    seen.add(t)
write_csv(a.output,rows)
print(f'Wrote {len(rows)} scenario rows to {a.output}')
