# 화성ON 인터넷 공개(외부 컴퓨터 접속용) — Cloudflare Quick Tunnel
# 계정·도메인 불필요. 실행하면 https://<무작위>.trycloudflare.com 공개 URL이 생성됨.
# 심사위원·외부 사용자에게 이 URL만 알려주면 어디서나 접속 가능.
#
# 사용 순서:
#   1) 새 PowerShell 창에서  ./scripts/serve.ps1   (서버 먼저 기동, 5200 포트)
#   2) 또 다른 PowerShell 창에서  ./scripts/tunnel.ps1
#   3) 출력되는  https://....trycloudflare.com  주소를 공유
#
# 주의: 무료 Quick Tunnel은 임시 주소이며 창을 닫으면 사라집니다.
#       장기 고정 주소가 필요하면 Cloudflare 계정 + Named Tunnel 사용.

$ErrorActionPreference = "Stop"
$port = 5200
$root = Split-Path -Parent $PSScriptRoot
$cf   = Join-Path $root "bin\cloudflared.exe"

if (-not (Test-Path $cf)) {
  Write-Host "[다운로드] cloudflared.exe 내려받는 중..." -ForegroundColor Yellow
  New-Item -ItemType Directory -Force (Split-Path $cf) | Out-Null
  Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" `
    -OutFile $cf
}

# 서버가 떠 있는지 가볍게 확인
try {
  Invoke-WebRequest -Uri "http://localhost:$port/api/health" -TimeoutSec 3 -UseBasicParsing | Out-Null
} catch {
  Write-Host "[주의] localhost:$port 서버 응답이 없습니다. 먼저 ./scripts/serve.ps1 로 서버를 켜세요." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================ 인터넷 공개 터널 ================" -ForegroundColor Cyan
Write-Host " 잠시 후 아래에 https://....trycloudflare.com 주소가 나타납니다." -ForegroundColor Cyan
Write-Host " 그 주소를 외부 사용자에게 공유하세요. (Ctrl+C 로 종료)" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

& $cf tunnel --url "http://localhost:$port"
