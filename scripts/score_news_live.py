#!/usr/bin/env python3
"""Fetch GDELT news, score titles with FinBERT, aggregate 7D/30D/90D sentiment.

This is an automation aid, not a replacement for review of materiality/catalyst risk.
Use `news_overrides.csv` to replace heuristic classifications when necessary.
"""
import argparse
from keymetrics.io import read_csv, write_csv
from keymetrics.data_sources.gdelt_news import fetch_articles, finbert_title_scores
from keymetrics.news_model import aggregate_news

p=argparse.ArgumentParser()
p.add_argument('--universe',default='config/universe.csv')
p.add_argument('--output',default='data/live/news_sentiment.csv')
p.add_argument('--days',type=int,default=90)
a=p.parse_args(); out=[]
for u in read_csv(a.universe):
    print('news',u['ticker'],u['company'])
    try:
        articles=fetch_articles(u['company'],days=a.days)
        scored=finbert_title_scores(articles)
        agg=aggregate_news(scored)
        out.append({'Ticker':u['ticker'],'Company':u['company'],**agg})
    except Exception as e:
        print('WARN',u['ticker'],e)
write_csv(a.output,out); print(f'Wrote {a.output}')
