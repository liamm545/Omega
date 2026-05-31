# Investment Radar 배포 가이드

이 프로젝트의 Python/Streamlit 앱은 GitHub Pages에 직접 올릴 수 없습니다. GitHub Pages는 정적 HTML/CSS/JavaScript만 제공하므로, Streamlit처럼 Python 프로세스가 계속 실행되어야 하는 앱은 Render, Railway, Fly.io, VPS 같은 서버형 호스팅이 필요합니다.

## 권장 구조

초기 MVP는 Render Web Service에 Streamlit 앱을 배포하고, 구입한 도메인 `www.yeongyeong.online`을 Render 서비스에 연결합니다.

```txt
www.yeongyeong.online
  -> Render Web Service
  -> Docker container
  -> streamlit run investment_radar/app.py
```

React/Vite 앱을 GitHub Pages에 남기고 싶다면 랜딩 페이지로만 사용하고, 실제 Investment Radar 버튼을 Render URL로 연결하세요.

## 1. GitHub에 push

루트에 추가된 배포 파일:

- `Dockerfile`
- `.dockerignore`
- `render.yaml`

Render는 이 파일들을 기준으로 Streamlit 앱을 빌드하고 실행합니다.

## 2. Render에서 배포

1. Render Dashboard에서 `New` -> `Blueprint` 또는 `Web Service`를 선택합니다.
2. GitHub repository를 연결합니다.
3. `render.yaml`을 사용하는 Blueprint 배포를 선택하면 기본 설정이 자동으로 잡힙니다.
4. 환경변수는 Render Dashboard에서 직접 입력합니다. 절대 GitHub에 커밋하지 마세요.

필수/선택 환경변수:

```txt
DART_API_KEY
NAVER_CLIENT_ID
NAVER_CLIENT_SECRET
KRX_API_KEY
OPENAI_API_KEY
INVESTMENT_RADAR_PRICE_SOURCE=pykrx
INVESTMENT_RADAR_MARKETS=KOSPI,KOSDAQ
INVESTMENT_RADAR_DEFAULT_START_DATE=20250101
```

무료 Render Web Service는 파일 변경이 재배포/재시작 때 사라집니다. 현재 기본값은 `/tmp/investment_radar.sqlite`라서 앱은 뜨지만, 버튼으로 수집한 DB 데이터는 영구 보존되지 않을 수 있습니다.

운영용으로 계속 쓸 계획이면 Render Starter 이상으로 올리고 persistent disk를 붙인 뒤 다음 환경변수로 바꾸세요.

```txt
INVESTMENT_RADAR_DB_PATH=/var/data/investment_radar.sqlite
```

그리고 Render Disks에서 mount path를 `/var/data`로 설정합니다.

## 3. 커스텀 도메인 연결

Render 서비스가 먼저 정상 배포되어 `https://...onrender.com` 주소에서 열려야 합니다.

그다음 Render 서비스의 `Settings` 또는 `Custom Domains`에서 다음 도메인을 추가합니다.

```txt
www.yeongyeong.online
```

Render가 보여주는 DNS target을 Namecheap Advanced DNS에 등록합니다. 일반적인 형태는 다음과 같습니다.

```txt
Type: CNAME
Host: www
Value: <your-render-service>.onrender.com
TTL: Automatic
```

기존 Namecheap parking 레코드는 제거해야 합니다.

```txt
www -> parkingpage.namecheap.com
```

루트 도메인 `yeongyeong.online`도 쓰고 싶으면 Render의 Custom Domains 화면에서 apex domain을 추가하고, Render가 안내하는 A/ALIAS 레코드를 그대로 Namecheap에 입력하세요. DNS 제공자마다 apex 처리 방식이 달라서 Render 화면의 지시를 따르는 것이 가장 안전합니다.

## 4. HTTPS

DNS가 전파되면 Render가 인증서를 자동 발급합니다. 인증서 발급 전에는 잠시 `Not verified` 또는 인증서 오류가 보일 수 있습니다.

## 5. 배포 후 확인

앱 상단의 `데이터 연결 상태와 원본 데이터 확인` 패널에서 다음을 확인합니다.

- pykrx 업데이트 로그가 `success` 또는 `partial`인지
- 최신 가격일이 실제 거래일인지
- NAVER 뉴스 업데이트 실패 시 HTTP 상태와 메시지가 무엇인지
- DART corp_code/financials 업데이트 row 수가 증가하는지

## 대안

- Streamlit Community Cloud: 가장 쉽지만 완전한 커스텀 도메인 연결에는 제약이 있습니다. `*.streamlit.app` 하위 도메인 중심입니다.
- Railway/Fly.io: 커스텀 도메인과 Python 앱 실행 가능. 설정은 Render와 비슷하지만 Docker/환경변수/도메인 연결 UI가 조금 다릅니다.
- VPS: 가장 자유롭지만 nginx, HTTPS, 프로세스 관리까지 직접 운영해야 합니다.
