# 화성ON 실행 가이드 (Ollama PC 인계용)

다국어 외국인 생활민원 AI 안내사. 단일 FastAPI 앱이 프론트+API를 서빙한다.
**Ollama/Weaviate 없이도 MOCK 모드로 즉시 작동.** 둘이 잡히면 실동작으로 자동 승격.

## 현재 데이터 (완료)
- L1 정제 FAQ: `kb/build/kb.json` (37건, 사람 검증)
- L2 자치법규: `kb/build/ordinances_chunks.json` (839개 조례·규칙 → 11,268 조문 청크)
- 데이터 재생성: `python scripts/build_kb.py` / `LAW_OC=<발급받은OC> python scripts/collect_ordinances.py`
  - OC 키: https://open.law.go.kr 가입 후 OPEN API 신청(무료)

## 1) 최소 실행 (MOCK — 키워드 검색 + 템플릿 답변)
```
pip install -r backend/requirements.txt
python -m uvicorn backend.app:app --host 0.0.0.0 --port 5200
# 브라우저: http://localhost:5200
```
또는 한 번에(접속 주소 안내 + 방화벽 규칙 포함):
```
./scripts/serve.ps1      # PowerShell
```

## 1-1) 외부 컴퓨터에서 접속하기

**같은 네트워크(사내망/Wi-Fi)**: 서버를 `--host 0.0.0.0`으로 띄우면(위 명령) 다른 PC·휴대폰에서
`http://<이 PC의 IP>:5200` 으로 접속. `./scripts/serve.ps1`이 접속 가능한 IP를 출력하고
Windows 방화벽 인바운드 규칙(포트 5200)도 자동 추가합니다(최초 1회 관리자 권한 권장).

**인터넷(외부 컴퓨터·외부 도메인)** — 용도별 3가지 경로:

### A. 임시 공개 URL (가장 빠름 · 계정 불필요) — 심사 데모용 추천
```
# 창 1: 서버
./scripts/serve.ps1
# 창 2: 인터넷 공개 (https://....trycloudflare.com 주소 발급)
./scripts/tunnel.ps1
```
출력되는 `https://<무작위>.trycloudflare.com` 주소만 공유하면 전 세계 어디서나 접속.
임시 주소이며 창을 닫으면 사라집니다. `bin/cloudflared.exe` 동봉(없으면 자동 다운로드).

### B. 고정 무료 도메인 (ngrok) — 매번 같은 주소가 필요할 때
1. https://ngrok.com 무료 가입 → 대시보드에서 **무료 정적 도메인 1개**(`xxxx.ngrok-free.app`)와 authtoken 발급
2. 설치·인증·실행:
```
winget install ngrok.ngrok            # 또는 https://ngrok.com/download
ngrok config add-authtoken <발급받은_토큰>
ngrok http --url=xxxx.ngrok-free.app 5200
```
→ 항상 `https://xxxx.ngrok-free.app` 같은 고정 주소로 접속(서버는 ./scripts/serve.ps1 로 켜둠).

### C. 커스텀 도메인 (내 도메인, 예: hwaseong-on.example.com) — Cloudflare Named Tunnel
본인 소유 도메인을 Cloudflare에 등록한 경우, 무료로 고정 커스텀 도메인 운영 가능.
```
# 최초 1회
bin\cloudflared.exe tunnel login
bin\cloudflared.exe tunnel create hwaseong-on
bin\cloudflared.exe tunnel route dns hwaseong-on hwaseong-on.<내도메인>
# 이후 실행
./scripts/serve.ps1            # 창1: 서버
./scripts/tunnel_named.ps1     # 창2: 고정 커스텀 도메인으로 공개
```

### D. 24시간 상시 운영 (PC를 꺼도 유지) — 클라우드 배포
이 앱은 **MOCK 모드(키워드+템플릿)** 그대로면 어디든 배포 가능:
- Render / Railway / Fly.io 등에 `python -m uvicorn backend.app:app --host 0.0.0.0 --port $PORT`로 배포 → 무료/유료 공개 URL.
- **실답변(Ollama 다국어)**까지 상시로 하려면 LLM이 필요 → ① 로컬 Ollama PC를 위 B/C 터널로 상시 노출하거나 ② 클라우드 GPU에 Ollama를 함께 띄웁니다.

> 정리: **지금 심사용이면 A**, **계속 같은 주소가 필요하면 B(무료 고정) 또는 C(내 도메인)**, **PC를 꺼도 24시간이면 D**.

## 1-2) 화면·사용 과정 캡처 (소개서/발표자료용)
실제 동작 캡처 10종이 `docs/screenshots/`에 있습니다 → [docs/SCREENSHOTS.md](docs/SCREENSHOTS.md).
재생성:
```
pip install playwright && python -m playwright install chromium
python scripts/screenshot.py     # 서버가 5200에 떠 있는 상태에서 실행
```

