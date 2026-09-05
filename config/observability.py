import json
import os
import time
import uuid
from datetime import datetime, timezone


class ObservabilityMiddleware:
    """Attach request/correlation IDs and emit one structured JSON access log."""

    def __init__(self, app):
        self.app = app
        self.service = os.getenv("SERVICE_CODE", "auth")
        self.environment = os.getenv("ENVIRONMENT", "development")

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        request_id = headers.get("x-request-id") or str(uuid.uuid4())
        correlation_id = headers.get("x-correlation-id") or request_id
        scope.setdefault("state", {})["request_id"] = request_id
        scope["state"]["correlation_id"] = correlation_id
        started = time.perf_counter()
        status_code = 500

        async def send_with_context(message):
            nonlocal status_code
            if message.get("type") == "http.response.start":
                status_code = int(message.get("status", 500))
                response_headers = list(message.get("headers", []))
                names = {key.lower() for key, _ in response_headers}
                if b"x-request-id" not in names:
                    response_headers.append((b"x-request-id", request_id.encode("latin-1")))
                if b"x-correlation-id" not in names:
                    response_headers.append((b"x-correlation-id", correlation_id.encode("latin-1")))
                message["headers"] = response_headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_context)
        except Exception as exc:
            self._emit(scope, request_id, correlation_id, 500, started, type(exc).__name__)
            raise
        else:
            self._emit(scope, request_id, correlation_id, status_code, started, None)

    def _emit(self, scope, request_id, correlation_id, status_code, started, error_type):
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "http_request",
            "service": self.service,
            "environment": self.environment,
            "request_id": request_id,
            "correlation_id": correlation_id,
            "method": scope.get("method"),
            "path": scope.get("path"),
            "status_code": status_code,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        }
        if error_type:
            event["error_type"] = error_type
        print(json.dumps(event, separators=(",", ":"), ensure_ascii=False), flush=True)
