from datetime import datetime, timedelta

import pandas as pd
import requests

from data_collectors.base import BaseCollector
from utils.env import get_env
from utils.retry import retry_on_exception


class KisCollector(BaseCollector):
    """Korea Investment Securities quote-only collector. No order APIs here."""

    MOCK_BASE_URL = "https://openapivts.koreainvestment.com:29443"
    REAL_BASE_URL = "https://openapi.koreainvestment.com:9443"

    def __init__(self, paper: bool = True, fallback_data=None, timeout: int = 10):
        super().__init__(fallback_data=fallback_data, timeout=timeout)
        self.app_key = get_env("KIS_APP_KEY")
        self.app_secret = get_env("KIS_APP_SECRET")
        self.base_url = self.MOCK_BASE_URL if paper else self.REAL_BASE_URL
        self._token = None
        self._token_expires_at = datetime.min

    def _has_credentials(self) -> bool:
        return bool(self.app_key and self.app_secret)

    @retry_on_exception()
    def issue_access_token(self) -> str:
        if not self._has_credentials():
            raise RuntimeError("KIS_APP_KEY/KIS_APP_SECRET missing")
        if self._token and datetime.now() < self._token_expires_at:
            return self._token
        response = requests.post(
            f"{self.base_url}/oauth2/tokenP",
            json={"grant_type": "client_credentials", "appkey": self.app_key, "appsecret": self.app_secret},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        self._token = payload["access_token"]
        self._token_expires_at = datetime.now() + timedelta(seconds=int(payload.get("expires_in", 86400)) - 300)
        return self._token

    @retry_on_exception()
    def get_current_price(self, ticker: str, market: str = "J") -> pd.DataFrame:
        try:
            token = self.issue_access_token()
            response = requests.get(
                f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price",
                headers={
                    "authorization": f"Bearer {token}",
                    "appkey": self.app_key,
                    "appsecret": self.app_secret,
                    "tr_id": "FHKST01010100",
                },
                params={"fid_cond_mrkt_div_code": market, "fid_input_iscd": ticker},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return self.normalize(response.json())
        except Exception as error:
            self.logger.exception("KIS current price failed: %s", error)
            return self.fallback_data.copy()

    def fetch(self, ticker: str, market: str = "J"):
        return self.get_current_price(ticker=ticker, market=market)

    def normalize(self, raw) -> pd.DataFrame:
        output = raw.get("output", raw) if isinstance(raw, dict) else raw
        return pd.DataFrame([output]) if isinstance(output, dict) else pd.DataFrame(output)


if __name__ == "__main__":
    print(KisCollector().get_current_price("005930").head().to_string(index=False))
