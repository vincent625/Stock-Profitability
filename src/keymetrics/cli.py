from __future__ import annotations

import argparse
from pathlib import Path

from .config import model_config
from .io import read_csv, write_csv
from .pipeline import rebuild_fundamental_snapshot, apply_sentiment_overlay
from .reporting import export_core_csvs, make_charts, export_xlsx


def build_snapshot(args: argparse.Namespace) -> int:
    cfg=model_config(args.config)
    fundamental=rebuild_fundamental_snapshot(read_csv(args.fundamental),cfg)
    sentiment=read_csv(args.sentiment)
    opportunity=apply_sentiment_overlay(fundamental,sentiment,cfg)
    export_core_csvs(args.output,fundamental,opportunity)
    if args.charts:
        make_charts(args.output,opportunity)
    if args.xlsx:
        export_xlsx(Path(args.output)/'analysis.xlsx',fundamental,sentiment,opportunity)
    print(f"Wrote {len(opportunity)} companies to {args.output}")
    return 0


def validate_snapshot(args: argparse.Namespace) -> int:
    cfg=model_config(args.config)
    fundamental=rebuild_fundamental_snapshot(read_csv(args.fundamental),cfg)
    opportunity=apply_sentiment_overlay(fundamental,read_csv(args.sentiment),cfg)
    expected={r['Ticker']:r for r in read_csv(args.expected)}
    failures=[]
    for r in opportunity:
        e=expected.get(r['Ticker'])
        if not e:
            failures.append(f"{r['Ticker']}: missing expected row"); continue
        exp=float(e['Opportunity Score'])
        delta=abs(r['Opportunity Score']-exp)
        if delta>args.tolerance:
            failures.append(f"{r['Ticker']}: {r['Opportunity Score']:.10f} vs {exp:.10f} (delta {delta:.3g})")
    if failures:
        print("Snapshot validation FAILED")
        print("\n".join(failures[:20]))
        return 1
    print(f"Snapshot validation passed for {len(opportunity)} companies (tol={args.tolerance}).")
    return 0


def fetch_quarterly(args: argparse.Namespace) -> int:
    from .data_sources.yfinance_source import fetch_quarterly_panel
    universe=read_csv(args.universe)
    rows=[]
    for u in universe:
        if u.get('data_mode')=='manual' or not u.get('market_ticker'):
            print(f"skip {u['ticker']}: manual data")
            continue
        print(f"fetch {u['ticker']} ({u['market_ticker']})")
        try:
            rr=fetch_quarterly_panel(u['market_ticker'],args.quarters)
            for x in rr:
                x['ticker']=u['ticker']; x['company']=u['company']; x['universe']=u['universe']
            rows.extend(rr)
        except Exception as e:
            print(f"WARN {u['ticker']}: {e}")
    write_csv(args.output,rows,fieldnames=['universe','ticker','company','period','revenue_growth','operating_margin','fcf_margin','pe','p_fcf','p_s','price'])
    print(f"Wrote {len(rows)} quarterly rows to {args.output}")
    return 0


def parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog='keymetrics',description='Key Metrics for Profitability research model')
    sub=p.add_subparsers(dest='command',required=True)
    common={'config':('config/model.yaml','Model configuration YAML')}
    b=sub.add_parser('snapshot',help='Rebuild the saved 45-company snapshot')
    b.add_argument('--config',default='config/model.yaml')
    b.add_argument('--fundamental',default='data/snapshots/2026-09-01/fundamental_model.csv')
    b.add_argument('--sentiment',default='data/snapshots/2026-09-01/news_sentiment.csv')
    b.add_argument('--output',default='output/snapshot')
    b.add_argument('--charts',action='store_true')
    b.add_argument('--xlsx',action='store_true')
    b.set_defaults(func=build_snapshot)

    v=sub.add_parser('validate-snapshot',help='Regression-test the current saved model')
    v.add_argument('--config',default='config/model.yaml')
    v.add_argument('--fundamental',default='data/snapshots/2026-09-01/fundamental_model.csv')
    v.add_argument('--sentiment',default='data/snapshots/2026-09-01/news_sentiment.csv')
    v.add_argument('--expected',default='data/snapshots/2026-09-01/opportunity_ranking_expected.csv')
    v.add_argument('--tolerance',type=float,default=1e-8)
    v.set_defaults(func=validate_snapshot)

    f=sub.add_parser('fetch-quarterly',help='Best-effort public quarterly fundamentals via yfinance')
    f.add_argument('--universe',default='config/universe.csv')
    f.add_argument('--quarters',type=int,default=20)
    f.add_argument('--output',default='data/live/quarterly_financials.csv')
    f.set_defaults(func=fetch_quarterly)
    return p


def main() -> int:
    args=parser().parse_args()
    return args.func(args)


if __name__=='__main__':
    raise SystemExit(main())
