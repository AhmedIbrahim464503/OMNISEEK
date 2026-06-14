# Security Hardening Specification

This document details the security controls, validation strategies, and API hardening policies implemented in OmniSeek.

---

## 1. Network & API Security Middleware

### A. HTTP Security Headers
FastAPI intercepts all response streams and appends headers to prevent clickjacking, scripting injections, and MIME-sniffing:

*   `X-Frame-Options`: Enforced as `DENY` to prevent UI redressing inside iframe wraps.
*   `X-Content-Type-Options`: Set to `nosniff` to force browsers to follow headers.
*   `X-XSS-Protection`: Configured with block mode `1; mode=block`.
*   `Content-Security-Policy`: Restricts content loading to self and trusted endpoints:
    ```
    default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' http://localhost:8000
    ```
*   `Strict-Transport-Security` (HSTS): Enabled in non-debug mode to force HTTPS connections (`max-age=31536000; includeSubDomains`).

### B. CORS Restrictions
Configured via `CORSMiddleware` using variables from `.env`. Restricts connections exclusively to registered clients (defaulting to port `3000` for frontend and `8000` for backend API routing).

---

## 2. API Rate Limiting

Rate limiting is enforced at the route level using a **Redis-backed fixed-window counter** dependency (`api/rate_limiter.py`):

*   **Ingestion Uploads**: Limit of `10` operations/minute per client IP. Prevents disk space exhaustion.
*   **Search Console Queries**: Limit of `100` searches/minute per client IP. Prevents model server exhaustion.
*   **Analytics Summaries**: Limit of `60` dashboard loads/minute per client IP.
*   *Fallback Strategy*: If Redis connectivity fails, the rate limiter logs warnings and falls back to passing requests safely.

---

## 3. Upload & File Security

Ingested streams are verified prior to writing to the isolated `/storage/` directories:

### A. Format and Extension Validation
Only files matching whitelisted properties are accepted:
*   **Allowed Extensions**: `.txt`, `.pdf`, `.mp3`, `.wav`, `.mp4`, `.mov`.
*   **Allowed Mimetypes**: `text/plain`, `application/pdf`, `audio/mpeg`, `audio/mp3`, `audio/wav`, `audio/x-wav`, `video/mp4`, `video/quicktime`.
*   Rejects executable, binary scripting formats, and double extension profiles (e.g. `exploit.pdf.exe`).

### B. File Sizing Limits
Maximum file size is restricted to `50MB`. Requests exceeding this trigger `413 Request Entity Too Large`.

### C. Path Traversal Prevention
Filenames are processed using `os.path.basename` to extract pure basenames:
```python
safe_filename = os.path.basename(file.filename)
```
This prevents folder traversal attempts (e.g., uploading files as `../../../../etc/passwd`).

### D. Security Scan Integration
An architecture-ready scanner integration point (`scan_file_for_virus`) is placed in the pipeline:
```python
async def scan_file_for_virus(file: UploadFile) -> bool:
    # Integration stub: Hook ClamAV daemon checks here
    return True
```
This hooks check validations before saving files to disk.
