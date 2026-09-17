#!/usr/bin/env python3
"""Build standardized QQQ market-multiple + normalized-FCF DCF scenarios."""
import argparse
from keymetrics.config import model_config
from keymetrics.io import read_csv, write_csv, as_float
from keymetrics.valuation import market_multiple_scenario, qqq_fundamental_dcf


def series(s):
    if not s:return []
    return [float(x) for x in str(s).split(';') if x.strip()]

p=argparse.ArgumentParser()
p.add_argument('--input',default='data/templates/qqq_scenario_inputs.csv')
p.add_argument('--config',default='config/model.yaml')
p.add_argument('--output',default='data/live/qqq_scenarios.csv')
a=p.parse_args(); cfg=model_config(a.config)
out=[]
for r in read_csv(a.input):
    price=as_float(r.get('current_price')); fpe=as_float(r.get('current_forward_pe')); ps=as_float(r.get('latest_ps')); latest_rg=as_float(r.get('latest_revenue_growth'))
    if None in (price,fpe,ps,latest_rg): continue
    market=market_multiple_scenario(price,fpe,series(r.get('forward_pe_history')),cfg['qqq_market_scenario'])
    fund=qqq_fundamental_dcf(price,ps,series(r.get('fcf_margins')),latest_rg,series(r.get('recent_revenue_growths')),cfg['qqq_dcf'])
    mw=as_float(r.get('market_weight')) or .5; fw=as_float(r.get('fundamental_weight')) or .5
    out.append({'universe':'QQQ','ticker':r['ticker'],'current_price':price,
        'market_bear':market['bear'],'market_base':market['base'],'market_bull':market['bull'],
        'fundamental_bear':fund['bear'],'fundamental_base':fund['base'],'fundamental_bull':fund['bull'],
        'market_weight':mw,'fundamental_weight':fw,'coverage':r.get('coverage','A'),
        'market_method':'Forward EPS × own historical forward-P/E bands','fundamental_method':'5Y normalized-FCF DCF','scenario_mix':f'Hybrid {mw:.0%}/{fw:.0%}'})
fields=['universe','ticker','current_price','market_bear','market_base','market_bull','fundamental_bear','fundamental_base','fundamental_bull','market_weight','fundamental_weight','coverage','market_method','fundamental_method','scenario_mix']
write_csv(a.output,out,fieldnames=fields); print(f'Wrote {a.output}')
