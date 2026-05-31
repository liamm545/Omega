from datetime import date


def today_kst_string() -> str:
    return date.today().isoformat()
