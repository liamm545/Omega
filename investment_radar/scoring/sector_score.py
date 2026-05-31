import pandas as pd

from scoring.common import clip_score, percentile_high_is_good


def calculate_sector_score(stocks: pd.DataFrame, improvement: pd.DataFrame, momentum: pd.DataFrame, news: pd.DataFrame) -> pd.DataFrame:
    frame = stocks[["ticker", "sector"]].merge(improvement, on="ticker", how="left").merge(momentum, on="ticker", how="left")
    news_counts = news.groupby("ticker").size().rename("news_count").reset_index()
    frame = frame.merge(news_counts, on="ticker", how="left")
    sector = frame.groupby("sector").agg(
        sector_improvement=("improvement_score", "mean"),
        sector_momentum=("momentum_score", "mean"),
        sector_news=("news_count", "sum"),
    )
    sector["sector_score"] = clip_score(
        pd.concat(
            [
                percentile_high_is_good(sector["sector_improvement"]),
                percentile_high_is_good(sector["sector_momentum"]),
                percentile_high_is_good(sector["sector_news"]),
            ],
            axis=1,
        ).mean(axis=1)
    )
    return frame[["ticker", "sector"]].merge(sector[["sector_score"]], on="sector", how="left")[["ticker", "sector_score"]]
