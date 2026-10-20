# =================================================================
# Windows PowerShell Backup Script for CTFd
# IEEE AUSB: Case File: The Mid-Sem Leak
# =================================================================

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "backups"
$tempDir = "$backupDir\temp_$timestamp"

if (-not (Test-Path $backupDir)) { New-Item -ItemType Directory -Path $backupDir | Out-Null }
New-Item -ItemType Directory -Path $tempDir | Out-Null

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [IEEE AUSB CTF] Creating Backup on Windows: $timestamp" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Dump MariaDB
Write-Host "[*] Exporting MariaDB database..." -ForegroundColor White
docker exec ctfd_db mariadb-dump -u ctfd -pctfd_secure_pass --single-transaction --quick ctfd > "$tempDir\database.sql"

# 2. Copy Uploads
Write-Host "[*] Copying challenge uploads..." -ForegroundColor White
docker cp ctfd_app:/var/uploads "$tempDir\uploads"

# 3. Zip archive
$zipPath = "$backupDir\ctfd_backup_$timestamp.zip"
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -Force
Remove-Item -Recurse -Force $tempDir

Write-Host "[+] Backup saved to: $zipPath" -ForegroundColor Green
