from __future__ import annotations

from typing import Any, Mapping

from .io import as_float
from .quarterly import company_quarterly_composites
from .scoring import confidence_adjusted_guidance, scenario_score, integrated_fundamental_score
from .valuation import hybrid_values


def build_fundamental_model(
    quarterly_rows: list[dict[str,Any]],
    guidance_rows: list[dict[str,Any]],
    scenario_rows: list[dict[str,Any]],
    universe_rows: list[dict[str,Any]],
    cfg: Mapping,
) -> list[dict[str,Any]]:
    """Build company-level fundamentals from normalized inputs.

    `scenario_rows` are deliberately explicit. For QQQ they can be generated with
    `build_qqq_scenarios.py`; healthcare can use company-specific normalized
    earnings/FCF/SOTP/revenue scenario values.
    """
    comps=company_quarterly_composites(quarterly_rows,cfg['eq'],cfg['valuation'])
    guidance={r['ticker']:r for r in guidance_rows}
    scenarios={r['ticker']:r for r in scenario_rows}
    out=[]
    for u in universe_rows:
        t=u['ticker']
        if t not in comps:
            continue
        if t not in scenarios:
            raise KeyError(f'Missing scenario input for {t}')
        c=comps[t]; g=guidance.get(t,{}); s=scenarios[t]
        price=as_float(s.get('current_price'))
        market={k:as_float(s.get(f'market_{k}')) for k in ('bear','base','bull')}
        fundamental={k:as_float(s.get(f'fundamental_{k}')) for k in ('bear','base','bull')}
        mw=as_float(s.get('market_weight')) or 0.0; fw=as_float(s.get('fundamental_weight')) or 0.0
        hybrid=hybrid_values(market,fundamental,mw,fw)
        if price is None or any(hybrid[k] is None for k in hybrid):
            br=ba=bu=ss=None
        else:
            br=hybrid['bear']/price-1; ba=hybrid['base']/price-1; bu=hybrid['bull']/price-1
            ss=scenario_score(br,ba,bu,cfg['scenario_score'])
        cred=as_float(g.get('credibility'))
        conf=g.get('confidence') or 'N/A'
        gadj=confidence_adjusted_guidance(cred,conf,cfg['guidance']['confidence_factors'])
        integrated=integrated_fundamental_score(c['eq_composite'],c['valuation_composite'],gadj,ss,cfg['fundamental_integrated'])
        out.append({
            'Universe':u['universe'],'Ticker':t,'Company':u['company'],'Coverage':s.get('coverage',''),
            'EQ Composite':c['eq_composite'],'Valuation Composite':c['valuation_composite'],
            'Guidance Credibility':cred,'Guidance Confidence':conf,'Guidance Obs':g.get('observations'),
            'Conf-Adj Guidance':gadj,'Current Price':price,
            'Market Bear':market['bear'],'Market Base':market['base'],'Market Bull':market['bull'],
            'Fundamental Bear':fundamental['bear'],'Fundamental Base':fundamental['base'],'Fundamental Bull':fundamental['bull'],
            'Market Wt':mw,'Fundamental Wt':fw,
            'Hybrid Bear':hybrid['bear'],'Hybrid Base':hybrid['base'],'Hybrid Bull':hybrid['bull'],
            'Bear %':br,'Base %':ba,'Bull %':bu,'Scenario Score':ss,'Fundamental Integrated':integrated,
            'Market Method':s.get('market_method',''),'Fundamental Method':s.get('fundamental_method',''),'Scenario Mix':s.get('scenario_mix',''),
        })
    return out
