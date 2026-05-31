import pandas as pd

from database.db import load_table, upsert_rows


def load_latest_macro(conn) -> pd.DataFrame:
    macro = load_table(conn, "macro_indicators")
    if macro.empty:
        return macro
    return macro.sort_values("date").groupby("indicator", as_index=False).tail(1).sort_values("indicator")


def load_latest_industry_kpis(conn) -> pd.DataFrame:
    kpis = load_table(conn, "industry_kpis")
    if kpis.empty:
        return kpis
    return kpis.sort_values("date").groupby(["industry", "kpi"], as_index=False).tail(1)


def save_industry_cycle_signals(conn, signals: pd.DataFrame) -> int:
    if signals.empty:
        return 0
    return upsert_rows(conn, "industry_cycle_signals", signals, ["date", "industry"])
