import pandas as pd
import plotly.express as px
import streamlit as st


def render_sector_radar(tables: dict, scores: pd.DataFrame) -> None:
    st.title("Sector Radar")
    sector = (
        scores.groupby("sector", as_index=False)
        .agg(
            total_score=("total_score", "mean"),
            valuation_score=("valuation_score", "mean"),
            momentum_score=("momentum_score", "mean"),
            event_score=("event_score", "mean"),
            count=("ticker", "count"),
        )
        .sort_values("total_score", ascending=False)
    )
    st.plotly_chart(px.scatter(sector, x="valuation_score", y="momentum_score", size="count", color="event_score", hover_name="sector"), use_container_width=True)
    st.dataframe(sector, use_container_width=True, hide_index=True)
