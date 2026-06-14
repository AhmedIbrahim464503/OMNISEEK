# Production Operations & Runbook

This guide documents the operational procedures, health checks, log rotations, and monitoring practices for running OmniSeek in production.

---

## 1. System Health Checks

OmniSeek exposes dedicated health check endpoints for load balancers and monitoring tools:

*   **Liveness Probe** (`/health/live`): Confirms the web process is running.
*   **Readiness Probe** (`/health/ready`): Confirms database connectivity.
*   **Deep Probe** (`/health/deep`): Performs checks on all components:
    *   Database (ping)
    *   Redis (ping)
    *   Celery (inspect stats)
    *   Storage path write permissions
    *   Model manager status

---

## 2. Logs Retention & Rotation

JSON logs are routed to `stdout` within Docker containers. To prevent disk space exhaustion:

*   **Docker Log Limits**: Configure max-size and max-file parameters in `/etc/docker/daemon.json`:
    ```json
    {
      "log-driver": "json-file",
      "log-opts": {
        "max-size": "100m",
        "max-file": "3"
      }
    }
    ```

---

## 3. Celery Worker Graceful Shutdown

To prevent task corruption when terminating workers:

*   **Shutdown Signal**: Send `SIGTERM` to the Celery worker process.
*   **Behavior**: Celery will stop accepting new tasks and complete active runs before shutting down.
*   **Celery Configs**: `soft_time_limit` and `time_limit` parameters automatically catch hanging tasks.
