# API Reference

This document catalogs the endpoint routing details and query payloads supported by the OMNISEEK web application.

---

## 1. Health Diagnostics

### `GET /health`
Validates backend responsiveness.
*   **Request Headers**: None
*   **Response Headers**: `Content-Type: application/json`
*   **Success Response** (200 OK):
    ```json
    {
      "status": "ok",
      "service": "omniseek-backend"
    }
    ```

---

## 2. Ingestion Routes

### `POST /api/upload` (also aliased under `/api/v1/upload`)
Ingests raw document, audio, or video files synchronously, parses their structure, and populates database chunks.
*   **Request Content Type**: `multipart/form-data`
*   **Request Form Fields**:
    *   `file` (Binary File Stream, Mandatory): Supported file types are `.txt`, `.pdf`, `.mp3`, `.wav`, `.mp4`, `.mov`.
*   **Success Response** (200 OK):
    ```json
    {
      "asset_id": "9df760d6-ff7d-4b8c-8f4b-1481b7dc5b4b",
      "status": "processed",
      "chunks_created": 12
    }
    ```
*   **Error Responses**:
    *   **400 Bad Request** (`ValidationError`):
        ```json
        {
          "detail": "File format '.png' is unsupported. Supported types: ['.txt', '.pdf', '.mp3', '.wav', '.mp4', '.mov']"
        }
        ```
    *   **500 Internal Server Error** (`DatabaseError` / `Exception`):
        ```json
        {
          "detail": "Failed to write file stream to storage: [Errno 28] No space left on device"
        }
        ```
