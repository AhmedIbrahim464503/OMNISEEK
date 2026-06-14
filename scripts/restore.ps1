# OmniSeek PostgreSQL Automated Restore Utility
# PowerShell script to restore a database snapshot from pg_dump inside container

param (
    [Parameter(Mandatory=$true)]
    [string]$BackupFilePath
)

if (!(Test-Path $BackupFilePath)) {
    Write-Error "Backup file not found at path: $BackupFilePath"
    exit 1
}

$containerBackupPath = "/var/lib/postgresql/data/omniseek_restore.dump"

Write-Host "Starting PostgreSQL database restore from: $BackupFilePath" -ForegroundColor Cyan

# 1. Copy the backup file to container path
Write-Host "Copying dump file to container 'omniseek-db'..." -ForegroundColor Yellow
docker cp $BackupFilePath "omniseek-db:$containerBackupPath"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to copy dump file into container."
    exit 1
}

# 2. Run pg_restore inside container
Write-Host "Executing pg_restore inside container 'omniseek-db'..." -ForegroundColor Yellow
# -c clean database objects before recreating, --if-exists checks
docker exec -t omniseek-db pg_restore -U postgres -d omniseek -c --if-exists -v $containerBackupPath

if ($LASTEXITCODE -ne 0) {
    Write-Error "Restore execution failed."
    # Clean file inside container even on failure
    docker exec -t omniseek-db rm $containerBackupPath
    exit 1
}

# 3. Clean up container path
Write-Host "Cleaning up files inside container..." -ForegroundColor Yellow
docker exec -t omniseek-db rm $containerBackupPath

Write-Host "PostgreSQL database restore finalized successfully!" -ForegroundColor Green
