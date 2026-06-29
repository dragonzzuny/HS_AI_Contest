# 화성ON 고정 커스텀 도메인 — Cloudflare Named Tunnel 실행기
# 본인 소유 도메인을 Cloudflare에 연결한 뒤, 아래 "최초 1회 설정"을 마치면
# 이 스크립트로 https://<원하는도메인> 에 항상 같은 주소로 접속할 수 있습니다.
#
# ── 최초 1회 설정(터미널에서 직접) ─────────────────────────────
#   bin\cloudflared.exe tunnel login                         # 브라우저에서 내 도메인 선택·인증
#   bin\cloudflared.exe tunnel create hwaseong-on            # 터널 생성(자격증명 json 발급)
#   bin\cloudflared.exe tunnel route dns hwaseong-on hwaseong-on.<내도메인>   # DNS 연결
#   → 위 명령이 만든 터널 UUID를 아래 $TunnelName 그대로 쓰면 됩니다.
# ───────────────────────────────────────────────────────────────
# 이후에는:  ./scripts/serve.ps1 (서버) +  ./scripts/tunnel_named.ps1 (이 스크립트)

param(
  [string]$TunnelName = "hwaseong-on",
  [int]$Port = 5200
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$cf   = Join-Path $root "bin\cloudflared.exe"

if (-not (Test-Path $cf)) { throw "bin\cloudflared.exe 없음 — ./scripts/tunnel.ps1 를 한 번 실행하면 자동 다운로드됩니다." }

# 서버 응답 확인
try { Invoke-WebRequest "http://localhost:$Port/api/health" -TimeoutSec 3 -UseBasicParsing | Out-Null }
catch { Write-Host "[주의] localhost:$Port 서버가 꺼져 있습니다. 먼저 ./scripts/serve.ps1 실행." -ForegroundColor Yellow }

Write-Host "Named Tunnel '$TunnelName' → http://localhost:$Port 연결, 고정 도메인으로 공개합니다." -ForegroundColor Cyan
& $cf tunnel run --url "http://localhost:$Port" $TunnelName
