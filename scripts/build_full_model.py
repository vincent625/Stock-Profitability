#!/usr/bin/env python3
"""Build the complete model from normalized quarterly/guidance/scenario/news inputs."""
import argparse
from keymetrics.config import model_config
from keymetrics.io import read_csv, write_csv
from keymetrics.full_model import build_fundamental_model
from keymetrics.pipeline import apply_sentiment_overlay
from keymetrics.reporting import make_charts, export_xlsx

p=argparse.ArgumentParser()
p.add_argument('--config',default='config/model.yaml')
p.add_argument('--universe',default='config/universe.csv')
p.add_argument('--quarterly',default='data/live/quarterly_financials.csv')
p.add_argument('--guidance',default='output/guidance_summary.csv')
p.add_argument('--scenarios',default='data/live/company_scenarios.csv')
p.add_argument('--sentiment',default='data/live/news_sentiment.csv')
p.add_argument('--output-dir',default='output/live')
p.add_argument('--charts',action='store_true')
p.add_argument('--xlsx',action='store_true')
a=p.parse_args()
cfg=model_config(a.config)
fund=build_fundamental_model(read_csv(a.quarterly),read_csv(a.guidance),read_csv(a.scenarios),read_csv(a.universe),cfg)
opp=apply_sentiment_overlay(fund,read_csv(a.sentiment),cfg)
write_csv(a.output_dir+'/fundamental_model.csv',fund)
write_csv(a.output_dir+'/opportunity_ranking.csv',opp)
if a.charts: make_charts(a.output_dir,opp)
if a.xlsx: export_xlsx(a.output_dir+'/analysis.xlsx',fund,read_csv(a.sentiment),opp)
print(f'Built {len(opp)} companies into {a.output_dir}')