## 2) 실동작 (Ollama — 다국어 그라운딩 답변)
```
# Ollama에 모델 준비 (한국어 강한 모델 권장)
ollama pull qwen2.5:14b        # 또는 exaone3.5:7.8b, gemma2:9b 등
ollama pull bge-m3             # 임베딩(추후 Weaviate 적재 시)

# 환경변수 설정 후 기동
set OLLAMA_HOST=http://localhost:11434      (PowerShell: $env:OLLAMA_HOST="http://localhost:11434")
set GEN_MODEL=qwen2.5:14b
python -m uvicorn backend.app:app --host 0.0.0.0 --port 5200
```
→ `/api/health`의 mode가 `ollama`로 바뀌면 성공. 6개 언어 실답변 가능.

## 3) 벡터 검색 승격 (Weaviate + BGE-M3, 선택)
```
docker compose -f docker-compose.weaviate.yml up -d        # localhost:8080
pip install -r requirements.txt                            # sentence-transformers, weaviate-client
python scripts/ingest_weaviate.py                          # L1+L2 임베딩 적재 (11k+ 청크)
```
※ 현재 `backend/app.py`는 KB 키워드 검색을 사용. Weaviate 하이브리드 검색으로 교체하는 retrieval 모듈은 다음 작업 항목(아래 TODO).

## 웹 폴백(선택) — KB에 없는 질문을 '공식 홈페이지'만 검색해 안내
환경변수 `WEB_FALLBACK=1` 이면, KB(온톨로지)에 근거가 없을 때 **공식 도메인(.go.kr/.or.kr/gov.kr)만**
인터넷 검색·요약해 안내합니다(블로그·상업사이트 배제). 답변에 "🌐 인터넷(공식)" 출처 + "확인 필요" 면책을 붙이며,
공식 출처가 없으면(예: 비트코인·맛집) 그대로 안전 거부합니다. 인터넷 연결 필요, LLM 없으면 공식 링크만 안내.
```
WEB_FALLBACK=1 OLLAMA_HOST=http://localhost:11434 GEN_MODEL=gemma3:4b python -m uvicorn backend.app:app --host 0.0.0.0 --port 5200
```

## 완료
- [x] 프론트 전면 리디자인(밝은 공공서비스 톤·반응형·접근성·6개 언어 UI 완전 현지화)
- [x] **환각 방지 가드레일**: 신뢰도 게이트 + 안전 거부 + 인용 무결성 검증 (`backend/app.py`)
- [x] **평가 하네스**(`scripts/eval.py`): 라우팅·인용·환각거부율 정량 측정, 전 지표 게이트 통과
- [x] **도메인 온톨로지**(`kb/ontology.json` + `scripts/build_ontology.py`): 실효 법조문·자격·선행절차·지원정책 연결
- [x] **온톨로지 무결성 검증**(`scripts/validate_ontology.py`): 헛링크·쓰레기·끊긴참조 자동 차단(오류 0)
- [x] **데이터 정화**: L2 수집실패 청크 79건 검색·인용 제외 / **서류 .txt 다운로드** 추가
- [x] AX 리뷰 문서: `docs/ONTOLOGY_REVIEW.md`(문제 발견→수정→검증)
- [x] 화면/사용 과정 캡처 13종 (`docs/screenshots/`, `scripts/screenshot.py`)
- [x] 외부 접속: LAN(`serve.ps1`) + Quick Tunnel(`tunnel.ps1`) + 커스텀도메인(`tunnel_named.ps1`)
- [x] 클라우드 24시간 배포 설정(`render.yaml` + `docs/DEPLOY.md`)
- [x] 서류초안(임금체불 진정서/대형폐기물 신고) 빈칸→공식 서식 생성 + 복사
- [x] **서류 다운로드 3종**: HWPX(한글)·DOCX(Word)·TXT — 한글 없이도 받기
- [x] **HWPX 생성 검증**: 실제 한글(HWP)에서 열림+내용 정확성 확인(MCP로 검증)
- [x] **실제 공식 서식 채움 엔진**(`fill_hwpx_template`): .hwpx 서식 빈칸을 서버에서 치환→실제 한글에서 열림 검증.
      서식 등록부 `kb/forms/registry.json`(없으면 생성본 폴백)
- [x] **공문서 수집 카탈로그**(`kb/forms/catalog.json`): 8개 분야 고빈도·안정 서식 목록(출처·다국어·수집상태).
      답변에 "공식 서식" 링크로 노출. 임금체불 진정서 1건 수집(`kb/forms/sources/`)

## 다음 작업 (TODO)
- [ ] backend에 Weaviate 하이브리드 검색 + BGE-reranker 연결 (현재 키워드 폴백)
- [ ] 처리보조 고도화: 신청서/진정서 초안 LLM 자동작성 (현재 템플릿 + Ollama 다국어 요약)
- [ ] 온톨로지 확장: L1↔L2 조문 단위 정밀 링크 확대(현재 도메인 대표 조문)
- [ ] `kb/_TODO_VERIFY.md` 16건 검증 → 신뢰도 '확인됨' 승격
- [ ] 솔루션 소개서 5p + 발표자료

## 구조
```
backend/app.py      FastAPI: 검색+생성(Ollama/MOCK)+처리보조+인용
web/                프론트(채팅+소스패널+6개언어+처리보조 칩)
kb/                 L1 FAQ(8도메인) + 스키마/DB설계/검증목록 + build/
scripts/            build_kb / collect_ordinances / ingest_weaviate
docker-compose.weaviate.yml
```
