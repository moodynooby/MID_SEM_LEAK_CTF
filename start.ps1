# =================================================================
# Windows PowerShell Startup Script for CTFd
# IEEE AUSB: Case File: The Mid-Sem Leak
# =================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [IEEE AUSB] Starting CTFd Stack on Windows" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "[!] .env not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

# 2. Check for docker compose
if (Get-Command "docker" -ErrorAction SilentlyContinue) {
    docker compose up -d
} elseif (Get-Command "docker-compose" -ErrorAction SilentlyContinue) {
    docker-compose up -d
} elseif (Get-Command "podman-compose" -ErrorAction SilentlyContinue) {
    podman-compose up -d
} else {
    Write-Host "[ERROR] Docker Desktop or Compose was not found!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop on Windows and try again."
    Exit 1
}

# 3. Detect LAN IP
$lanIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch "vEthernet|Loopback" -and $_.IPAddress -notmatch "^169\." } | Select-Object -ExpandProperty IPAddress -First 1)
if (-not $lanIP) { $lanIP = "localhost" }

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " [SUCCESS] CTFd Stack is Running!" -ForegroundColor Green
Write-Host " Local Access:         http://localhost" -ForegroundColor White
Write-Host " Participant LAN URL:  http://$($lanIP)" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Green
