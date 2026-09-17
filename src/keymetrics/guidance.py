from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .scoring import clamp


@dataclass(frozen=True)
class GuidanceObservation:
    ticker: str
    period: str
    metric: str
    metric_kind: str  # "absolute" or "growth_pp"
    guide_low: float | None
    guide_high: float | None
    guide_mid: float
    actual: float
    include: bool = True
    notes: str = ""
    source: str = ""

    @property
    def range_hit(self) -> int | None:
        if self.guide_low is None or self.guide_high is None:
            return None
        return int(self.guide_low <= self.actual <= self.guide_high)

    @property
    def absolute_error(self) -> float:
        if self.metric_kind == "growth_pp":
            return abs(self.actual - self.guide_mid)
        if self.guide_mid == 0:
            raise ZeroDivisionError("guide_mid is zero for absolute guidance metric")
        return abs(self.actual / self.guide_mid - 1.0)

    @property
    def signed_error(self) -> float:
        if self.metric_kind == "growth_pp":
            return self.actual - self.guide_mid
        if self.guide_mid == 0:
            raise ZeroDivisionError("guide_mid is zero for absolute guidance metric")
        return self.actual / self.guide_mid - 1.0


def banded_accuracy_score(error: float, metric_kind: str) -> float:
    """Healthcare annual guidance scoring used by the project."""
    if metric_kind == "growth_pp":
        # error is in percentage points, e.g. 0.7 means 0.7pp.
        bands = [(0.5,100),(1.0,90),(1.5,80),(2.5,70),(4.0,55),(6.0,35),(10.0,15)]
    else:
        # error is decimal fraction, e.g. 0.02 = 2%.
        bands = [(0.01,100),(0.02,90),(0.03,80),(0.05,70),(0.08,55),(0.12,35),(0.20,15)]
    for threshold, score in bands:
        if error <= threshold + 1e-12:
            return float(score)
    return 0.0


def linear_accuracy_score(error_fraction: float, zero_at: float = 0.10) -> float:
    """QQQ recurring guidance method: accuracy declines linearly to 0 at 10% error."""
    return clamp((1.0 - error_fraction / zero_at) * 100.0, 0.0, 100.0)


def observation_score(obs: GuidanceObservation, method: str = "banded", range_weight: float = 0.20) -> float:
    err = obs.absolute_error
    if method == "banded":
        accuracy = banded_accuracy_score(err, obs.metric_kind)
    elif method == "linear":
        if obs.metric_kind == "growth_pp":
            # For a growth-point metric, use 10 percentage points as the zero-accuracy anchor.
            accuracy = clamp((1.0 - err / 10.0) * 100.0, 0.0, 100.0)
        else:
            accuracy = linear_accuracy_score(err)
    else:
        raise ValueError(f"Unknown guidance method: {method}")
    hit = obs.range_hit
    if hit is None:
        return accuracy
    return (1.0 - range_weight) * accuracy + range_weight * 100.0 * hit


def evidence_factor(n: int, mapping: Mapping) -> float:
    if n <= 0:
        return 0.0
    max_key = max(int(k) for k in mapping)
    key = min(n, max_key)
    return float(mapping.get(key, mapping.get(str(key))))


def confidence_label(n: int) -> str:
    if n >= 5:
        return "High"
    if n == 4:
        return "High/Medium"
    if n == 3:
        return "Medium"
    if n == 2:
        return "Medium/Low"
    if n == 1:
        return "Low"
    return "N/A"


def credibility(observations: Iterable[GuidanceObservation], method: str, evidence_map: Mapping, range_weight: float = 0.20) -> dict:
    included = [o for o in observations if o.include]
    if not included:
        return {"observations":0,"average_observation_score":None,"evidence_factor":0.0,"credibility":None,"confidence":"N/A","avg_abs_error":None,"avg_bias":None,"range_hit_rate":None}
    scores = [observation_score(o, method=method, range_weight=range_weight) for o in included]
    ef = evidence_factor(len(included), evidence_map)
    hits = [o.range_hit for o in included if o.range_hit is not None]
    return {
        "observations": len(included),
        "average_observation_score": sum(scores)/len(scores),
        "evidence_factor": ef,
        "credibility": sum(scores)/len(scores) * ef,
        "confidence": confidence_label(len(included)),
        "avg_abs_error": sum(o.absolute_error for o in included)/len(included),
        "avg_bias": sum(o.signed_error for o in included)/len(included),
        "range_hit_rate": (sum(hits)/len(hits)) if hits else None,
    }
