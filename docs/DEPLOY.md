# 화성ON 배포 가이드 (24시간 고정 URL — 심사위원 자유 접속용)

PC 전원과 무관하게 항상 켜져 있고, 고정·깔끔한 URL을 발급하는 **Render 무료 배포**를 권장합니다.
MOCK 모드(근거검색·인용·**환각 거부**·서류초안·온톨로지)는 LLM 없이 그대로 동작합니다.

## 사전 조건
- 이 저장소가 GitHub에 올라가 있어야 합니다. (현재 origin: `github.com/dragonzzuny/HS_AI_Contest`)
- 변경사항을 **먼저 커밋·푸시**해야 Render가 최신 코드를 배포합니다.
  ```
  git add -A && git commit -m "화성ON: 환각 가드레일+온톨로지+평가하네스+UI" && git push
  ```
- `kb/build/ordinances_chunks.json`(법제처 수집본, 12MB)은 저장소에 포함되어 있어야 합니다.
  (`kb.json`·`ontology.json`은 배포 시 `render.yaml`이 자동 재생성)

## Render 배포 (Blueprint, 5분)
1. https://render.com 가입(GitHub 로그인) → **New +** → **Blueprint**
2. 이 저장소 선택 → 루트의 `render.yaml`을 자동 인식 → **Apply**
3. 빌드 완료 후 발급되는 URL 확인: `https://hwaseong-on.onrender.com`
4. `https://hwaseong-on.onrender.com/api/health` 에서 `"ok": true` 확인
5. 이 URL을 심사 제출/공유

> 무료 플랜은 15분 미사용 시 휴면 → 다음 첫 접속이 30~60초 느릴 수 있습니다(이후 정상).
> 항상 즉시 응답이 필요하면 유료 Starter(월 $7) 또는 외부 핑(uptime monitor) 사용.

## (선택) 실시간 다국어 답변까지 켜기
배포본은 기본 MOCK(답변 본문 한국어). 6개 언어 **실제 번역 답변**까지 하려면 LLM 연결:
- 집/사무실 Ollama PC를 `./scripts/tunnel.ps1`(또는 ngrok)로 노출 → 그 주소를
  Render 환경변수 `OLLAMA_HOST`에 설정(`GEN_MODEL=qwen2.5:14b`).
- Ollama PC가 꺼지면 자동으로 안전한 MOCK으로 폴백되므로 서비스는 끊기지 않습니다.

## 품질 게이트 (배포 전 자가검증)
```
python -m uvicorn backend.app:app --host 0.0.0.0 --port 5200   # 창1
PYTHONUTF8=1 python scripts/eval.py                            # 창2
```
라우팅 정확도·인용 무결성·**환각(범위 밖) 거부율**이 기준치 이상이면 통과(종료코드 0).

## 대안 배포처
- **Railway / Fly.io**: 동일하게 `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`.
- **로컬 PC + 터널**: `./scripts/serve.ps1` + `./scripts/tunnel.ps1`(임시) / `tunnel_named.ps1`(커스텀 도메인). 상세: [RUN.md](../RUN.md).
