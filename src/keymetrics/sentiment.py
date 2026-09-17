from __future__ import annotations

from typing import Mapping

from .scoring import clamp


def raw_sentiment(d7: float, d30: float, d90: float, cfg: Mapping) -> float:
    w=cfg["window_weights"]
    return float(w["d7"])*d7 + float(w["d30"])*d30 + float(w["d90"])*d90


def adjusted_sentiment(raw: float, confidence: str, cfg: Mapping) -> float:
    neutral=float(cfg.get("neutral_score",50.0))
    factor=float(cfg["confidence_factors"][confidence])
    return neutral+(raw-neutral)*factor


def centered_overlay(adjusted: float, materiality: str, cfg: Mapping) -> float:
    neutral=float(cfg.get("neutral_score",50.0))
    coeff=float(cfg.get("overlay_coefficient",0.05))
    factor=float(cfg["materiality_factors"][materiality])
    cap=float(cfg.get("overlay_cap_points",2.5))
    return clamp(coeff*(adjusted-neutral)*factor,-cap,cap)


def opportunity_score(fundamental_score: float, adjusted: float, materiality: str, cfg: Mapping) -> tuple[float,float]:
    overlay=centered_overlay(adjusted,materiality,cfg)
    return fundamental_score+overlay,overlay


def quadrant(fundamental: float, adjusted: float, cfg: Mapping) -> str:
    q=cfg["quadrant"]
    if fundamental>=float(q["fundamental_high"]) and adjusted>=float(q["sentiment_high"]):
        return "High Fundamentals / Positive Catalyst"
    if fundamental>=float(q["fundamental_high"]) and adjusted<=float(q["sentiment_low"]):
        return "High Fundamentals / Negative Catalyst"
    if fundamental<float(q["fundamental_low"]) and adjusted>=float(q["sentiment_high"]):
        return "Momentum / Weak Fundamentals"
    if fundamental<float(q["fundamental_low"]) and adjusted<=float(q["sentiment_low"]):
        return "Weak Fundamentals / Negative Sentiment"
    return "Neutral / Watch"
