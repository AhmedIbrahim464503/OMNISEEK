import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from api.router import api_router
from core.config import settings
from core.db import init_db
from core.logging import setup_logging, logger, request_context
from api.metrics import metrics_collector

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing OWASP-standard HTTP security headers on all responses."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self' http://localhost:8000 http://localhost:3000"
        )
        # Apply HSTS in production (secured by HTTPS)
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

class TelemetryAndTracingMiddleware(BaseHTTPMiddleware):
    """Middleware generating Request and Trace IDs, injecting context loggers, and collecting metrics."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        
        # Parse or generate request and trace IDs
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        
        # Update thread-safe logging context var
        token = request_context.set({
            "request_id": request_id,
            "trace_id": trace_id
        })
        
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            duration = time.perf_counter() - start_time
            metrics_collector.record_request(request.method, request.url.path, 500, duration)
            raise exc
        finally:
            duration = time.perf_counter() - start_time
            # Reset logging context
            request_context.reset(token)

        # Exclude metrics route from logging and metrics counting to prevent clutter
        if request.url.path != "/metrics":
            metrics_collector.record_request(
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration=duration
            )
            
        # Append tracing headers to the response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager handling application setup and teardown."""
    setup_logging()
    logger.info("Initializing OMNISEEK application lifecycle startup...")
    
    # Execute database initializations (enabling extensions)
    await init_db()
    
    yield
    
    logger.info("Tearing down OMNISEEK application lifecycle shutdown...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Apply middlewares
app.add_middleware(TelemetryAndTracingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Configure Cross-Origin Resource Sharing (CORS) middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include primary API router
app.include_router(api_router)
