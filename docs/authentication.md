# Authentication & Authorization

This document details the JWT identity authentication flow, password encryption methods, and role permissions used in OmniSeek.

---

## 1. Credentials Cryptography

Password credentials are encrypted using **PBKDF2-HMAC-SHA256** with a cryptographically secure 16-byte random salt and 100,000 iterations:

*   **Encryption**:
    ```python
    salt = os.urandom(16)
    db_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    password_hash = f"{salt.hex()}:{db_hash.hex()}"
    ```
*   **Verification**: The salt is extracted from the database string, password inputs are rehashed with the same parameters, and compared using `hmac.compare_digest` to prevent timing attacks.

---

## 2. JWT Access Token Flow

Identity tokens are generated using a custom, pure Python implementation of **HMAC-SHA256 JWT** signatures, eliminating external dependencies:

*   **Header Format**:
    ```json
    {"alg": "HS256", "typ": "JWT"}
    ```
*   **Payload Claims**:
    *   `sub`: User account identification (username).
    *   `role`: Authorization permissions role (`USER` or `ADMIN`).
    *   `exp`: Token expiration timestamp (defaulting to 24 hours).
*   **Signature**: Calculated by signing the header and payload base64url strings with the HMAC-SHA256 algorithm using the `JWT_SECRET` key.

---

## 3. Role-Based Permissions (RBAC)

FastAPI endpoints enforce access control rules through dependencies:

| Endpoint | Method | Required Role | Required Permission |
| :--- | :--- | :--- | :--- |
| `/api/auth/register` | `POST` | Public | Create new account |
| `/api/auth/login` | `POST` | Public | Retrieve JWT token |
| `/api/upload` | `POST` | `USER`, `ADMIN` | Ingest media and files |
| `/api/search` | `GET` | `USER`, `ADMIN` | Execute semantic searches |
| `/api/search/dashboard`| `GET` | `ADMIN` | Read system quality telemetry |
| `/api/search/benchmark`| `POST` | `ADMIN` | Trigger database quality benchmarks |
| `/health/live` | `GET` | Public | Live probe |
| `/health/ready` | `GET` | Public | Readiness database check |
| `/health/deep` | `GET` | Public | Component deep checks |
| `/metrics` | `GET` | Public | Prometheus metrics scrape |
