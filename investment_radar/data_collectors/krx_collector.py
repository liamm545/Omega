import pandas as pd
import requests

from data_collectors.base import BaseCollector
from utils.env import get_env
from utils.retry import retry_on_exception


class KrxCollector(BaseCollector):
    """KRX Open API boundary with pykrx fallback placeholders.

    KRX Open API endpoint shapes differ by subscription. Keep these methods as
    stable app-facing interfaces; wire exact endpoints once your API product is fixed.
    """

    BASE_URL = "https://data-dbg.krx.co.kr/svc/apis"

    def __init__(self, fallback_data=None, timeout: int = 10):
        super().__init__(fallback_data=fallback_data, timeout=timeout)
        self.api_key = get_env("KRX_API_KEY")
        self.price_source = get_env("INVESTMENT_RADAR_PRICE_SOURCE", "pykrx")

    def _headers(self) -> dict:
        return {"AUTH_KEY": self.api_key} if self.api_key else {}

    @retry_on_exception()
    def _get(self, path: str, params: dict = None) -> dict:
        if not self.api_key:
            raise RuntimeError("KRX_API_KEY missing; use pykrx fallback or sample data")
        response = requests.get(f"{self.BASE_URL}/{path}", headers=self._headers(), params=params or {}, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_stock_master(self) -> pd.DataFrame:
        if self.price_source == "pykrx":
            return self._pykrx_stock_master()
        try:
            raw = self._get("stk/isu_base_info")
            return pd.DataFrame(raw.get("OutBlock_1", raw.get("data", [])))
        except Exception as error:
            self.logger.warning("KRX master failed, trying pykrx fallback: %s", error)
            return self._pykrx_stock_master()

    def get_daily_price(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        if self.price_source == "pykrx":
            return self._pykrx_daily_price(ticker, start_date, end_date)
        try:
            raw = self._get("stk/stock_by_date", {"isuCd": ticker, "strtDd": start_date, "endDd": end_date})
            return pd.DataFrame(raw.get("OutBlock_1", raw.get("data", [])))
        except Exception as error:
            self.logger.warning("KRX daily price failed, trying pykrx fallback: %s", error)
            return self._pykrx_daily_price(ticker, start_date, end_date)

    def get_market_cap(self, date: str) -> pd.DataFrame:
        if self.price_source == "pykrx":
            return self._pykrx_market_cap(date)
        try:
            raw = self._get("stk/market_cap", {"basDd": date})
            return pd.DataFrame(raw.get("OutBlock_1", raw.get("data", [])))
        except Exception as error:
            self.logger.warning("KRX market cap failed, trying pykrx fallback: %s", error)
            return self._pykrx_market_cap(date)

    def _pykrx_stock_master(self) -> pd.DataFrame:
        try:
            from pykrx import stock
            markets = [market.strip() for market in get_env("INVESTMENT_RADAR_MARKETS", "KOSPI,KOSDAQ").split(",")]
            rows = []
            for market in markets:
                tickers = stock.get_market_ticker_list(market=market)
                rows.extend(
                    {
                        "ticker": ticker,
                        "name": stock.get_market_ticker_name(ticker),
                        "market": market,
                        "sector": "missing",
                        "industry": "missing",
                        "market_cap": None,
                    }
                    for ticker in tickers
                )
            return pd.DataFrame(rows)
        except Exception as error:
            self.logger.warning("pykrx stock master unavailable: %s", error)
            return self.fallback_data.copy()

    def _pykrx_daily_price(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        try:
            from pykrx import stock
            start = start_date.replace("-", "")
            end = end_date.replace("-", "")
            ohlcv = stock.get_market_ohlcv(start, end, ticker).reset_index()
            if ohlcv.empty:
                return pd.DataFrame(columns=_daily_price_columns())
            ohlcv = ohlcv.rename(
                columns={
                    "날짜": "date",
                    "시가": "open",
                    "고가": "high",
                    "저가": "low",
                    "종가": "close",
                    "거래량": "volume",
                    "거래대금": "trading_value",
                    "등락률": "return_1d",
                }
            )
            ohlcv["ticker"] = ticker
            ohlcv["date"] = pd.to_datetime(ohlcv["date"]).dt.strftime("%Y-%m-%d")
            if "trading_value" not in ohlcv.columns:
                ohlcv["trading_value"] = ohlcv["close"] * ohlcv["volume"]
            if "return_1d" not in ohlcv.columns:
                ohlcv["return_1d"] = ohlcv["close"].pct_change() * 100
            ohlcv["return_1m"] = ohlcv["close"].pct_change(21) * 100
            ohlcv["return_3m"] = ohlcv["close"].pct_change(63) * 100
            return ohlcv[_daily_price_columns()].fillna(0)
        except Exception as error:
            self.logger.warning("pykrx daily price unavailable: %s", error)
            return self.fallback_data.copy()

    def _pykrx_market_cap(self, date: str) -> pd.DataFrame:
        try:
            from pykrx import stock
            frame = stock.get_market_cap(date.replace("-", "")).reset_index()
            if frame.empty:
                return pd.DataFrame(columns=["ticker", "market_cap"])
            frame = frame.rename(columns={"티커": "ticker", "시가총액": "market_cap"})
            return frame[["ticker", "market_cap"]]
        except Exception as error:
            self.logger.warning("pykrx market cap unavailable: %s", error)
            return self.fallback_data.copy()

    def fetch(self, *args, **kwargs):
        return self.get_stock_master()

    def normalize(self, raw) -> pd.DataFrame:
        return raw if isinstance(raw, pd.DataFrame) else pd.DataFrame(raw)


def _daily_price_columns() -> list[str]:
    return [
        "date",
        "ticker",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "trading_value",
        "return_1d",
        "return_1m",
        "return_3m",
    ]


if __name__ == "__main__":
    print(KrxCollector().get_stock_master().head().to_string(index=False))
