import pandas as pd
import requests

from data_collectors.base import BaseCollector
from utils.env import get_first_env
from utils.retry import retry_on_exception
from utils.text_cleaner import clean_text


class NaverNewsCollector(BaseCollector):
    API_URL = "https://openapi.naver.com/v1/search/news.json"
    CLIENT_ID_KEYS = ["NAVER_CLIENT_ID", "NAVER_SEARCH_CLIENT_ID", "VITE_NAVER_CLIENT_ID"]
    CLIENT_SECRET_KEYS = ["NAVER_CLIENT_SECRET", "NAVER_SEARCH_CLIENT_SECRET", "VITE_NAVER_CLIENT_SECRET"]

    def __init__(self, fallback_data=None, timeout: int = 10):
        super().__init__(fallback_data=fallback_data, timeout=timeout)
        self.client_id = get_first_env(self.CLIENT_ID_KEYS)
        self.client_secret = get_first_env(self.CLIENT_SECRET_KEYS)
        self.last_error = ""
        self.last_request_url = ""

    def _headers(self) -> dict:
        if not self.client_id or not self.client_secret:
            raise RuntimeError(
                "NAVER_CLIENT_ID/NAVER_CLIENT_SECRET missing. "
                "루트 .env 또는 investment_radar/.env에 NAVER_CLIENT_ID=..., NAVER_CLIENT_SECRET=... 형식으로 추가하세요."
            )
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

    @retry_on_exception()
    def search_news(self, query: str, display: int = 20, sort: str = "date", start: int = 1) -> pd.DataFrame:
        try:
            self.last_error = ""
            self.last_request_url = ""
            display = max(1, min(int(display), 100))
            start = max(1, min(int(start), 1000))
            if sort not in ("sim", "date"):
                sort = "date"
            response = requests.get(
                self.API_URL,
                headers=self._headers(),
                params={"query": query, "display": display, "start": start, "sort": sort},
                timeout=self.timeout,
            )
            self.last_request_url = response.url
            if not response.ok:
                self.last_error = _format_naver_error(response)
            response.raise_for_status()
            return self.normalize(response.json())
        except Exception as error:
            if not self.last_error:
                self.last_error = str(error)
            self.logger.exception("Naver news API failed for query=%s: %s", query, error)
            return self.fallback_data.copy()

    def fetch(self, query: str, display: int = 20, sort: str = "date", start: int = 1):
        return self.search_news(query=query, display=display, sort=sort, start=start)

    def normalize(self, raw) -> pd.DataFrame:
        items = raw.get("items", []) if isinstance(raw, dict) else []
        frame = pd.DataFrame(items)
        if frame.empty:
            return pd.DataFrame(columns=["title", "link", "description", "pubDate"])
        frame["title"] = frame["title"].map(clean_text)
        frame["description"] = frame["description"].map(clean_text)
        frame = frame.rename(columns={"originallink": "original_link"})
        return frame.drop_duplicates(subset=["link"])[["title", "link", "description", "pubDate"]]


def _format_naver_error(response: requests.Response) -> str:
    body = response.text[:500]
    try:
        payload = response.json()
        if isinstance(payload, dict):
            body = f"{payload.get('errorCode', '')} {payload.get('errorMessage', payload)}"
    except ValueError:
        pass
    help_text = ""
    if response.status_code == 401:
        help_text = " Client ID/Secret 값 또는 변수명을 확인하세요."
    elif response.status_code == 403:
        help_text = " 네이버 개발자센터 애플리케이션 API 설정에서 '검색' 권한이 선택되어 있는지 확인하세요."
    elif response.status_code == 400:
        help_text = " query/display/start/sort 파라미터를 확인하세요."
    return f"HTTP {response.status_code}: {body}{help_text}"


if __name__ == "__main__":
    collector = NaverNewsCollector()
    print(collector.search_news("삼성전자 HBM", display=3).to_string(index=False))
