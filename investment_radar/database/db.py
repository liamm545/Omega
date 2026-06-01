from pathlib import Path
import sqlite3
from datetime import datetime

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "database" / "schema.sql"


def get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database(db_path: Path) -> None:
    conn = get_connection(db_path)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
        conn.executescript(file.read())
    ensure_schema_compatibility(conn)
    purge_sample_intelligence_data(conn)
    seed_sample_data(conn)
    seed_industry_intelligence_data(conn)
    conn.close()


def load_table(conn: sqlite3.Connection, table_name: str) -> pd.DataFrame:
    return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)


def upsert_rows(conn: sqlite3.Connection, table_name: str, rows: pd.DataFrame, key_columns: list[str]) -> int:
    if rows.empty:
        return 0
    columns = list(rows.columns)
    placeholders = ", ".join(["?"] * len(columns))
    update_columns = [column for column in columns if column not in key_columns]
    update_clause = ", ".join([f"{column}=excluded.{column}" for column in update_columns])
    if update_clause:
        sql = (
            f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders}) "
            f"ON CONFLICT({', '.join(key_columns)}) DO UPDATE SET {update_clause}"
        )
    else:
        sql = f"INSERT OR IGNORE INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    conn.executemany(sql, rows[columns].itertuples(index=False, name=None))
    conn.commit()
    return len(rows)


def log_update(conn: sqlite3.Connection, source: str, status: str, rows: int = 0, message: str = "") -> None:
    conn.execute(
        "INSERT INTO update_logs (created_at, source, status, rows, message) VALUES (?, ?, ?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), source, status, int(rows or 0), message),
    )
    conn.commit()


def ensure_schema_compatibility(conn: sqlite3.Connection) -> None:
    _ensure_columns(
        conn,
        "industry_kpis",
        {
            "sector": "TEXT",
            "kpi_name": "TEXT",
            "yoy_change": "REAL",
            "mom_change": "REAL",
            "trend_3m": "REAL",
            "trend_6m": "REAL",
            "source_url": "TEXT",
            "updated_at": "TEXT",
        },
    )
    _ensure_columns(
        conn,
        "scores",
        {
            "sector_cycle_score": "REAL",
            "event_impact_score": "REAL",
            "second_order_score": "REAL",
            "overheating_penalty": "REAL",
        },
    )
    _ensure_columns(
        conn,
        "event_impacts",
        {
            "negative_impact_companies_json": "TEXT",
        },
    )


def _ensure_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    for column, column_type in columns.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
    conn.commit()


