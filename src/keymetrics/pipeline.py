from __future__ import annotations

from typing import Any, Mapping

from .io import as_float, as_int
from .scoring import scenario_score, confidence_adjusted_guidance, integrated_fundamental_score
from .sentiment import raw_sentiment, adjusted_sentiment, opportunity_score, quadrant


def rebuild_fundamental_snapshot(rows: list[dict[str, Any]], cfg: Mapping) -> list[dict[str, Any]]:
    """Recalculate score-bearing fields in the saved fundamental snapshot.

    The snapshot contains market/fundamental scenario values and component inputs.
    This function intentionally recalculates hybrid returns, scenario score, guidance
    adjustment and integrated score instead of trusting the saved outputs.
    """
    out=[]
    for r in rows:
        x=dict(r)
        price=as_float(r.get("Current Price"))
        mw=as_float(r.get("Market Wt")) or 0.0
        fw=as_float(r.get("Fundamental Wt")) or 0.0
        hybrid={}
        for case,title in (("bear","Bear"),("base","Base"),("bull","Bull")):
            m=as_float(r.get(f"Market {title}")); f=as_float(r.get(f"Fundamental {title}"))
            if m is None and f is None: v=None
            elif m is None: v=f
            elif f is None: v=m
            else: v=mw*m+fw*f
            hybrid[case]=v
            x[f"Hybrid {title}"]=v
        if price is None or price<=0 or any(hybrid[k] is None for k in ("bear","base","bull")):
            br=ba=bu=None; ss=None
        else:
            br=hybrid["bear"]/price-1.0; ba=hybrid["base"]/price-1.0; bu=hybrid["bull"]/price-1.0
            ss=scenario_score(br,ba,bu,cfg["scenario_score"])
        x["Bear %"]=br; x["Base %"]=ba; x["Bull %"]=bu; x["Scenario Score"]=ss
        cred=as_float(r.get("Guidance Credibility")); conf=r.get("Guidance Confidence")
        gadj=confidence_adjusted_guidance(cred,conf,cfg["guidance"]["confidence_factors"])
        x["Conf-Adj Guidance"]=gadj
        eq=as_float(r.get("EQ Composite")); val=as_float(r.get("Valuation Composite"))
        fund=integrated_fundamental_score(eq,val,gadj,ss,cfg["fundamental_integrated"])
        x["Fundamental Integrated"]=fund
        out.append(x)
    return out


def apply_sentiment_overlay(fundamental_rows: list[dict[str, Any]], sentiment_rows: list[dict[str, Any]], cfg: Mapping) -> list[dict[str, Any]]:
    sent_by={r["Ticker"]:r for r in sentiment_rows}
    out=[]
    for f in fundamental_rows:
        t=f["Ticker"]
        s=sent_by.get(t)
        if s is None:
            raise KeyError(f"Missing sentiment row for {t}")
        d7=as_float(s.get("7D") or s.get("7D Sentiment")); d30=as_float(s.get("30D") or s.get("30D Sentiment")); d90=as_float(s.get("90D") or s.get("90D Sentiment"))
        if None in (d7,d30,d90):
            raise ValueError(f"Missing sentiment window score for {t}")
        confidence=s.get("Confidence") or s.get("News Confidence") or "Low"
        materiality=s.get("Materiality") or "Minor"
        raw=raw_sentiment(d7,d30,d90,cfg["sentiment"])
        adj=adjusted_sentiment(raw,confidence,cfg["sentiment"])
        fund=as_float(f.get("Fundamental Integrated"))
        if fund is None:
            raise ValueError(f"Missing Fundamental Integrated score for {t}")
        opportunity,overlay=opportunity_score(fund,adj,materiality,cfg["sentiment"])
        x={
            "Universe":f.get("Universe"),"Ticker":t,"Company":f.get("Company"),"Coverage":f.get("Coverage"),
            "Fundamental Integrated Score":fund,
            "Adjusted News Sentiment":adj,
            "Materiality":materiality,
            "Materiality Factor":cfg["sentiment"]["materiality_factors"][materiality],
            "Sentiment Overlay":overlay,
            "Opportunity Score":opportunity,
            "Sentiment Momentum":d7-d30,
            "Catalyst Risk":as_float(s.get("Catalyst Risk")),
            "Quadrant":quadrant(fund,adj,cfg["sentiment"]),
            "Bear Return":as_float(f.get("Bear %")),"Base Return":as_float(f.get("Base %")),"Bull Return":as_float(f.get("Bull %")),
            "Guidance Credibility":as_float(f.get("Guidance Credibility")),"Confidence":f.get("Guidance Confidence"),
            "Scenario Score":as_float(f.get("Scenario Score")),
            "Key News":s.get("Key News / Catalyst") or s.get("Key News") or "",
            "Primary Source":s.get("Primary Source") or s.get("Primary Source URL") or "",
            "Secondary Source":s.get("Secondary / Risk Source") or s.get("Secondary Source") or "",
        }
        out.append(x)
    out.sort(key=lambda r:r["Opportunity Score"],reverse=True)
    for i,r in enumerate(out,1): r["Opportunity Rank"]=i
    return out
