FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLCONFIGDIR=/tmp/matplotlib \
    PYTHONPATH=/app/investment_radar

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY investment_radar/requirements.txt /app/investment_radar/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /app/investment_radar/requirements.txt

COPY investment_radar /app/investment_radar

EXPOSE 8501

CMD streamlit run investment_radar/app.py \
    --server.address=0.0.0.0 \
    --server.port=${PORT:-8501} \
    --server.headless=true \
    --browser.gatherUsageStats=false