def purge_sample_intelligence_data(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM macro_indicators WHERE source = 'sample'")
    conn.execute("DELETE FROM industry_kpis WHERE source = 'sample'")
    conn.execute("DELETE FROM news WHERE source = 'sample' OR title LIKE '샘플:%'")
    conn.execute("DELETE FROM event_stock_map WHERE event_id IN (SELECT event_id FROM events WHERE event_name LIKE '샘플:%')")
    conn.execute("DELETE FROM events WHERE event_name LIKE '샘플:%'")
    conn.commit()


def seed_sample_data(conn: sqlite3.Connection) -> None:
    current = conn.execute("SELECT COUNT(*) AS cnt FROM stocks").fetchone()["cnt"]
    if current:
        return

    stocks = [
        ("005930", "삼성전자", "KOSPI", "반도체", "메모리/파운드리", 470_000_000_000_000),
        ("000660", "SK하이닉스", "KOSPI", "반도체", "메모리", 150_000_000_000_000),
        ("035420", "NAVER", "KOSPI", "인터넷", "플랫폼/AI", 32_000_000_000_000),
        ("066570", "LG전자", "KOSPI", "전자", "가전/전장/스마트팩토리", 17_500_000_000_000),
        ("064400", "LG씨엔에스", "KOSPI", "IT서비스", "클라우드/스마트팩토리", 6_800_000_000_000),
        ("012450", "한화에어로스페이스", "KOSPI", "방산", "항공/방산", 14_000_000_000_000),
        ("010140", "삼성중공업", "KOSPI", "조선", "조선", 8_700_000_000_000),
        ("034020", "두산에너빌리티", "KOSPI", "원전", "원전/발전", 12_200_000_000_000),
    ]
    conn.executemany("INSERT INTO stocks VALUES (?, ?, ?, ?, ?, ?)", stocks)

    daily_prices = [
        ("2026-05-29", "005930", 76000, 77400, 75500, 77100, 22_000_000, 1_690_000_000_000, 1.2, 6.8, 12.5),
        ("2026-05-29", "000660", 205000, 214000, 202000, 212000, 5_200_000, 1_090_000_000_000, 3.1, 13.5, 28.0),
        ("2026-05-29", "035420", 190000, 195000, 187000, 193500, 1_100_000, 212_000_000_000, 0.9, 4.2, 8.8),
        ("2026-05-29", "066570", 104000, 111500, 102000, 110000, 1_900_000, 207_000_000_000, 4.6, 9.5, 17.4),
        ("2026-05-29", "064400", 68000, 69500, 66400, 69000, 740_000, 50_000_000_000, 1.8, 3.2, 6.1),
        ("2026-05-29", "012450", 256000, 263000, 251000, 260000, 690_000, 179_000_000_000, 1.1, 8.0, 21.5),
        ("2026-05-29", "010140", 9800, 10100, 9600, 10050, 11_000_000, 110_000_000_000, 2.4, 15.0, 33.0),
        ("2026-05-29", "034020", 20900, 21600, 20500, 21400, 4_500_000, 95_000_000_000, 1.9, 7.5, 14.2),
    ]
    conn.executemany("INSERT INTO daily_prices VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", daily_prices)

    financials = [
        ("005930", 2026, 1, 72_000, 8_900, 7_100, 460_000, 95_000, 365_000, 13_500, 8_100),
        ("000660", 2026, 1, 19_000, 5_200, 4_100, 120_000, 58_000, 62_000, 7_200, 3_900),
        ("035420", 2026, 1, 2_900, 520, 380, 35_000, 12_000, 23_000, 700, 510),
        ("066570", 2026, 1, 21_000, 1_700, 1_100, 62_000, 36_000, 26_000, 2_100, 1_250),
        ("064400", 2026, 1, 1_450, 180, 130, 7_800, 3_100, 4_700, 230, 170),
        ("012450", 2026, 1, 2_800, 420, 310, 19_000, 9_500, 9_500, 450, 280),
        ("010140", 2026, 1, 2_500, 260, 180, 18_500, 13_000, 5_500, 360, 210),
        ("034020", 2026, 1, 4_100, 350, 220, 27_000, 17_500, 9_500, 410, 240),
        ("005930", 2025, 1, 64_000, 6_200, 5_000, 445_000, 94_000, 351_000, 10_900, 6_200),
        ("000660", 2025, 1, 12_000, 2_100, 1_400, 111_000, 60_000, 51_000, 4_000, 1_500),
        ("035420", 2025, 1, 2_550, 410, 310, 33_000, 12_600, 20_400, 620, 430),
        ("066570", 2025, 1, 19_200, 1_250, 780, 60_000, 36_700, 23_300, 1_650, 860),
    ]
    conn.executemany("INSERT INTO financials VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", financials)

    valuations = [
        ("2026-05-29", "005930", 13.5, 1.25, 1.9, 7.8, 4.2, 1.8),
        ("2026-05-29", "000660", 18.8, 2.15, 3.6, 9.9, 2.6, 0.7),
        ("2026-05-29", "035420", 22.0, 1.45, 4.4, 11.2, 3.4, 0.5),
        ("2026-05-29", "066570", 9.7, 0.95, 0.52, 4.8, 6.1, 1.2),
        ("2026-05-29", "064400", 25.0, 2.8, 2.9, 13.5, 2.0, 0.0),
        ("2026-05-29", "012450", 16.0, 2.1, 1.8, 8.5, 3.1, 0.8),
        ("2026-05-29", "010140", 12.0, 1.7, 1.2, 7.0, 2.4, 0.0),
        ("2026-05-29", "034020", 19.5, 1.6, 1.4, 10.0, 2.2, 0.0),
    ]
    conn.executemany("INSERT INTO valuation_features VALUES (?, ?, ?, ?, ?, ?, ?, ?)", valuations)

    conn.commit()


def seed_industry_intelligence_data(conn: sqlite3.Connection) -> None:
    # No synthetic macro/KPI rows are seeded. These tables must be populated by
    # explicit collectors or user-provided datasets so the cycle engine never
    # treats fabricated numbers as evidence.
    return None
