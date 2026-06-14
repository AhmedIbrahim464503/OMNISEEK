# Evaluator Walkthrough & FAQ

This guide serves as a quick reference sheet answering common questions about OmniSeek's design and implementations.

---

## 1. System Design Questions

### Q1: Why use a custom, pure Python implementation for JWT?
> A custom JWT implementation using standard libraries (`hmac`, `hashlib`, `base64`) removes external dependency risks and prevents potential package conflicts in production containers, while maintaining cryptographically secure signatures.

### Q2: How is the score linear fusion implemented?
> Cosine distance similarity values and full-text `ts_rank` values are normalized to a common `[0.0, 1.0]` range. They are then combined using a weighted linear formula (default weight `w = 0.7` for vector similarity).

---

## 2. Ingestion & Worker Questions

### Q3: Why offload embedding generation to Celery?
> File parsing and vector generation (Whisper/CLIP) are resource-intensive tasks. Offloading them to Celery ensures FastAPI request threads remain responsive.

### Q4: How are task failures handled?
> Celery tasks are configured with exponential backoff retries and soft/hard timeouts. Task states (PENDING, STARTED, RETRY, SUCCESS, FAILURE) are logged to the PostgreSQL database in real time.
