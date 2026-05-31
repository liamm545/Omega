from abc import ABC, abstractmethod
from typing import Any, Optional

import pandas as pd

from utils.logger import get_logger


class BaseCollector(ABC):
    def __init__(self, fallback_data: Optional[pd.DataFrame] = None, timeout: int = 10):
        self.fallback_data = fallback_data if fallback_data is not None else pd.DataFrame()
        self.timeout = timeout
        self.logger = get_logger(self.__class__.__name__)

    def run(self, *args, **kwargs) -> pd.DataFrame:
        try:
            raw = self.fetch(*args, **kwargs)
            return self.normalize(raw)
        except Exception as error:
            self.logger.exception("collector failed; returning fallback data: %s", error)
            return self.fallback_data.copy()

    @abstractmethod
    def fetch(self, *args, **kwargs) -> Any:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw: Any) -> pd.DataFrame:
        raise NotImplementedError

    def save(self, rows: pd.DataFrame, conn, table_name: str) -> int:
        if rows.empty:
            return 0
        rows.to_sql(table_name, conn, if_exists="append", index=False)
        return len(rows)
