# Disaster Recovery & Backups

This guide details the backup, restore, and disaster recovery strategies for OmniSeek databases.

---

## 1. Backup Utilities

Database snapshots are captured using the custom PowerShell utility script `scripts/backup.ps1`:

*   **Process**:
    *   Triggers `pg_dump` inside the active database container to generate a compressed custom-format backup.
    *   Copies the file to the host backups folder: `backups/omniseek_backup_YYYYMMDD_HHMMSS.dump`.
    *   Removes temporary backup files from the container.

---

## 2. Restore Procedures

Database restore operations are executed using the custom PowerShell utility script `scripts/restore.ps1`:

*   **Execution Command**:
    ```powershell
    .\scripts\restore.ps1 -BackupFilePath .\backups\omniseek_backup_20260614_085358.dump
    ```
*   **Process**:
    *   Copies the target backup file into the postgres container.
    *   Executes `pg_restore` with `-c` (clean) and `--if-exists` flags, dropping existing schema elements before rebuilding the database.
    *   Cleans up temporary files from the container.

---

## 3. Disaster Recovery Scheduling Recommendations

To ensure business continuity, implement the following scheduling strategies:

*   **Frequent Snapshots**: Run automated backups daily during low-traffic periods.
*   **Offsite Replication**: Configure cron tasks to sync backups to secure cloud storage (such as AWS S3 or GCP Cloud Storage) with a 30-day retention policy.
*   **Recovery Testing**: Periodically restore database backups in testing environments to verify snapshot integrity.
