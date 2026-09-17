from __future__ import annotations

import math
from statistics import median
from typing import Sequence, Mapping

from .scoring import clamp


def percentile(values: Sequence[float], p: float) -> float:
    vals = sorted(float(v) for v in values)
    if not vals:
        raise ValueError("percentile requires at least one value")
    if len(vals) == 1:
        return vals[0]
    k = (len(vals) - 1) * p
    lo = math.floor(k); hi = math.ceil(k)
    if lo == hi:
        return vals[lo]
    return vals[lo] + (vals[hi] - vals[lo]) * (k - lo)


def market_multiple_scenario(current_price: float, current_forward_pe: float, forward_pe_history: Sequence[float], cfg: Mapping) -> dict[str, float]:
    if current_price <= 0 or current_forward_pe <= 0:
        raise ValueError("current price and forward P/E must be positive")
    cap = float(cfg.get("forward_pe_history_cap", 150.0))
    hist = [float(x) for x in forward_pe_history if x and 0 < float(x) <= cap]
    implied_eps = current_price / current_forward_pe
    factors = cfg["eps_factors"]
    if len(hist) >= int(cfg.get("min_forward_pe_observations", 5)):
        target = {"bear": percentile(hist,0.25), "base": percentile(hist,0.50), "bull": percentile(hist,0.75)}
    else:
        fm = cfg["fallback_multiple_factors"]
        target = {k: current_forward_pe * float(fm[k]) for k in ("bear","base","bull")}
    return {k: implied_eps * float(factors[k]) * target[k] for k in ("bear","base","bull")}


def dcf_5y(fcf0: float, start_growth: float, terminal_year_growth: float, discount_rate: float, terminal_growth: float, years: int = 5) -> float:
    if fcf0 <= 0:
        raise ValueError("fcf0 must be positive")
    if discount_rate <= terminal_growth:
        raise ValueError("discount rate must exceed terminal growth")
    fcf = fcf0
    pv = 0.0
    for year in range(1, years+1):
        frac = (year-1)/(years-1) if years > 1 else 1.0
        g = start_growth + (terminal_year_growth-start_growth)*frac
        fcf *= 1.0 + g
        pv += fcf / (1.0 + discount_rate)**year
    terminal = fcf * (1.0 + terminal_growth)/(discount_rate-terminal_growth)
    pv += terminal / (1.0 + discount_rate)**years
    return pv


def qqq_fundamental_dcf(current_price: float, latest_ps: float, fcf_margins: Sequence[float], latest_revenue_growth: float, recent_revenue_growths: Sequence[float], cfg: Mapping) -> dict[str, float]:
    positive_margins = [float(x) for x in fcf_margins if x is not None and float(x) > 0]
    if not positive_margins or latest_ps <= 0 or current_price <= 0:
        return {"bear":None,"base":None,"bull":None}
    norm_margin = median(positive_margins)
    sales_per_share = current_price/latest_ps
    fcf_per_share = sales_per_share * norm_margin
    ga = cfg["growth_anchor"]
    recent = [float(x) for x in recent_revenue_growths if x is not None]
    med8 = median(recent[-8:] if len(recent)>8 else recent) if recent else latest_revenue_growth
    anchor = clamp(float(ga["latest_weight"])*latest_revenue_growth + float(ga["median8_weight"])*med8, float(ga["min"]), float(ga["max"]))
    out={}
    for case in ("bear","base","bull"):
        c=cfg[case]
        start=clamp(anchor+float(c["start_delta"]),float(c["start_min"]),float(c["start_max"]))
        out[case]=dcf_5y(fcf_per_share,start,float(c["terminal_year_growth"]),float(c["discount_rate"]),float(c["terminal_growth"]),int(cfg.get("years",5)))
    return out


def hybrid_values(market: Mapping[str,float|None], fundamental: Mapping[str,float|None], market_weight: float, fundamental_weight: float) -> dict[str,float|None]:
    out={}
    for case in ("bear","base","bull"):
        m=market.get(case); f=fundamental.get(case)
        if m is None and f is None: out[case]=None
        elif m is None: out[case]=f
        elif f is None: out[case]=m
        else: out[case]=market_weight*m+fundamental_weight*f
    return out
