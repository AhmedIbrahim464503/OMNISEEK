# Deployment Guide

This document describes how to configure, build, and deploy the containerized OMNISEEK application stack.

---

## 1. System Requirements
*   Operating System: Windows 10/11, macOS, or Linux.
*   Container Engine: Docker Engine (v20.10+) and Docker Compose (v2.0+).

---

## 2. Setting Up Environment Configuration
1.  Copy the example environment configuration:
    ```bash
    cp .env.example .env
    ```
2.  Review and edit settings inside the newly created `.env` file as needed (defaults are pre-configured to connect across container networks).

---

## 3. Starting the Containers
Build and boot the database, Redis cache, FastAPI app, and Celery background task worker services:
```bash
docker-compose up --build -d
```

---

## 4. Initializing Database Tables & pgvector
Execute the database initialization utility script inside the running backend container to enable the vector extension and construct structural schemas:
```bash
docker-compose exec backend python core/init_schema.py
```
This prepares the database to accept incoming uploads.
