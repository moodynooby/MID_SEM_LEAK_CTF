# =================================================================
# Windows PowerShell Shutdown Script for CTFd
# IEEE AUSB: Case File: The Mid-Sem Leak
# =================================================================

Write-Host "[*] Stopping CTFd containers..." -ForegroundColor Yellow
if (Get-Command "docker" -ErrorAction SilentlyContinue) {
    docker compose down
} elseif (Get-Command "docker-compose" -ErrorAction SilentlyContinue) {
    docker-compose down
}
Write-Host "[+] Containers stopped successfully." -ForegroundColor Green
