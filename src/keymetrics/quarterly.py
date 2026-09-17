from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Iterable, Mapping, Any

from .io import as_float
from .scoring import earnings_quality_score, valuation_score, latest_history_composite


def score_quarterly_rows(rows: Iterable[dict[str, Any]], eq_cfg: Mapping, valuation_cfg: Mapping) -> list[dict[str, Any]]:
    out=[]
    for r in rows:
        x=dict(r)
        rg=as_float(r.get("revenue_growth"))
        om=as_float(r.get("operating_margin"))
        fm=as_float(r.get("fcf_margin"))
        pe=as_float(r.get("pe")); pfcf=as_float(r.get("p_fcf")); ps=as_float(r.get("p_s"))
        x["eq_score"]=earnings_quality_score(rg,om,fm,eq_cfg)
        x["valuation_score"]=valuation_score(pe,pfcf,ps,valuation_cfg)
        out.append(x)
    return out


def company_quarterly_composites(rows: Iterable[dict[str, Any]], eq_cfg: Mapping, valuation_cfg: Mapping) -> dict[str, dict[str, float|None]]:
    scored=score_quarterly_rows(rows,eq_cfg,valuation_cfg)
    by=defaultdict(list)
    for r in scored:
        by[r["ticker"]].append(r)
    out={}
    for ticker,items in by.items():
        items=sorted(items,key=lambda x:str(x.get("period","")))
        eqs=[x["eq_score"] for x in items if x["eq_score"] is not None]
        vals=[x["valuation_score"] for x in items if x["valuation_score"] is not None]
        latest_eq=eqs[-1] if eqs else None
        latest_val=vals[-1] if vals else None
        avg_eq=mean(eqs) if eqs else None
        avg_val=mean(vals) if vals else None
        out[ticker]={
            "latest_eq":latest_eq,
            "history_avg_eq":avg_eq,
            "eq_composite":latest_history_composite(latest_eq,avg_eq,float(eq_cfg.get("composite_latest_weight",0.70))),
            "latest_valuation":latest_val,
            "history_avg_valuation":avg_val,
            "valuation_composite":latest_history_composite(latest_val,avg_val,float(valuation_cfg.get("composite_latest_weight",0.70))),
            "eq_observations":len(eqs),
            "valuation_observations":len(vals),
        }
    return out
