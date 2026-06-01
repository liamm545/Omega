from __future__ import annotations

import pandas as pd


def calculate_sector_market_scores(stocks: pd.DataFrame, scores: pd.DataFrame, sector_name: str) -> dict:
    if scores is None or scores.empty:
        return {"momentum_score": 0.0, "event_score": 0.0, "stock_count": 0, "overheating": 0.0}
    frame = scores[scores.get("intelligence_sector", scores.get("sector", "")).eq(sector_name)]
    if frame.empty:
        return {"momentum_score": 0.0, "event_score": 0.0, "stock_count": 0, "overheating": 0.0}
    momentum = float(frame.get("momentum_score", pd.Series([0])).mean())
    event = float(frame.get("event_score", pd.Series([0])).mean())
    overheat = _overheating(frame)
    return {"momentum_score": momentum, "event_score": event, "stock_count": len(frame), "overheating": overheat}


def _overheating(frame: pd.DataFrame) -> float:
    if "return_1d" in frame.columns:
        hot = (pd.to_numeric(frame["return_1d"], errors="coerce").fillna(0) >= 10).sum()
        return float(hot * 5)
    if "momentum_score" in frame.columns:
        return float((pd.to_numeric(frame["momentum_score"], errors="coerce").fillna(0) >= 85).sum() * 3)
    return 0.0
