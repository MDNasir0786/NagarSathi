"""Logging setup and request-scoped middleware (request id + timing)."""

from __future__ import annotations

import logging
import sys
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.config import settings

logger = logging.getLogger("app.request")

REQUEST_ID_HEADER = "X-Request-ID"


def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)
    # Replace handlers so repeated calls (e.g. reload) don't duplicate output.
    for handler in list(root.handlers):
        root.removeHandler(handler)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    root.addHandler(handler)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assign a request id, log the outcome and expose timing to clients."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex[:16]
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000
        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers["X-Response-Time-ms"] = f"{duration_ms:.1f}"
        logger.info(
            "%s %s -> %s (%.1fms) rid=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Small in-process sliding-window limiter.

    Enough to blunt accidental floods from a single client during development.
    In production put a real limiter (API gateway / Redis) in front of this;
    an in-memory counter cannot coordinate across worker processes.
    """

    def __init__(self, app: FastAPI) -> None:
        super().__init__(app)
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        ip = forwarded.split(",")[0].strip() if forwarded else (
            request.client.host if request.client else "unknown"
        )
        # Separate bucket for the expensive AI routes.
        bucket = "ai" if "/ai/" in request.url.path else "default"
        return f"{bucket}:{ip}"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not settings.rate_limit_enabled or request.method == "OPTIONS":
            return await call_next(request)
        if request.url.path in {"/health", "/ready", "/metrics"}:
            return await call_next(request)

        key = self._client_key(request)
        limit = (
            settings.ai_rate_limit_requests
            if key.startswith("ai:")
            else settings.rate_limit_requests
        )
        window = settings.rate_limit_window_seconds
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > window:
            hits.popleft()

        if len(hits) >= limit:
            from fastapi.responses import JSONResponse

            retry_after = max(1, int(window - (now - hits[0])))
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "rate_limited",
                        "message": "Too many requests. Please slow down.",
                    }
                },
                headers={"Retry-After": str(retry_after)},
            )

        hits.append(now)
        return await call_next(request)
