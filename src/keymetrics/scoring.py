from __future__ import annotations

from math import isfinite
from typing import Mapping, Iterable


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def linear_score(value: float | None, cheap: float, expensive: float) -> float | None:
    """100 at cheap anchor, 0 at expensive anchor, linearly clamped."""
    if value is None or not isfinite(value):
        return None
    if expensive <= cheap:
        raise ValueError("expensive anchor must exceed cheap anchor")
    return clamp((expensive - value) / (expensive - cheap) * 100.0, 0.0, 100.0)


def dynamic_weighted_average(values: Mapping[str, float | None], weights: Mapping[str, float], min_components: int = 1) -> float | None:
    present = [(k, v) for k, v in values.items() if v is not None and k in weights]
    if len(present) < min_components:
        return None
    denom = sum(weights[k] for k, _ in present)
    if denom <= 0:
        return None
    return sum(v * weights[k] for k, v in present) / denom


def earnings_quality_score(revenue_growth: float | None, operating_margin: float | None, fcf_margin: float | None, cfg: Mapping) -> float | None:
    def score(v: float | None, spec: Mapping) -> float | None:
        if v is None:
            return None
        return clamp(float(spec["intercept"]) + v * float(spec["slope"]), float(spec["min"]), float(spec["max"]))

    vals = {
        "revenue_growth": score(revenue_growth, cfg["revenue_score"]),
        "operating_margin": score(operating_margin, cfg["operating_margin_score"]),
        "fcf_margin": score(fcf_margin, cfg["fcf_margin_score"]),
    }
    return dynamic_weighted_average(vals, cfg["weights"], int(cfg.get("min_components", 2)))


def valuation_score(pe: float | None, p_fcf: float | None, p_s: float | None, cfg: Mapping) -> float | None:
    pe2 = pe
    if pe2 is not None and (pe2 <= 0 or pe2 > float(cfg.get("pe_exclude_above", 100.0))):
        pe2 = None
    pfcf2 = p_fcf if p_fcf is None or p_fcf > 0 else None
    ps2 = p_s if p_s is None or p_s > 0 else None
    vals = {
        "pe": linear_score(pe2, *map(float, cfg["anchors"]["pe"])),
        "p_fcf": linear_score(pfcf2, *map(float, cfg["anchors"]["p_fcf"])),
        "p_s": linear_score(ps2, *map(float, cfg["anchors"]["p_s"])),
    }
    return dynamic_weighted_average(vals, cfg["weights"], 1)


def latest_history_composite(latest: float | None, history_average: float | None, latest_weight: float = 0.70) -> float | None:
    if latest is None and history_average is None:
        return None
    if latest is None:
        return history_average
    if history_average is None:
        return latest
    return latest_weight * latest + (1.0 - latest_weight) * history_average


def scaled_return_score(value: float, lo: float, hi: float) -> float:
    if hi <= lo:
        raise ValueError("hi must exceed lo")
    return clamp((value - lo) / (hi - lo) * 100.0, 0.0, 100.0)


def scenario_score(bear_return: float, base_return: float, bull_return: float, cfg: Mapping) -> float:
    w = cfg["weights"]
    bear = scaled_return_score(bear_return, *map(float, cfg["bear_range"]))
    base = scaled_return_score(base_return, *map(float, cfg["base_range"]))
    bull = scaled_return_score(bull_return, *map(float, cfg["bull_range"]))
    return float(w["bear"]) * bear + float(w["base"]) * base + float(w["bull"]) * bull


def confidence_adjusted_guidance(credibility: float | None, confidence: str | None, confidence_factors: Mapping[str, float]) -> float | None:
    if credibility is None or confidence in (None, "", "N/A"):
        return None
    factor = confidence_factors.get(confidence)
    return None if factor is None else credibility * float(factor)


def integrated_fundamental_score(eq: float | None, valuation: float | None, guidance_adjusted: float | None, scenario: float | None, cfg: Mapping) -> float | None:
    weights = cfg["weights"]
    vals = {"eq": eq, "valuation": valuation, "guidance": guidance_adjusted, "scenario": scenario}
    present = [(k, v) for k, v in vals.items() if v is not None]
    if not present:
        return None
    if not cfg.get("reweight_missing", True):
        return sum(float(weights[k]) * v for k, v in present)
    denom = sum(float(weights[k]) for k, _ in present)
    return sum(float(weights[k]) * v for k, v in present) / denom


def rank_desc(rows: list[dict], key: str) -> list[dict]:
    ordered = sorted(rows, key=lambda r: (r.get(key) is not None, r.get(key) if r.get(key) is not None else float("-inf")), reverse=True)
    for i, row in enumerate(ordered, 1):
        row["Rank"] = i
    return ordered
