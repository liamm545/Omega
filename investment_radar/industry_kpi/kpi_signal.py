from __future__ import annotations

import pandas as pd

from industry_kpi.kpi_registry import get_sector_kpis


def normalize_kpi_frame(kpis: pd.DataFrame) -> pd.DataFrame:
    if kpis is None or kpis.empty:
        return pd.DataFrame(columns=_columns())
    frame = kpis.copy()
    if "sector" not in frame.columns:
        frame["sector"] = frame.get("industry", "missing")
    if "kpi_name" not in frame.columns:
        frame["kpi_name"] = frame.get("kpi", "missing")
    if "source_url" not in frame.columns:
        frame["source_url"] = frame.get("evidence_url", "")
    if "mom_change" not in frame.columns:
        frame["mom_change"] = frame.get("change_1m", pd.NA)
    if "trend_3m" not in frame.columns:
        frame["trend_3m"] = frame.get("change_3m", pd.NA)
    if "trend_6m" not in frame.columns:
        frame["trend_6m"] = pd.NA
    if "yoy_change" not in frame.columns:
        frame["yoy_change"] = pd.NA
    for column in _columns():
        if column not in frame.columns:
            frame[column] = pd.NA
    return frame[_columns()]


def latest_kpi_status(kpis: pd.DataFrame, sector: str) -> list[dict]:
    frame = normalize_kpi_frame(kpis)
    latest = _latest(frame[frame["sector"].eq(sector)], ["sector", "kpi_name"])
    rows = []
    for name in get_sector_kpis(sector):
        matched = latest[latest["kpi_name"].eq(name)]
        if matched.empty:
            rows.append({"kpi_name": name, "status": "missing", "value": "missing", "source_url": ""})
        else:
            item = matched.iloc[0].to_dict()
            item["status"] = _signal_from_row(item)
            rows.append(item)
    return rows


def sector_kpi_signal_score(kpis: pd.DataFrame, sector: str) -> tuple[float, list[str], list[str]]:
    rows = latest_kpi_status(kpis, sector)
    positives = []
    negatives = []
    scored = []
    for row in rows:
        if row.get("status") == "missing":
            continue
        signal = _numeric_signal(row)
        scored.append(signal)
        label = f"{row.get('kpi_name')}={_fmt(row.get('value'))}{row.get('unit') or ''}"
        if signal > 0:
            positives.append(label)
        elif signal < 0:
            negatives.append(label)
    if not scored:
        return 0.0, positives, negatives
    return max(min(50 + sum(scored) / len(scored) * 50, 100), 0), positives, negatives


def _signal_from_row(row: dict) -> str:
    signal = _numeric_signal(row)
    if signal > 0.15:
        return "positive"
    if signal < -0.15:
        return "negative"
    return "neutral"


def _numeric_signal(row: dict) -> float:
    values = []
    for key in ["yoy_change", "mom_change", "trend_3m", "trend_6m"]:
        value = pd.to_numeric(row.get(key), errors="coerce")
        if pd.notna(value):
            values.append(float(value))
    if not values:
        value = pd.to_numeric(row.get("value"), errors="coerce")
        if pd.notna(value):
            values.append(float(value))
    if not values:
        return 0.0
    avg = sum(values) / len(values)
    return max(min(avg / 30, 1), -1)


def _latest(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if frame.empty:
        return frame
    return frame.sort_values("date").groupby(keys, as_index=False).tail(1)


def _fmt(value) -> str:
    value = pd.to_numeric(value, errors="coerce")
    return "missing" if pd.isna(value) else f"{value:g}"


def _columns() -> list[str]:
    return ["date", "sector", "kpi_name", "value", "unit", "yoy_change", "mom_change", "trend_3m", "trend_6m", "source", "source_url", "updated_at"]
