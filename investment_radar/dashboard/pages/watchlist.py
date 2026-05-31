from pathlib import Path

import streamlit as st
import yaml


def render_watchlist(tables, scores) -> None:
    st.title("Watchlist")
    path = Path(__file__).resolve().parents[2] / "config" / "watchlist.yaml"
    with open(path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    st.dataframe(data["watchlist"], use_container_width=True)
    st.caption("향후 CSV 업로드와 병합해 개인 관심 종목/키워드를 반영합니다.")
