"""
Custom middleware for logging request details and processing time.
"""
import time
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs HTTP method, path, and processing time in milliseconds.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000  # ms

        print(
            f"{request.method} {request.url.path} - {process_time:.2f}ms"
        )
        return response