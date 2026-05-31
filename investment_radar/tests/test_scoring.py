from database.db import get_connection, initialize_database, load_table
from scoring.total_score import calculate_all_scores


def test_calculate_all_scores(tmp_path):
    db_path = tmp_path / "test.sqlite"
    initialize_database(db_path)
    conn = get_connection(db_path)
    tables = {
        name: load_table(conn, name)
        for name in ["stocks", "daily_prices", "financials", "valuation_features", "news", "events", "event_stock_map"]
    }
    scores = calculate_all_scores(tables)
    assert not scores.empty
    assert {"ticker", "total_score", "grade"}.issubset(scores.columns)
