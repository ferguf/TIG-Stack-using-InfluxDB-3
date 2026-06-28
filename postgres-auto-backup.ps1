# Define Paths
$backupDir = "$PSScriptRoot\psql\backup"
$date = Get-Date -Format "yyyy-MM-dd_HHmm"
$filename = "$backupDir\backup_$date.sql"

# 1. Ensure the backup directory exists
if (!(Test-Path $backupDir)) { 
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null 
    Write-Host "Created directory: $backupDir" -ForegroundColor Cyan
}

# 2. Execute pg_dump
# --clean ensures existing views/tables are dropped during a restore
# --if-exists prevents errors during the drop phase
Write-Host "Backing up 'mydatabase' to $filename..." -ForegroundColor Yellow

docker exec db pg_dump -U myuser --clean --if-exists -d mydatabase | Out-File -FilePath $filename -Encoding utf8

if ($LASTEXITCODE -eq 0) {
    Write-Host "Backup successfully saved to $filename" -ForegroundColor Green
} else {
    Write-Host "Backup FAILED with exit code $LASTEXITCODE" -ForegroundColor Red
}
