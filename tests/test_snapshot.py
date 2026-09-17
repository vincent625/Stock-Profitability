from pathlib import Path

from keymetrics.config import model_config
from keymetrics.io import read_csv
from keymetrics.pipeline import rebuild_fundamental_snapshot, apply_sentiment_overlay

ROOT=Path(__file__).resolve().parents[1]


def test_current_45_company_snapshot_matches_saved_output():
    cfg=model_config(ROOT/'config/model.yaml')
    fundamental=rebuild_fundamental_snapshot(read_csv(ROOT/'data/snapshots/2026-09-01/fundamental_model.csv'),cfg)
    actual=apply_sentiment_overlay(fundamental,read_csv(ROOT/'data/snapshots/2026-09-01/news_sentiment.csv'),cfg)
    expected={r['Ticker']:r for r in read_csv(ROOT/'data/snapshots/2026-09-01/opportunity_ranking_expected.csv')}
    assert len(actual)==45
    for r in actual:
        e=expected[r['Ticker']]
        assert abs(r['Opportunity Score']-float(e['Opportunity Score']))<1e-8
        assert abs(r['Fundamental Integrated Score']-float(e['Fundamental Integrated Score']))<1e-8
        assert abs(r['Adjusted News Sentiment']-float(e['Adjusted News Sentiment']))<1e-8


def test_regn_snapshot_formula():
    cfg=model_config(ROOT/'config/model.yaml')
    fundamental=rebuild_fundamental_snapshot(read_csv(ROOT/'data/snapshots/2026-09-01/fundamental_model.csv'),cfg)
    actual=apply_sentiment_overlay(fundamental,read_csv(ROOT/'data/snapshots/2026-09-01/news_sentiment.csv'),cfg)
    regn=next(x for x in actual if x['Ticker']=='REGN')
    assert abs(regn['Sentiment Overlay']-.98)<1e-12
    assert abs(regn['Opportunity Score']-70.59905624260054)<1e-10
