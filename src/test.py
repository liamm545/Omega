import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DART_API_KEY = os.getenv("DART_API_KEY")

# 삼성전자 DART 고유번호
# 주의: 종목코드 005930이 아니라 DART corp_code임
SAMSUNG_CORP_CODE = "00126380"

url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"

params = {
    "crtfc_key": DART_API_KEY,
    "corp_code": SAMSUNG_CORP_CODE,
    "bsns_year": "2024",
    "reprt_code": "11011",  # 사업보고서
    "fs_div": "CFS",        # 연결재무제표
}

res = requests.get(url, params=params, timeout=10)
data = res.json()

print("status:", data.get("status"))
print("message:", data.get("message"))

if data.get("status") != "000":
    raise RuntimeError(data.get("message"))

df = pd.DataFrame(data["list"])

# 보기 좋은 주요 컬럼만 출력
cols = [
    "sj_nm",          # 재무제표명
    "account_nm",    # 계정명
    "thstrm_nm",     # 당기명
    "thstrm_amount", # 당기금액
    "frmtrm_nm",     # 전기명
    "frmtrm_amount", # 전기금액
]

print(df[cols].head(30))

# CSV 저장
df.to_csv("samsung_2024_financials.csv", index=False, encoding="utf-8-sig")
print("saved: samsung_2024_financials.csv")