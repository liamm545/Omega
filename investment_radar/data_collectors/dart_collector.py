import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET

import pandas as pd
import requests

from data_collectors.base import BaseCollector
from utils.env import get_env
from utils.retry import retry_on_exception


class DartCollector(BaseCollector):
    BASE_URL = "https://opendart.fss.or.kr/api"

    def __init__(self, fallback_data=None, timeout: int = 10):
        super().__init__(fallback_data=fallback_data, timeout=timeout)
        self.api_key = get_env("DART_API_KEY")
        self._corp_code_cache = None

    def _require_key(self) -> bool:
        if not self.api_key:
            self.logger.warning("DART_API_KEY missing; returning fallback/empty data")
            return False
        return True

    @retry_on_exception()
    def _get_json(self, endpoint: str, params: dict) -> dict:
        response = requests.get(f"{self.BASE_URL}/{endpoint}", params=params, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") not in (None, "000"):
            raise RuntimeError(f"DART API error {payload.get('status')}: {payload.get('message')}")
        return payload

    @retry_on_exception()
    def fetch_corp_codes(self) -> pd.DataFrame:
        if self._corp_code_cache is not None:
            return self._corp_code_cache.copy()
        if not self._require_key():
            return pd.DataFrame(columns=["corp_code", "corp_name", "stock_code", "modify_date"])

        response = requests.get(
            f"{self.BASE_URL}/corpCode.xml",
            params={"crtfc_key": self.api_key},
            timeout=self.timeout,
        )
        response.raise_for_status()
        with zipfile.ZipFile(BytesIO(response.content)) as zipped:
            xml_bytes = zipped.read("CORPCODE.xml")
        root = ET.fromstring(xml_bytes)
        rows = [
            {
                "corp_code": item.findtext("corp_code"),
                "corp_name": item.findtext("corp_name"),
                "stock_code": item.findtext("stock_code"),
                "modify_date": item.findtext("modify_date"),
            }
            for item in root.findall("list")
        ]
        self._corp_code_cache = pd.DataFrame(rows)
        return self._corp_code_cache.copy()

    def get_corp_code(self, stock_code: str) -> str:
        corp_codes = self.fetch_corp_codes()
        matched = corp_codes[corp_codes["stock_code"].eq(stock_code)]
        if matched.empty:
            raise ValueError(f"DART corp_code not found for stock_code={stock_code}")
        return matched.iloc[0]["corp_code"]

    def fetch_financial_statement(self, stock_code: str, year: int, reprt_code: str = "11013") -> dict:
        if not self._require_key():
            return {}
        corp_code = self.get_corp_code(stock_code)
        return self.fetch_financial_statement_by_corp_code(corp_code, year, reprt_code)

    def fetch_financial_statement_by_corp_code(self, corp_code: str, year: int, reprt_code: str = "11013") -> dict:
        if not self._require_key():
            return {}
        return self._get_json(
            "fnlttSinglAcntAll.json",
            {
                "crtfc_key": self.api_key,
                "corp_code": corp_code,
                "bsns_year": str(year),
                "reprt_code": reprt_code,
                "fs_div": "CFS",
            },
        )

    def search_filings(self, corp_code: str = None, begin_date: str = None, end_date: str = None, page_count: int = 20) -> pd.DataFrame:
        if not self._require_key():
            return pd.DataFrame()
        params = {"crtfc_key": self.api_key, "page_count": page_count}
        if corp_code:
            params["corp_code"] = corp_code
        if begin_date:
            params["bgn_de"] = begin_date.replace("-", "")
        if end_date:
            params["end_de"] = end_date.replace("-", "")
        payload = self._get_json("list.json", params)
        return pd.DataFrame(payload.get("list", []))

    def fetch(self, *args, **kwargs):
        return self.fetch_financial_statement(*args, **kwargs)

    def normalize(self, raw) -> pd.DataFrame:
        rows = raw.get("list", []) if isinstance(raw, dict) else []
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows)

    def normalize_financial_statement(self, stock_code: str, raw: dict, year: int, quarter: int) -> pd.DataFrame:
        rows = raw.get("list", []) if isinstance(raw, dict) else []
        if not rows:
            return pd.DataFrame(columns=_financial_columns())

        data = pd.DataFrame(rows)
        data["amount"] = data["thstrm_amount"].map(_to_number)
        account_map = {
            "revenue": ["매출액", "영업수익"],
            "operating_profit": ["영업이익"],
            "net_income": ["당기순이익", "분기순이익", "반기순이익"],
            "assets": ["자산총계"],
            "liabilities": ["부채총계"],
            "equity": ["자본총계"],
            "operating_cash_flow": ["영업활동 현금흐름", "영업활동으로 인한 현금흐름"],
        }
        values = {key: _pick_account(data, names) for key, names in account_map.items()}
        values["free_cash_flow"] = None
        return pd.DataFrame(
            [
                {
                    "ticker": stock_code,
                    "year": year,
                    "quarter": quarter,
                    **values,
                }
            ],
            columns=_financial_columns(),
        )


def _to_number(value):
    if value in (None, "", "-"):
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def _pick_account(data: pd.DataFrame, account_names: list[str]):
    matched = data[data["account_nm"].isin(account_names)]
    if matched.empty:
        return None
    return matched.iloc[0]["amount"]


def _financial_columns() -> list[str]:
    return [
        "ticker",
        "year",
        "quarter",
        "revenue",
        "operating_profit",
        "net_income",
        "assets",
        "liabilities",
        "equity",
        "operating_cash_flow",
        "free_cash_flow",
    ]


if __name__ == "__main__":
    collector = DartCollector()
    print(collector.search_filings(page_count=3).head().to_string(index=False))
