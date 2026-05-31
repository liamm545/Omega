import pandas as pd


RELATION_MULTIPLIER = {
    "DIRECT": 1.0,
    "SUPPLY_CHAIN": 0.82,
    "SECTOR_THEME": 0.62,
    "SPECULATIVE": 0.35,
}

RELATION_DIRECTNESS = {
    "DIRECT": 30,
    "SUPPLY_CHAIN": 22,
    "SECTOR_THEME": 15,
    "SPECULATIVE": 7,
}

EARNINGS_LINK = {
    "DIRECT": 18,
    "SUPPLY_CHAIN": 14,
    "SECTOR_THEME": 9,
    "SPECULATIVE": 4,
}


def calculate_event_score(events: pd.DataFrame, event_stock_map: pd.DataFrame) -> pd.DataFrame:
    if event_stock_map.empty:
        return pd.DataFrame(columns=["ticker", "event_score"])

    frame = event_stock_map.merge(events[["event_id", "confidence_score"]], on="event_id", how="left")
    frame["source_reliability"] = frame["confidence_score"].fillna(0).clip(0, 100) * 0.30
    frame["relation_directness"] = frame["relation_type"].map(RELATION_DIRECTNESS).fillna(5)
    frame["earnings_link_probability_score"] = frame["relation_type"].map(EARNINGS_LINK).fillna(3)
    frame["market_reaction"] = (frame["relation_strength"].fillna(0).clip(0, 100) / 10).clip(0, 10)
    frame["follow_up_news"] = frame["relation_type"].isin(["DIRECT", "SUPPLY_CHAIN"]).astype(int) * 7
    frame["event_score"] = (
        frame["source_reliability"]
        + frame["relation_directness"]
        + frame["earnings_link_probability_score"]
        + frame["market_reaction"]
        + frame["follow_up_news"]
    ).clip(0, 100)
    return frame.groupby("ticker", as_index=False)["event_score"].max()


def build_event_candidates(tables: dict, scores: pd.DataFrame) -> pd.DataFrame:
    events = tables["events"]
    mapping = tables["event_stock_map"]
    stocks = tables["stocks"]
    prices = tables["daily_prices"].sort_values("date").groupby("ticker").tail(1)
    frame = (
        mapping.merge(events, on="event_id", how="left")
        .merge(stocks, on="ticker", how="left")
        .merge(prices[["ticker", "return_1m", "return_3m"]], on="ticker", how="left")
        .merge(scores[["ticker", "total_score", "grade", "event_score"]], on="ticker", how="left")
    )
    frame["price_reflection"] = frame["return_1m"].apply(_price_reflection)
    frame["overheat_risk"] = frame["return_1m"].apply(lambda x: "높음" if x >= 15 else "보통" if x >= 7 else "낮음")
    frame["earnings_link_probability"] = frame["relation_type"].map(
        {
            "DIRECT": "높음: 후속 MOU/계약/투자 확인 필요",
            "SUPPLY_CHAIN": "중간: 실제 공급 물량과 단가 확인 필요",
            "SECTOR_THEME": "낮음~중간: 실적 연결 경로 검증 필요",
            "SPECULATIVE": "낮음: 뉴스 반복성과 공식 출처 확인 필요",
        }
    )
    frame["secondary_candidate"] = (frame["relation_type"] != "DIRECT") & (frame["return_1m"] < 10)
    return frame.sort_values(["event_score", "relation_strength"], ascending=False)


def _price_reflection(return_1m: float) -> str:
    if return_1m >= 15:
        return "상당 부분 반영 가능"
    if return_1m >= 7:
        return "일부 반영"
    return "아직 덜 반영된 후보"
