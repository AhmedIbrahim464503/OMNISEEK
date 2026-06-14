# OmniSeek PostgreSQL Automated Backup Utility
# PowerShell script for database snapshots dump inside pgvector container

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $PSScriptRoot "..\" "backups"
$backupFile = "omniseek_backup_$timestamp.dump"
$containerBackupPath = "/var/lib/postgresql/data/omniseek_backup.dump"

if (!(Test-Path $backupDir)) {
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
}

$localBackupPath = Join-Path $backupDir $backupFile

Write-Host "Starting PostgreSQL backup for OmniSeek database..." -ForegroundColor Cyan

# 1. Execute pg_dump inside the docker container
Write-Host "Triggering pg_dump inside container 'omniseek-db'..." -ForegroundColor Yellow
docker exec -t omniseek-db pg_dump -U postgres -d omniseek -F c -b -v -f $containerBackupPath

if ($LASTEXITCODE -ne 0) {
    Write-Error "Database dump execution failed. Ensure docker container is active."
    exit 1
}

# 2. Copy the backup file from container volume to host backups folder
Write-Host "Copying dump file to host path: $localBackupPath" -ForegroundColor Yellow
docker cp "omniseek-db:$containerBackupPath" $localBackupPath

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to copy dump file from container to host."
    exit 1
}

# 3. Clean temporary container dump
Write-Host "Cleaning temporary file inside container..." -ForegroundColor Yellow
docker exec -t omniseek-db rm $containerBackupPath

Write-Host "PostgreSQL backup completed successfully!" -ForegroundColor Green
Write-Host "Snapshot location: $localBackupPath" -ForegroundColor Green
