import pandas as pd


def calculate_value_trap_flags(
    financials: pd.DataFrame,
    prices: pd.DataFrame,
    receivables_inventory: pd.DataFrame = None,
    min_trading_value: float = 5_000_000_000,
) -> pd.DataFrame:
    latest = financials.sort_values(["year", "quarter"]).groupby("ticker").tail(1).copy()
    latest_price = prices.sort_values("date").groupby("ticker").tail(1)[["ticker", "trading_value"]]
    frame = latest[["ticker", "assets", "liabilities"]].merge(latest_price, on="ticker", how="left")

    op_loss = (
        financials.sort_values(["year", "quarter"])
        .groupby("ticker")
        .tail(3)
        .assign(op_loss=lambda x: x["operating_profit"].fillna(0) < 0)
        .groupby("ticker")["op_loss"]
        .sum()
        .rename("op_loss_count")
    )
    ocf_negative = (
        financials.sort_values(["year", "quarter"])
        .groupby("ticker")
        .tail(3)
        .assign(ocf_negative=lambda x: x["operating_cash_flow"].fillna(0) < 0)
        .groupby("ticker")["ocf_negative"]
        .sum()
        .rename("ocf_negative_count")
    )
    frame = frame.merge(op_loss, on="ticker", how="left").merge(ocf_negative, on="ticker", how="left")
    frame["debt_ratio"] = frame["liabilities"] / frame["assets"].replace(0, pd.NA)
    frame["receivables_warning"] = False
    frame["inventory_warning"] = False

    if receivables_inventory is not None and not receivables_inventory.empty:
        ri = receivables_inventory.copy()
        frame = frame.merge(ri[["ticker", "receivables_warning", "inventory_warning"]], on="ticker", how="left", suffixes=("", "_ri"))
        frame["receivables_warning"] = frame["receivables_warning_ri"].fillna(False)
        frame["inventory_warning"] = frame["inventory_warning_ri"].fillna(False)

    def flags(row):
        risk_flags = []
        if row.get("op_loss_count", 0) >= 3:
            risk_flags.append("최근 3개 기간 연속 영업적자")
        if row.get("ocf_negative_count", 0) >= 3:
            risk_flags.append("최근 3개 기간 연속 영업현금흐름 음수")
        debt_ratio = 0 if pd.isna(row.get("debt_ratio", 0)) else row.get("debt_ratio", 0)
        trading_value = 0 if pd.isna(row.get("trading_value", 0)) else row.get("trading_value", 0)
        if debt_ratio >= 3:
            risk_flags.append("부채비율 300% 이상")
        if row.get("receivables_warning", False):
            risk_flags.append("매출채권 증가율이 매출 증가율보다 과도")
        if row.get("inventory_warning", False):
            risk_flags.append("재고자산 급증")
        if trading_value < min_trading_value:
            risk_flags.append("거래대금 부족")
        risk_flags.append("관리종목/투자주의환기 여부: TODO")
        return risk_flags

    frame["risk_flags"] = frame.apply(flags, axis=1)
    frame["risk_score"] = frame["risk_flags"].map(lambda items: max(0, (len(items) - 1) * 12))
    frame["is_value_trap"] = frame["risk_score"] >= 24
    frame["risk_flags"] = frame["risk_flags"].map(lambda items: "; ".join(items))
    return frame[["ticker", "is_value_trap", "risk_flags", "risk_score"]]
