# 화성ON 로컬/사내망(LAN) 서버 실행
# 같은 Wi-Fi/네트워크의 다른 컴퓨터·휴대폰에서 http://<이 PC IP>:5200 으로 접속 가능.
# 사용:  PowerShell에서  ./scripts/serve.ps1   (또는 우클릭 → PowerShell로 실행)

$ErrorActionPreference = "Stop"
$port = 5200
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# 1) 방화벽 인바운드 규칙(최초 1회, 관리자 권한 필요). 실패해도 계속 진행.
$ruleName = "HwaseongON-$port"
if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
  try {
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow `
      -Protocol TCP -LocalPort $port -Profile Any -ErrorAction Stop | Out-Null
    Write-Host "[방화벽] 포트 $port 인바운드 허용 규칙 추가됨" -ForegroundColor Green
  } catch {
    Write-Host "[방화벽] 규칙 추가 실패(관리자 권한 필요). LAN 접속이 안 되면 관리자 PowerShell에서 다시 실행하세요." -ForegroundColor Yellow
  }
}

# 2) 접속 주소 안내
$ips = (Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } |
  Select-Object -ExpandProperty IPAddress)
Write-Host ""
Write-Host "================ 화성ON 서버 ================" -ForegroundColor Cyan
Write-Host " 이 PC:        http://localhost:$port"
foreach ($ip in $ips) { Write-Host " 같은 네트워크: http://${ip}:$port" }
Write-Host " 외부(인터넷) 공개는  ./scripts/tunnel.ps1  를 함께 실행" -ForegroundColor DarkGray
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 3) 서버 기동 (0.0.0.0 → 외부 접속 허용)
python -m uvicorn backend.app:app --host 0.0.0.0 --port $port
