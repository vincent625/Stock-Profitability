#!/usr/bin/env python3
"""Recompute guidance credibility from the standardized observation CSV."""
import argparse
from collections import defaultdict
from keymetrics.config import model_config
from keymetrics.guidance import GuidanceObservation, credibility
from keymetrics.io import read_csv, write_csv, as_float

p=argparse.ArgumentParser()
p.add_argument('--input',default='data/templates/guidance_observations.csv')
p.add_argument('--config',default='config/model.yaml')
p.add_argument('--output',default='output/guidance_summary.csv')
a=p.parse_args(); cfg=model_config(a.config)
by=defaultdict(list); meta={}
for r in read_csv(a.input):
    if not r.get('ticker'): continue
    lo=as_float(r.get('guide_low')); hi=as_float(r.get('guide_high')); mid=as_float(r.get('guide_mid')); actual=as_float(r.get('actual'))
    if mid is None or actual is None: continue
    obs=GuidanceObservation(r['ticker'],r.get('period',''),r.get('metric',''),r.get('metric_kind','absolute'),lo,hi,mid,actual,r.get('include','1').lower() not in {'0','false','no'},r.get('notes',''),r.get('source',''))
    by[r['ticker']].append(obs); meta[r['ticker']]=r.get('universe','Healthcare')
out=[]
for t,obs in sorted(by.items()):
    universe=meta[t]
    method='linear' if universe=='QQQ' else 'banded'
    emap=cfg['guidance']['qqq_evidence_factor'] if universe=='QQQ' else cfg['guidance']['healthcare_evidence_factor']
    x=credibility(obs,method,emap,float(cfg['guidance']['observation_range_weight']))
    out.append({'ticker':t,'universe':universe,**x})
fields=['ticker','universe','observations','average_observation_score','evidence_factor','credibility','confidence','avg_abs_error','avg_bias','range_hit_rate']
write_csv(a.output,out,fieldnames=fields); print(f'Wrote {a.output}')
