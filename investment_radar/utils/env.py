from pathlib import Path
import os

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]


def load_env_files() -> None:
    """Load both app-local and project-root .env files.

    Streamlit keeps the Python process alive while files are edited, so this is
    called from get_env as well as at import time.
    """
    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT.parent / ".env")


load_env_files()


def get_env(name: str, default=None, required: bool = False):
    load_env_files()
    value = os.getenv(name, default)
    if required and (value is None or value == ""):
        raise RuntimeError(
            f"환경변수 {name} 값이 필요합니다. investment_radar/.env 또는 프로젝트 루트 .env에 {name}=... 형식으로 추가하세요."
        )
    return value


def get_first_env(names: list[str], default=None, required: bool = False):
    for name in names:
        value = get_env(name)
        if value not in (None, ""):
            return value
    if required:
        joined = " 또는 ".join(names)
        raise RuntimeError(f"환경변수 {joined} 중 하나가 필요합니다.")
    return default
