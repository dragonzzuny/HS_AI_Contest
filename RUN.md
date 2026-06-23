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

## 다음 작업 (TODO)
- [ ] backend에 Weaviate 하이브리드 검색 + BGE-reranker 연결 (현재 키워드 폴백)
- [ ] 처리보조 고도화: 신청서/진정서 초안 LLM 자동작성 (현재 템플릿 힌트만)
- [ ] L2 조문 검색 시 담당부서·시행일 메타 노출
- [ ] `kb/_TODO_VERIFY.md` 16건 검증 → 신뢰도 '확인됨' 승격
- [ ] 공개 배포(심사용 URL): Ollama PC를 cloudflared 터널 등으로 외부 노출 또는 클라우드 이전
- [ ] 솔루션 소개서 5p + 발표자료

## 구조
```
backend/app.py      FastAPI: 검색+생성(Ollama/MOCK)+처리보조+인용
web/                프론트(채팅+소스패널+6개언어+처리보조 칩)
kb/                 L1 FAQ(8도메인) + 스키마/DB설계/검증목록 + build/
scripts/            build_kb / collect_ordinances / ingest_weaviate
docker-compose.weaviate.yml
```
