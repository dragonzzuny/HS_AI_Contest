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

## 한 달 내내 유지 + 즉시 응답 (keep-alive, 무료)

Render 무료 서비스는 **삭제 전까지 무기한 유지**되므로 한 달 심사 기간 동안 계속 떠 있습니다.
다만 15분 미사용 시 휴면(콜드스타트 30~60초)이 있어, 심사위원이 아무 때나 눌러도
**즉시 응답**하도록 외부에서 10분마다 깨워두면 됩니다(비용 $0).

### 무료 업타임 핑 설정
1. 배포로 발급된 주소 확보: `https://hwaseong-on.onrender.com`
2. **cron-job.org** 또는 **UptimeRobot** (둘 다 무료) 가입
3. 모니터/크론잡 추가
   - URL: `https://hwaseong-on.onrender.com/api/health`
   - 주기: **10분** (휴면 15분보다 짧게)
   - 방식: GET, 성공조건 200/JSON `"ok": true`
4. 저장 → 한 달 내내 따뜻하게 유지(항상 즉시 응답).

> 한도: Render 무료는 계정당 약 750 인스턴스시간/월. **단일 서비스 24시간 ≈ 730시간**으로 한도 내.
> 다른 무료 서비스를 함께 돌리면 한도를 넘을 수 있으니 이 서비스만 상시 유지 권장.

### 콜드스타트 0을 보장하려면(선택)
- **Render Starter(월 $7)**: 휴면 없이 항상 상시. 한 달 심사면 가장 깔끔.
- 또는 Railway(무료 크레딧)·Fly.io 상시 인스턴스.

| 방식 | 한 달 유지 | 비용 | 콜드스타트 | PC 켜둠 |
|---|---|---|---|---|
| Render 무료 + 핑 | ✅ | $0 | 핑으로 예방 | 불필요 |
| Render Starter | ✅ | $7/월 | 없음 | 불필요 |
| 로컬 PC + 터널 | △ | $0 | - | 한 달 내내 필요(비권장) |

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
